"""
Coding battles service.

Manages creation, joining, cancelling, and termination of 1v1 coding battle lobbies,
live in-battle submission routing, winner resolution, and history retrieval.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import BattleStatus, Verdict
from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.models.battle import Battle, BattleSubmission
from app.models.problem import Problem
from app.models.submission import Submission
from app.models.user import User
from app.models.rating_history import RatingHistory
from app.services.notification_service import notification_service
from app.services.submission_service import create_submission


async def create_battle(
    db: AsyncSession,
    host_id: uuid.UUID,
    problem_id: uuid.UUID,
    duration_seconds: int = 1800,
    opponent_username: str | None = None,
) -> Battle:
    """Create a pending battle lobby with a selected problem."""
    if duration_seconds <= 0:
        raise BadRequestException("Duration must be a positive number of seconds")
    if duration_seconds > 86400:
        raise BadRequestException("Duration cannot exceed 24 hours (86400 seconds)")

    p_stmt = select(Problem).where(Problem.id == problem_id)
    p_res = await db.execute(p_stmt)
    if not p_res.scalars().first():
        raise NotFoundException("Problem not found")

    active_stmt = select(Battle).where(
        and_(
            or_(Battle.host_user_id == host_id, Battle.opponent_user_id == host_id),
            or_(Battle.status == BattleStatus.PENDING, Battle.status == BattleStatus.ACTIVE),
        )
    )
    active_res = await db.execute(active_stmt)
    if active_res.scalars().first():
        raise BadRequestException("You are already hosting or participating in a battle")

    opponent = None
    if opponent_username:
        opp_stmt = select(User).where(User.username == opponent_username)
        opp_res = await db.execute(opp_stmt)
        opponent = opp_res.scalars().first()
        if not opponent:
            raise NotFoundException(f"User '{opponent_username}' not found")
        if opponent.id == host_id:
            raise BadRequestException("Cannot challenge yourself")

    battle = Battle(
        host_user_id=host_id,
        problem_id=problem_id,
        status=BattleStatus.PENDING,
        duration_seconds=duration_seconds,
    )
    db.add(battle)
    await db.commit()
    await db.refresh(battle)

    if opponent:
        host_stmt = select(User.username).where(User.id == host_id)
        host_res = await db.execute(host_stmt)
        host_username = host_res.scalar() or "Someone"

        await notification_service.create_notification(
            db=db,
            user_id=opponent.id,
            title="Battle Invitation",
            message=f"{host_username} challenged you to a coding battle!",
            notification_type="battle_invite",
            reference_id=str(battle.id),
        )

    return battle


async def join_battle(
    db: AsyncSession, battle_id: uuid.UUID, opponent_id: uuid.UUID
) -> Battle:
    """Join a pending battle lobby as the opponent, moving it to active."""
    stmt = select(Battle).where(Battle.id == battle_id)
    result = await db.execute(stmt)
    battle = result.scalars().first()
    if not battle:
        raise NotFoundException("Battle lobby not found")

    if battle.status != BattleStatus.PENDING:
        raise BadRequestException(f"Cannot join battle with status '{battle.status}'")

    if battle.host_user_id == opponent_id:
        raise BadRequestException("You cannot join your own battle lobby")

    active_stmt = select(Battle).where(
        and_(
            or_(Battle.host_user_id == opponent_id, Battle.opponent_user_id == opponent_id),
            or_(Battle.status == BattleStatus.PENDING, Battle.status == BattleStatus.ACTIVE),
        )
    )
    active_res = await db.execute(active_stmt)
    if active_res.scalars().first():
        raise BadRequestException("You are already hosting or participating in a battle")

    battle.opponent_user_id = opponent_id
    battle.status = BattleStatus.ACTIVE
    now = datetime.now(timezone.utc)
    battle.started_at = now
    battle.ended_at = now + timedelta(seconds=battle.duration_seconds)

    await db.commit()
    await db.refresh(battle)

    from app.websocket.manager import ws_manager

    await ws_manager.broadcast_to_room(
        str(battle_id),
        {
            "type": "battle_started",
            "battle_id": str(battle.id),
            "started_at": battle.started_at.isoformat(),
            "ended_at": battle.ended_at.isoformat(),
            "duration": battle.duration_seconds,
        },
    )

    return battle


async def cancel_battle(
    db: AsyncSession, battle_id: uuid.UUID, user_id: uuid.UUID
) -> Battle:
    """Cancel a pending battle lobby."""
    stmt = select(Battle).where(Battle.id == battle_id)
    result = await db.execute(stmt)
    battle = result.scalars().first()
    if not battle:
        raise NotFoundException("Battle lobby not found")

    if battle.host_user_id != user_id:
        raise ForbiddenException("Only the host can cancel the battle lobby")

    if battle.status != BattleStatus.PENDING:
        raise BadRequestException("Can only cancel pending battle lobbies")

    battle.status = BattleStatus.CANCELLED
    await db.commit()
    await db.refresh(battle)

    from app.websocket.manager import ws_manager

    await ws_manager.broadcast_to_room(
        str(battle.id),
        {
            "type": "battle_cancelled",
            "battle_id": str(battle.id),
            "reason": "host_cancelled",
        },
    )

    return battle


async def end_battle(
    db: AsyncSession, battle_id: uuid.UUID, user_id: uuid.UUID
) -> Battle:
    """Manually end a pending lobby or active battle."""
    stmt = select(Battle).where(Battle.id == battle_id)
    result = await db.execute(stmt)
    battle = result.scalars().first()
    if not battle:
        raise NotFoundException("Battle not found")

    is_host = battle.host_user_id == user_id
    is_opponent = battle.opponent_user_id == user_id
    if not is_host and not is_opponent:
        raise ForbiddenException("You are not a participant in this battle")

    if battle.status == BattleStatus.PENDING and not is_host:
        raise ForbiddenException("Only the host can end a pending battle lobby")

    if battle.status not in (BattleStatus.PENDING, BattleStatus.ACTIVE):
        raise BadRequestException(f"Cannot end battle with status '{battle.status}'")

    now = datetime.now(timezone.utc)
    if battle.status == BattleStatus.PENDING:
        battle.status = BattleStatus.CANCELLED
    else:
        battle.status = BattleStatus.FINISHED
        battle.winner_id = None
    battle.ended_at = now

    await db.commit()
    await db.refresh(battle)

    from app.websocket.manager import ws_manager

    await ws_manager.broadcast_to_room(
        str(battle.id),
        {
            "type": "battle_finished",
            "battle_id": str(battle.id),
            "winner_id": None,
            "winner_username": None,
            "ended_at": now.isoformat(),
            "reason": "manual_end",
            "status": battle.status,
        },
    )

    return battle


async def _battle_leaderboard(db: AsyncSession, battle_id: uuid.UUID) -> list[dict]:
    """Build live battle standings from linked submissions."""
    stmt = (
        select(BattleSubmission)
        .where(BattleSubmission.battle_id == battle_id)
        .order_by(BattleSubmission.created_at.asc())
    )
    result = await db.execute(stmt)
    rankings = []
    for bs in result.scalars().all():
        sub_stmt = select(Submission).where(Submission.id == bs.submission_id)
        sub_res = await db.execute(sub_stmt)
        sub = sub_res.scalars().first()
        user_stmt = select(User.username).where(User.id == bs.user_id)
        user_res = await db.execute(user_stmt)
        username = user_res.scalar() or "Unknown"
        if sub:
            rankings.append({
                "user_id": str(bs.user_id),
                "username": username,
                "verdict": sub.verdict,
                "execution_time_ms": sub.execution_time_ms,
                "submission_id": str(sub.id),
            })
    return rankings


async def submit_battle_solution(
    db: AsyncSession,
    battle_id: uuid.UUID,
    user_id: uuid.UUID,
    language: str,
    source_code: str,
) -> Submission:
    """Create a submission for a battle problem and judge synchronously."""
    stmt = select(Battle).where(Battle.id == battle_id)
    result = await db.execute(stmt)
    battle = result.scalars().first()
    if not battle:
        raise NotFoundException("Battle not found")

    if battle.status != BattleStatus.ACTIVE:
        raise BadRequestException("Submissions are only allowed during active battles")

    if user_id != battle.host_user_id and user_id != battle.opponent_user_id:
        raise ForbiddenException("You are not a participant in this battle")

    now = datetime.now(timezone.utc)
    if battle.ended_at and now > battle.ended_at:
        battle.status = BattleStatus.FINISHED
        await db.commit()
        raise BadRequestException("The battle duration has expired")

    sub = await create_submission(
        db,
        user_id=user_id,
        problem_id=battle.problem_id,
        language=language,
        source_code=source_code,
        enqueue=False,
    )

    sub_stmt = select(Submission).where(Submission.id == sub.id)
    sub_res = await db.execute(sub_stmt)
    sub = sub_res.scalars().first()
    if sub:
        await db.refresh(sub)

    battle_sub = BattleSubmission(
        battle_id=battle_id,
        user_id=user_id,
        submission_id=sub.id,
    )
    db.add(battle_sub)
    await db.commit()
    await db.refresh(battle)

    from app.websocket.manager import ws_manager

    await ws_manager.broadcast_to_room(
        str(battle_id),
        {
            "type": "submission_received",
            "user_id": str(user_id),
            "verdict": sub.verdict,
            "submission_id": str(sub.id),
        },
    )

    rankings = await _battle_leaderboard(db, battle_id)
    await ws_manager.broadcast_to_room(
        str(battle_id),
        {"type": "leaderboard_updated", "rankings": rankings},
    )

    if sub.verdict == Verdict.ACCEPTED:
        battle.status = BattleStatus.FINISHED
        battle.winner_id = user_id
        battle.ended_at = now

        stmt_winner = select(User).where(User.id == user_id).with_for_update()
        winner_res = await db.execute(stmt_winner)
        winner = winner_res.scalars().first()
        if winner:
            winner.rating += 50
            # Log rating history for winner
            db.add(RatingHistory(
                user_id=winner.id,
                battle_id=battle.id,
                rating=winner.rating,
                rating_change=50
            ))

        loser_id = (
            battle.opponent_user_id
            if user_id == battle.host_user_id
            else battle.host_user_id
        )
        if loser_id:
            stmt_loser = select(User).where(User.id == loser_id).with_for_update()
            loser_res = await db.execute(stmt_loser)
            loser = loser_res.scalars().first()
            if loser:
                loser.rating = max(0, loser.rating - 20)
                # Log rating history for loser
                db.add(RatingHistory(
                    user_id=loser.id,
                    battle_id=battle.id,
                    rating=loser.rating,
                    rating_change=-20
                ))
                await notification_service.create_notification(
                    db=db,
                    user_id=loser.id,
                    title="Battle Finished",
                    message=f"You lost the battle to {winner.username if winner else 'opponent'}.",
                    notification_type="battle_result",
                    reference_id=str(battle.id),
                )

        if winner:
            await notification_service.create_notification(
                db=db,
                user_id=winner.id,
                title="Battle Won!",
                message="Congratulations! You won the coding battle.",
                notification_type="battle_result",
                reference_id=str(battle.id),
            )

        await db.commit()

        await ws_manager.broadcast_to_room(
            str(battle_id),
            {
                "type": "battle_finished",
                "winner_id": str(user_id),
                "winner_username": winner.username if winner else None,
                "ended_at": battle.ended_at.isoformat(),
                "final_standings": rankings,
            },
        )
    else:
        await db.commit()

    return sub


async def check_and_expire_battles(db: AsyncSession) -> None:
    """Expire active battles past their end time (draw)."""
    now = datetime.now(timezone.utc)
    stmt = select(Battle).where(
        and_(Battle.status == BattleStatus.ACTIVE, Battle.ended_at <= now)
    )
    result = await db.execute(stmt)
    expired_battles = result.scalars().all()

    from app.websocket.manager import ws_manager

    for battle in expired_battles:
        battle.status = BattleStatus.FINISHED
        battle.ended_at = now
        await db.commit()

        await ws_manager.broadcast_to_room(
            str(battle.id),
            {
                "type": "battle_finished",
                "winner_id": None,
                "winner_username": None,
                "ended_at": now.isoformat(),
                "reason": "time_expired",
            },
        )


async def get_battle_details(db: AsyncSession, battle_id: uuid.UUID) -> dict:
    """Fetch complete battle details with usernames and problem details."""
    stmt = (
        select(Battle)
        .options(selectinload(Battle.problem))
        .where(Battle.id == battle_id)
    )
    result = await db.execute(stmt)
    battle = result.scalars().first()
    if not battle:
        raise NotFoundException("Battle not found")

    problem = battle.problem
    problem_title = problem.title if problem else "Unknown"
    problem_slug = problem.slug if problem else ""

    host_stmt = select(User.username).where(User.id == battle.host_user_id)
    host_res = await db.execute(host_stmt)
    host_username = host_res.scalar() or "Unknown"

    opp_username = None
    if battle.opponent_user_id:
        opp_stmt = select(User.username).where(User.id == battle.opponent_user_id)
        opp_res = await db.execute(opp_stmt)
        opp_username = opp_res.scalar()

    winner_username = None
    if battle.winner_id:
        win_stmt = select(User.username).where(User.id == battle.winner_id)
        win_res = await db.execute(win_stmt)
        winner_username = win_res.scalar()

    return {
        "id": battle.id,
        "host_user_id": battle.host_user_id,
        "host_username": host_username,
        "opponent_user_id": battle.opponent_user_id,
        "opponent_username": opp_username,
        "problem_id": battle.problem_id,
        "problem_title": problem_title,
        "problem_slug": problem_slug,
        "status": battle.status,
        "winner_id": battle.winner_id,
        "winner_username": winner_username,
        "duration_seconds": battle.duration_seconds,
        "started_at": battle.started_at,
        "ended_at": battle.ended_at,
        "created_at": battle.created_at,
    }


async def get_battle_history(
    db: AsyncSession, user_id: uuid.UUID, page: int = 1, per_page: int = 20
) -> list[dict]:
    """Retrieve paginated battle history list for a user."""
    offset = (page - 1) * per_page
    stmt = (
        select(Battle)
        .options(selectinload(Battle.problem))
        .where(or_(Battle.host_user_id == user_id, Battle.opponent_user_id == user_id))
        .order_by(Battle.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    battles = result.scalars().all()

    history = []
    for b in battles:
        problem = b.problem
        problem_title = problem.title if problem else "Unknown"
        host_stmt = select(User.username).where(User.id == b.host_user_id)
        h_res = await db.execute(host_stmt)
        h_name = h_res.scalar() or "Unknown"

        opp_name = None
        if b.opponent_user_id:
            opp_stmt = select(User.username).where(User.id == b.opponent_user_id)
            o_res = await db.execute(opp_stmt)
            opp_name = o_res.scalar()

        win_name = None
        if b.winner_id:
            win_stmt = select(User.username).where(User.id == b.winner_id)
            w_res = await db.execute(win_stmt)
            win_name = w_res.scalar()

        history.append({
            "id": b.id,
            "host_username": h_name,
            "opponent_username": opp_name,
            "problem_title": problem_title,
            "status": b.status,
            "winner_username": win_name,
            "created_at": b.created_at,
        })
    return history
