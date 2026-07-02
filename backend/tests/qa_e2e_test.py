"""
AlgoArena / CodeClash Backend — End-to-End QA Test Suite
Run: python tests/qa_e2e_test.py
Requires: httpx, websockets (API at http://localhost:8000)
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import httpx

BASE = "http://localhost:8000"
API = f"{BASE}/api/v1"
TIMEOUT = 30.0


@dataclass
class TestResult:
    module: str
    method: str
    path: str
    test_case: str
    expected: str
    actual: str
    status: str  # PASS / FAIL
    notes: str = ""


@dataclass
class QAReport:
    results: list[TestResult] = field(default_factory=list)
    perf: dict[str, float] = field(default_factory=dict)
    critical_bugs: list[str] = field(default_factory=list)
    security_issues: list[str] = field(default_factory=list)
    perf_issues: list[str] = field(default_factory=list)

    def add(self, **kwargs):
        self.results.append(TestResult(**kwargs))

    def pass_(self, module, method, path, test_case, expected, actual, notes=""):
        self.add(module=module, method=method, path=path, test_case=test_case,
                 expected=expected, actual=actual, status="PASS", notes=notes)

    def fail(self, module, method, path, test_case, expected, actual, notes=""):
        self.add(module=module, method=method, path=path, test_case=test_case,
                 expected=expected, actual=actual, status="FAIL", notes=notes)
        if "security" in notes.lower() or "unauthorized" in test_case.lower() and actual.startswith("200"):
            self.security_issues.append(f"{method} {path}: {test_case} — {notes}")
        elif notes:
            self.critical_bugs.append(f"{method} {path}: {test_case} — {notes}")


report = QAReport()
state: dict[str, Any] = {}


def auth_headers(token: str | None = None) -> dict:
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


async def req(client: httpx.AsyncClient, method: str, url: str, **kwargs) -> httpx.Response:
    t0 = time.perf_counter()
    r = await client.request(method, url, timeout=TIMEOUT, **kwargs)
    elapsed = (time.perf_counter() - t0) * 1000
    key = f"{method} {url.split('?')[0]}"
    report.perf[key] = max(report.perf.get(key, 0), elapsed)
    return r


# ---------------------------------------------------------------------------
# A. Health & Discovery
# ---------------------------------------------------------------------------
async def test_health(client: httpx.AsyncClient):
    r = await req(client, "GET", f"{BASE}/")
    if r.status_code == 200 and r.json().get("status") == "healthy":
        report.pass_("health", "GET", "/", "Health check", "200 healthy", f"{r.status_code} {r.json()}")
    else:
        report.fail("health", "GET", "/", "Health check", "200 healthy", f"{r.status_code} {r.text}")

    r2 = await req(client, "GET", f"{BASE}/openapi.json")
    if r2.status_code == 200:
        paths = r2.json().get("paths", {})
        state["openapi_paths"] = len(paths)
        report.pass_("health", "GET", "/openapi.json", "OpenAPI schema", f">=40 paths", f"{len(paths)} paths")
    else:
        report.fail("health", "GET", "/openapi.json", "OpenAPI schema", "200", str(r2.status_code))


# ---------------------------------------------------------------------------
# B. Authentication
# ---------------------------------------------------------------------------
async def test_auth(client: httpx.AsyncClient):
    mod = "auth"
    suffix = uuid.uuid4().hex[:8]
    user_a = {
        "username": f"qa_user_a_{suffix}",
        "email": f"qa_a_{suffix}@test.com",
        "password": "TestPass123!",
    }
    user_b = {
        "username": f"qa_user_b_{suffix}",
        "email": f"qa_b_{suffix}@test.com",
        "password": "TestPass456!",
    }

    # Register valid
    r = await req(client, "POST", f"{API}/auth/register", json=user_a)
    if r.status_code == 201:
        body = r.json()
        for k in ("id", "username", "email", "rating", "created_at"):
            if k not in body:
                report.fail(mod, "POST", "/auth/register", "Schema fields", f"has {k}", f"missing {k}")
                break
        else:
            report.pass_(mod, "POST", "/auth/register", "Valid registration", "201 + schema", f"201 id={body['id'][:8]}")
        state["user_a"] = user_a
        state["user_a_id"] = body["id"]
    else:
        report.fail(mod, "POST", "/auth/register", "Valid registration", "201", f"{r.status_code} {r.text[:200]}")
        return

    # Register duplicate
    r = await req(client, "POST", f"{API}/auth/register", json=user_a)
    if r.status_code == 409:
        report.pass_(mod, "POST", "/auth/register", "Duplicate username", "409", str(r.status_code))
    else:
        report.fail(mod, "POST", "/auth/register", "Duplicate username", "409", f"{r.status_code}")

    # Register invalid (short password)
    r = await req(client, "POST", f"{API}/auth/register", json={**user_b, "password": "short"})
    if r.status_code == 422:
        report.pass_(mod, "POST", "/auth/register", "Short password validation", "422", str(r.status_code))
    else:
        report.fail(mod, "POST", "/auth/register", "Short password validation", "422", f"{r.status_code}")

    # Register user B
    r = await req(client, "POST", f"{API}/auth/register", json=user_b)
    if r.status_code == 201:
        state["user_b"] = user_b
        state["user_b_id"] = r.json()["id"]
        report.pass_(mod, "POST", "/auth/register", "Second user registration", "201", "201")
    else:
        report.fail(mod, "POST", "/auth/register", "Second user registration", "201", str(r.status_code))

    # Login valid
    r = await req(client, "POST", f"{API}/auth/login", json={
        "username_or_email": user_a["username"], "password": user_a["password"]
    })
    if r.status_code == 200 and "access_token" in r.json():
        state["token_a"] = r.json()["access_token"]
        state["refresh_a"] = r.json()["refresh_token"]
        report.pass_(mod, "POST", "/auth/login", "Valid login", "200 + tokens", "200")
    else:
        report.fail(mod, "POST", "/auth/login", "Valid login", "200 + tokens", f"{r.status_code} {r.text[:200]}")
        return

    # Login invalid password
    r = await req(client, "POST", f"{API}/auth/login", json={
        "username_or_email": user_a["username"], "password": "WrongPassword!"
    })
    if r.status_code == 401:
        report.pass_(mod, "POST", "/auth/login", "Invalid password", "401", str(r.status_code))
    else:
        report.fail(mod, "POST", "/auth/login", "Invalid password", "401", f"{r.status_code}")

    # Login B
    r = await req(client, "POST", f"{API}/auth/login", json={
        "username_or_email": user_b["username"], "password": user_b["password"]
    })
    if r.status_code == 200:
        state["token_b"] = r.json()["access_token"]
        report.pass_(mod, "POST", "/auth/login", "User B login", "200", "200")
    else:
        report.fail(mod, "POST", "/auth/login", "User B login", "200", str(r.status_code))

    # /me with token
    r = await req(client, "GET", f"{API}/auth/me", headers=auth_headers(state["token_a"]))
    if r.status_code == 200 and r.json()["username"] == user_a["username"]:
        report.pass_(mod, "GET", "/auth/me", "Authenticated /me", "200 correct user", "200")
    else:
        report.fail(mod, "GET", "/auth/me", "Authenticated /me", "200", f"{r.status_code}")

    # /me without token
    r = await req(client, "GET", f"{API}/auth/me")
    if r.status_code == 401:
        report.pass_(mod, "GET", "/auth/me", "No token", "401", str(r.status_code))
    else:
        report.fail(mod, "GET", "/auth/me", "No token", "401", f"{r.status_code}", "security: missing auth not blocked")

    # Invalid token
    r = await req(client, "GET", f"{API}/auth/me", headers=auth_headers("invalid.token.here"))
    if r.status_code == 401:
        report.pass_(mod, "GET", "/auth/me", "Invalid token", "401", str(r.status_code))
    else:
        report.fail(mod, "GET", "/auth/me", "Invalid token", "401", f"{r.status_code}", "security: bad token accepted")

    # Tampered JWT (change payload)
    parts = state["token_a"].split(".")
    tampered = parts[0] + ".eyJzdWIiOiJ0YW1wZXJlZCIsInR5cGUiOiJhY2Nlc3MifQ." + parts[2]
    r = await req(client, "GET", f"{API}/auth/me", headers=auth_headers(tampered))
    if r.status_code == 401:
        report.pass_(mod, "GET", "/auth/me", "Tampered JWT", "401", str(r.status_code))
    else:
        report.fail(mod, "GET", "/auth/me", "Tampered JWT", "401", f"{r.status_code}", "security: JWT tampering not rejected")

    # Refresh token
    r = await req(client, "POST", f"{API}/auth/refresh", json={"refresh_token": state["refresh_a"]})
    if r.status_code == 200 and "access_token" in r.json():
        state["token_a"] = r.json()["access_token"]
        state["refresh_a_new"] = r.json()["refresh_token"]
        report.pass_(mod, "POST", "/auth/refresh", "Token refresh", "200 + new tokens", "200")
    else:
        report.fail(mod, "POST", "/auth/refresh", "Token refresh", "200", f"{r.status_code} {r.text[:200]}")

    # Logout
    r = await req(client, "POST", f"{API}/auth/logout", json={"access_token": state["token_a"]})
    if r.status_code == 200:
        report.pass_(mod, "POST", "/auth/logout", "Logout", "200", "200")
    else:
        report.fail(mod, "POST", "/auth/logout", "Logout", "200", str(r.status_code))

    # Re-login after logout for remaining tests
    r = await req(client, "POST", f"{API}/auth/login", json={
        "username_or_email": user_a["username"], "password": user_a["password"]
    })
    state["token_a"] = r.json()["access_token"]

    # Admin login
    r = await req(client, "POST", f"{API}/auth/login", json={
        "username_or_email": "admin", "password": "admin12345"
    })
    if r.status_code == 200:
        state["token_admin"] = r.json()["access_token"]
        report.pass_(mod, "POST", "/auth/login", "Admin login", "200", "200")
    else:
        report.fail(mod, "POST", "/auth/login", "Admin login", "200", f"{r.status_code} — admin may not exist")


# ---------------------------------------------------------------------------
# C. Problems
# ---------------------------------------------------------------------------
async def test_problems(client: httpx.AsyncClient):
    mod = "problems"

    r = await req(client, "GET", f"{API}/problems/")
    if r.status_code == 200 and "items" in r.json() and len(r.json()["items"]) > 0:
        state["problem_id"] = r.json()["items"][0]["id"]
        state["problem_slug"] = r.json()["items"][0]["slug"]
        report.pass_(mod, "GET", "/problems/", "List problems", "200 + items", f"200 count={len(r.json()['items'])}")
    else:
        report.fail(mod, "GET", "/problems/", "List problems", "200 + items", f"{r.status_code}")
        return

    r = await req(client, "GET", f"{API}/problems/?difficulty=easy")
    if r.status_code == 200 and all(p["difficulty"] == "easy" for p in r.json()["items"]):
        report.pass_(mod, "GET", "/problems/?difficulty=easy", "Filter difficulty", "all easy", "PASS")
    else:
        report.fail(mod, "GET", "/problems/?difficulty=easy", "Filter difficulty", "all easy", str(r.status_code))

    r = await req(client, "GET", f"{API}/problems/?tag=Arrays")
    if r.status_code == 200:
        report.pass_(mod, "GET", "/problems/?tag=Arrays", "Filter tag", "200", f"200 count={len(r.json()['items'])}")
    else:
        report.fail(mod, "GET", "/problems/?tag=Arrays", "Filter tag", "200", str(r.status_code))

    r = await req(client, "GET", f"{API}/problems/?search=Two")
    if r.status_code == 200 and any("Two" in p["title"] for p in r.json()["items"]):
        report.pass_(mod, "GET", "/problems/?search=Two", "Search", "match found", "PASS")
    else:
        report.fail(mod, "GET", "/problems/?search=Two", "Search", "match found", str(r.status_code))

    r = await req(client, "GET", f"{API}/problems/{state['problem_slug']}")
    if r.status_code == 200 and "description" in r.json():
        report.pass_(mod, "GET", "/problems/{slug}", "Problem detail", "200 + description", "200")
    else:
        report.fail(mod, "GET", "/problems/{slug}", "Problem detail", "200", str(r.status_code))

    r = await req(client, "GET", f"{API}/problems/nonexistent-slug-xyz")
    if r.status_code == 404:
        report.pass_(mod, "GET", "/problems/{slug}", "Invalid slug", "404", "404")
    else:
        report.fail(mod, "GET", "/problems/{slug}", "Invalid slug", "404", str(r.status_code))

    r = await req(client, "GET", f"{API}/problems/tags")
    if r.status_code == 200 and len(r.json()) > 0:
        report.pass_(mod, "GET", "/problems/tags", "List tags", "200 + tags", f"200 count={len(r.json())}")
    else:
        report.fail(mod, "GET", "/problems/tags", "List tags", "200", str(r.status_code))

    # Non-admin create problem
    r = await req(client, "POST", f"{API}/problems/", headers=auth_headers(state.get("token_a")),
                  json={"title": "QA Test", "description": "d", "input_format": "i",
                        "output_format": "o", "constraints": "c", "difficulty": "easy", "test_cases": []})
    if r.status_code == 403:
        report.pass_(mod, "POST", "/problems/", "Non-admin create blocked", "403", "403")
    else:
        report.fail(mod, "POST", "/problems/", "Non-admin create blocked", "403", f"{r.status_code}",
                    "security: non-admin can create problems" if r.status_code == 201 else "")

    # Admin create (if admin token exists)
    if state.get("token_admin"):
        r = await req(client, "POST", f"{API}/problems/", headers=auth_headers(state["token_admin"]),
                      json={"title": f"QA Admin Problem {uuid.uuid4().hex[:6]}", "description": "Test problem",
                            "input_format": "One integer n", "output_format": "One integer",
                            "constraints": "1<=n<=100", "difficulty": "easy",
                            "test_cases": [{"input": "1", "expected_output": "1", "is_sample": True}]})
        if r.status_code == 201:
            report.pass_(mod, "POST", "/problems/", "Admin create problem", "201", "201")
        else:
            report.fail(mod, "POST", "/problems/", "Admin create problem", "201", f"{r.status_code} {r.text[:200]}")


# ---------------------------------------------------------------------------
# D. Users
# ---------------------------------------------------------------------------
async def test_users(client: httpx.AsyncClient):
    mod = "users"
    if not state.get("token_a"):
        return

    r = await req(client, "GET", f"{API}/users/profile/{state['user_a']['username']}")
    if r.status_code == 200 and "username" in r.json():
        report.pass_(mod, "GET", "/users/profile/{username}", "Public profile", "200", "200")
    else:
        report.fail(mod, "GET", "/users/profile/{username}", "Public profile", "200", str(r.status_code))

    r = await req(client, "GET", f"{API}/users/profile/nonexistent_user_xyz")
    if r.status_code == 404:
        report.pass_(mod, "GET", "/users/profile/{username}", "Invalid username", "404", "404")
    else:
        report.fail(mod, "GET", "/users/profile/{username}", "Invalid username", "404", str(r.status_code))

    r = await req(client, "PUT", f"{API}/users/profile", headers=auth_headers(state["token_a"]),
                  json={"bio": "QA test bio"})
    if r.status_code == 200 and r.json().get("bio") == "QA test bio":
        report.pass_(mod, "PUT", "/users/profile", "Update profile", "200 + bio updated", "200")
    else:
        report.fail(mod, "PUT", "/users/profile", "Update profile", "200", f"{r.status_code}")

    r = await req(client, "GET", f"{API}/users/stats", headers=auth_headers(state["token_a"]))
    if r.status_code == 200 and "total_solved" in r.json():
        report.pass_(mod, "GET", "/users/stats", "Own stats", "200 + stats", "200")
    else:
        report.fail(mod, "GET", "/users/stats", "Own stats", "200", str(r.status_code))

    r = await req(client, "GET", f"{API}/users/search?q=qa_user")
    if r.status_code == 401:
        report.fail(mod, "GET", "/users/search", "Search without auth", "200 public or 401", "401 — search requires auth")
    elif r.status_code == 200:
        report.pass_(mod, "GET", "/users/search?q=qa_user", "Search users", "200", f"200 count={len(r.json())}")

    r = await req(client, "GET", f"{API}/users/stats", headers=auth_headers(state["token_a"]))
    # no token
    r2 = await req(client, "GET", f"{API}/users/stats")
    if r2.status_code == 401:
        report.pass_(mod, "GET", "/users/stats", "No auth", "401", "401")
    else:
        report.fail(mod, "GET", "/users/stats", "No auth", "401", str(r2.status_code), "security")


# ---------------------------------------------------------------------------
# E. Submissions
# ---------------------------------------------------------------------------
async def test_submissions(client: httpx.AsyncClient):
    mod = "submissions"
    if not state.get("token_a") or not state.get("problem_id"):
        return

    python_ac = """
n = int(input())
print(n)
"""
    r = await req(client, "POST", f"{API}/submissions/", headers=auth_headers(state["token_a"]),
                  json={"problem_id": state["problem_id"], "language": "python", "code": python_ac})
    if r.status_code == 201:
        body = r.json()
        state["submission_id"] = body["id"]
        for k in ("id", "verdict", "language", "problem_id"):
            if k not in body:
                report.fail(mod, "POST", "/submissions/", "Response schema", f"has {k}", "missing")
                break
        else:
            report.pass_(mod, "POST", "/submissions/", "Submit code", "201 + schema", f"201 verdict={body['verdict']}")
    else:
        report.fail(mod, "POST", "/submissions/", "Submit code", "201", f"{r.status_code} {r.text[:300]}")

    # Wait for judge
    await asyncio.sleep(3)
    r = await req(client, "GET", f"{API}/submissions/{state.get('submission_id')}",
                  headers=auth_headers(state["token_a"]))
    if r.status_code == 200:
        verdict = r.json().get("verdict")
        report.pass_(mod, "GET", "/submissions/{id}", "Poll verdict", "200", f"200 verdict={verdict}")
        if verdict == "PENDING":
            report.fail(mod, "GET", "/submissions/{id}", "Judge processed", "AC/WA/TLE/RE", "PENDING",
                        "Judge may not be running or Docker unavailable")
    else:
        report.fail(mod, "GET", "/submissions/{id}", "Get submission", "200", str(r.status_code))

    # Missing fields
    r = await req(client, "POST", f"{API}/submissions/", headers=auth_headers(state["token_a"]), json={})
    if r.status_code == 422:
        report.pass_(mod, "POST", "/submissions/", "Missing fields", "422", "422")
    else:
        report.fail(mod, "POST", "/submissions/", "Missing fields", "422", str(r.status_code))

    # Invalid language
    r = await req(client, "POST", f"{API}/submissions/", headers=auth_headers(state["token_a"]),
                  json={"problem_id": state["problem_id"], "language": "brainfuck", "code": "++."})
    if r.status_code in (201, 422, 400):
        report.pass_(mod, "POST", "/submissions/", "Invalid language", "accepted or rejected", f"{r.status_code}")
    else:
        report.fail(mod, "POST", "/submissions/", "Invalid language", "4xx", str(r.status_code))

    # Run sample
    r = await req(client, "POST", f"{API}/submissions/run", headers=auth_headers(state["token_a"]),
                  json={"problem_id": state["problem_id"], "language": "python", "code": python_ac, "input": "42"})
    if r.status_code == 200 and "stdout" in r.json():
        report.pass_(mod, "POST", "/submissions/run", "Run on sample input", "200 + stdout", f"200 stdout={r.json()['stdout'][:20]}")
    else:
        report.fail(mod, "POST", "/submissions/run", "Run on sample input", "200", f"{r.status_code} {r.text[:200]}")

    r = await req(client, "GET", f"{API}/submissions/history", headers=auth_headers(state["token_a"]))
    if r.status_code == 200 and "submissions" in r.json():
        report.pass_(mod, "GET", "/submissions/history", "History", "200 + list", f"200 total={r.json()['total']}")
    else:
        report.fail(mod, "GET", "/submissions/history", "History", "200", str(r.status_code))

    r = await req(client, "GET", f"{API}/submissions/", headers=auth_headers(state["token_a"]))
    if r.status_code == 401:
        report.pass_(mod, "POST", "/submissions/", "No auth submit", "401", "401")
    # GET without auth on history
    r = await req(client, "GET", f"{API}/submissions/history")
    if r.status_code == 401:
        report.pass_(mod, "GET", "/submissions/history", "No auth", "401", "401")
    else:
        report.fail(mod, "GET", "/submissions/history", "No auth", "401", str(r.status_code), "security")


# ---------------------------------------------------------------------------
# F. Friends
# ---------------------------------------------------------------------------
async def test_friends(client: httpx.AsyncClient):
    mod = "friends"
    if not state.get("token_a") or not state.get("token_b"):
        return

    r = await req(client, "POST", f"{API}/friends/request", headers=auth_headers(state["token_a"]),
                  json={"receiver_username": state["user_b"]["username"]})
    if r.status_code == 201:
        try:
            body = r.json()
            state["friend_request_id"] = body.get("id")
            report.pass_(mod, "POST", "/friends/request", "Send request", "201", f"201 id={body.get('id','?')[:8]}")
        except Exception as e:
            report.fail(mod, "POST", "/friends/request", "Send request schema", "201 valid JSON", f"parse error: {e}",
                        "FriendRequestResponse may not match ORM return (missing sender_username)")
    elif r.status_code == 500:
        report.fail(mod, "POST", "/friends/request", "Send request", "201", "500",
                    "CRITICAL: ResponseValidationError — FriendRequest ORM returned without enriched fields")
    else:
        report.fail(mod, "POST", "/friends/request", "Send request", "201", f"{r.status_code} {r.text[:300]}")

    # Duplicate request
    r = await req(client, "POST", f"{API}/friends/request", headers=auth_headers(state["token_a"]),
                  json={"receiver_username": state["user_b"]["username"]})
    if r.status_code == 409:
        report.pass_(mod, "POST", "/friends/request", "Duplicate request", "409", "409")
    else:
        report.fail(mod, "POST", "/friends/request", "Duplicate request", "409", f"{r.status_code}")

    # Self request
    r = await req(client, "POST", f"{API}/friends/request", headers=auth_headers(state["token_a"]),
                  json={"receiver_username": state["user_a"]["username"]})
    if r.status_code == 400:
        report.pass_(mod, "POST", "/friends/request", "Self request blocked", "400", "400")
    else:
        report.fail(mod, "POST", "/friends/request", "Self request blocked", "400", str(r.status_code))

    # List pending (user B)
    r = await req(client, "GET", f"{API}/friends/requests", headers=auth_headers(state["token_b"]))
    if r.status_code == 200:
        reqs = r.json()
        if reqs and not state.get("friend_request_id"):
            state["friend_request_id"] = reqs[0]["id"]
        report.pass_(mod, "GET", "/friends/requests", "List pending", "200", f"200 count={len(reqs)}")
    else:
        report.fail(mod, "GET", "/friends/requests", "List pending", "200", str(r.status_code))

    # Accept
    if state.get("friend_request_id"):
        r = await req(client, "POST", f"{API}/friends/accept/{state['friend_request_id']}",
                      headers=auth_headers(state["token_b"]))
        if r.status_code == 200:
            report.pass_(mod, "POST", "/friends/accept/{id}", "Accept request", "200", "200")
        else:
            report.fail(mod, "POST", "/friends/accept/{id}", "Accept request", "200", f"{r.status_code} {r.text[:200]}")

    r = await req(client, "GET", f"{API}/friends/", headers=auth_headers(state["token_a"]))
    if r.status_code == 200 and len(r.json()) >= 1:
        state["friend_id"] = r.json()[0]["friend_id"]
        report.pass_(mod, "GET", "/friends/", "Friend list", "200 + friends", f"200 count={len(r.json())}")
    else:
        report.fail(mod, "GET", "/friends/", "Friend list", "200 + >=1", f"{r.status_code} {r.text[:200]}")

    if state.get("friend_id"):
        r = await req(client, "GET", f"{API}/friends/compare/{state['friend_id']}",
                      headers=auth_headers(state["token_a"]))
        if r.status_code == 200 and "user_stats" in r.json():
            report.pass_(mod, "GET", "/friends/compare/{id}", "Compare stats", "200", "200")
        else:
            report.fail(mod, "GET", "/friends/compare/{id}", "Compare stats", "200", str(r.status_code))


# ---------------------------------------------------------------------------
# G. Battles
# ---------------------------------------------------------------------------
async def test_battles(client: httpx.AsyncClient):
    mod = "battles"
    if not state.get("token_a") or not state.get("problem_id"):
        return

    r = await req(client, "POST", f"{API}/battles/", headers=auth_headers(state["token_a"]),
                  json={"problem_id": state["problem_id"], "duration_seconds": 600,
                        "opponent_username": state.get("user_b", {}).get("username")})
    if r.status_code == 201:
        state["battle_id"] = r.json()["id"]
        report.pass_(mod, "POST", "/battles/", "Create battle", "201", f"201 id={state['battle_id'][:8]}")
    else:
        report.fail(mod, "POST", "/battles/", "Create battle", "201", f"{r.status_code} {r.text[:300]}")
        return

    r = await req(client, "GET", f"{API}/battles/{uuid.uuid4()}", headers=auth_headers(state["token_a"]))
    if r.status_code == 404:
        report.pass_(mod, "GET", "/battles/{id}", "Invalid battle ID", "404", "404")
    else:
        report.fail(mod, "GET", "/battles/{id}", "Invalid battle ID", "404", str(r.status_code))

    # Join as user B
    if state.get("token_b"):
        r = await req(client, "POST", f"{API}/battles/{state['battle_id']}/join",
                      headers=auth_headers(state["token_b"]))
        if r.status_code == 200 and r.json().get("status") == "active":
            report.pass_(mod, "POST", "/battles/{id}/join", "Join battle", "200 active", "200")
        else:
            report.fail(mod, "POST", "/battles/{id}/join", "Join battle", "200 active", f"{r.status_code} {r.text[:200]}")

    r = await req(client, "GET", f"{API}/battles/history", headers=auth_headers(state["token_a"]))
    if r.status_code == 200:
        report.pass_(mod, "GET", "/battles/history", "Battle history", "200", f"200 count={len(r.json())}")
    else:
        report.fail(mod, "GET", "/battles/history", "Battle history", "200", str(r.status_code))

    # Unauthorized battle access (no token)
    r = await req(client, "GET", f"{API}/battles/{state['battle_id']}")
    if r.status_code == 401:
        report.pass_(mod, "GET", "/battles/{id}", "No auth", "401", "401")
    else:
        report.fail(mod, "GET", "/battles/{id}", "No auth", "401", str(r.status_code), "security")

    # WebSocket test
    try:
        import websockets
        ws_url = f"ws://localhost:8000/ws/battle/{state['battle_id']}?token={state['token_a']}"
        async with websockets.connect(ws_url, open_timeout=5) as ws:
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
            if msg.get("type") == "connected":
                report.pass_(mod, "WS", "/ws/battle/{id}", "WebSocket connect", "connected event", str(msg.get("type")))
                await ws.send(json.dumps({"type": "ping"}))
                pong = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
                if pong.get("type") == "pong":
                    report.pass_(mod, "WS", "/ws/battle/{id}", "Ping/pong", "pong", "pong")
                else:
                    report.fail(mod, "WS", "/ws/battle/{id}", "Ping/pong", "pong", str(pong))
            else:
                report.fail(mod, "WS", "/ws/battle/{id}", "WebSocket connect", "connected", str(msg))
    except Exception as e:
        report.fail(mod, "WS", "/ws/battle/{id}", "WebSocket connect", "connected", str(e))


# ---------------------------------------------------------------------------
# H. Analytics, Notifications, Codeforces, Leaderboard
# ---------------------------------------------------------------------------
async def test_analytics(client: httpx.AsyncClient):
    mod = "analytics"
    if not state.get("token_a"):
        return
    endpoints = ["/analytics/dashboard", "/analytics/topics", "/analytics/submission-heatmap",
                 "/analytics/difficulty-breakdown", "/analytics/weak-areas"]
    for ep in endpoints:
        r = await req(client, "GET", f"{API}{ep}", headers=auth_headers(state["token_a"]))
        if r.status_code == 200:
            report.pass_(mod, "GET", ep, "Authenticated access", "200", "200")
        else:
            report.fail(mod, "GET", ep, "Authenticated access", "200", f"{r.status_code} {r.text[:200]}")

    r = await req(client, "GET", f"{API}/analytics/dashboard")
    if r.status_code == 401:
        report.pass_(mod, "GET", "/analytics/dashboard", "No auth", "401", "401")
    else:
        report.fail(mod, "GET", "/analytics/dashboard", "No auth", "401", str(r.status_code), "security")


async def test_notifications(client: httpx.AsyncClient):
    mod = "notifications"
    if not state.get("token_b"):
        return
    r = await req(client, "GET", f"{API}/notifications/", headers=auth_headers(state["token_b"]))
    if r.status_code == 200:
        notifs = r.json()
        report.pass_(mod, "GET", "/notifications/", "List notifications", "200", f"200 count={len(notifs)}")
        if notifs:
            state["notification_id"] = notifs[0]["id"]
    else:
        report.fail(mod, "GET", "/notifications/", "List notifications", "200", str(r.status_code))

    r = await req(client, "GET", f"{API}/notifications/unread-count", headers=auth_headers(state["token_b"]))
    if r.status_code == 200 and "unread_count" in r.json():
        report.pass_(mod, "GET", "/notifications/unread-count", "Unread count", "200", str(r.json()))
    else:
        report.fail(mod, "GET", "/notifications/unread-count", "Unread count", "200", str(r.status_code))

    if state.get("notification_id"):
        r = await req(client, "PUT", f"{API}/notifications/{state['notification_id']}/read",
                      headers=auth_headers(state["token_b"]))
        if r.status_code == 200:
            report.pass_(mod, "PUT", "/notifications/{id}/read", "Mark read", "200", "200")
        else:
            report.fail(mod, "PUT", "/notifications/{id}/read", "Mark read", "200", str(r.status_code))

    r = await req(client, "PUT", f"{API}/notifications/read-all", headers=auth_headers(state["token_b"]))
    if r.status_code == 200:
        report.pass_(mod, "PUT", "/notifications/read-all", "Mark all read", "200", "200")
    else:
        report.fail(mod, "PUT", "/notifications/read-all", "Mark all read", "200", str(r.status_code))


async def test_codeforces(client: httpx.AsyncClient):
    mod = "codeforces"
    if not state.get("token_a"):
        return

    r = await req(client, "GET", f"{API}/codeforces/profile", headers=auth_headers(state["token_a"]))
    if r.status_code == 404:
        report.pass_(mod, "GET", "/codeforces/profile", "No linked profile", "404", "404")
    else:
        report.fail(mod, "GET", "/codeforces/profile", "No linked profile", "404", str(r.status_code))

    r = await req(client, "POST", f"{API}/codeforces/link", headers=auth_headers(state["token_a"]),
                  json={"handle": "tourist"})
    if r.status_code == 200 and r.json().get("handle"):
        report.pass_(mod, "POST", "/codeforces/link", "Valid handle link", "200", f"200 handle={r.json()['handle']}")
    else:
        report.fail(mod, "POST", "/codeforces/link", "Valid handle link", "200", f"{r.status_code} {r.text[:200]}")

    r = await req(client, "POST", f"{API}/codeforces/link", headers=auth_headers(state["token_a"]),
                  json={"handle": "this_handle_definitely_does_not_exist_xyz123"})
    if r.status_code in (400, 404):
        report.pass_(mod, "POST", "/codeforces/link", "Invalid handle", "400/404", str(r.status_code))
    else:
        report.fail(mod, "POST", "/codeforces/link", "Invalid handle", "400/404", f"{r.status_code}")

    r = await req(client, "GET", f"{API}/codeforces/contests", headers=auth_headers(state["token_a"]))
    if r.status_code == 200:
        report.pass_(mod, "GET", "/codeforces/contests", "Contest list", "200", f"200 count={len(r.json())}")
    else:
        report.fail(mod, "GET", "/codeforces/contests", "Contest list", "200", str(r.status_code))

    r = await req(client, "POST", f"{API}/codeforces/sync", headers=auth_headers(state["token_a"]))
    if r.status_code == 200:
        report.pass_(mod, "POST", "/codeforces/sync", "Sync data", "200", "200")
    else:
        report.fail(mod, "POST", "/codeforces/sync", "Sync data", "200", f"{r.status_code} {r.text[:200]}")


async def test_leaderboard(client: httpx.AsyncClient):
    mod = "leaderboard"
    r = await req(client, "GET", f"{API}/leaderboard/")
    if r.status_code == 200 and isinstance(r.json(), list):
        report.pass_(mod, "GET", "/leaderboard/", "Global leaderboard", "200 list", f"200 count={len(r.json())}")
    else:
        report.fail(mod, "GET", "/leaderboard/", "Global leaderboard", "200", str(r.status_code))


# ---------------------------------------------------------------------------
# I. Security extras
# ---------------------------------------------------------------------------
async def test_security(client: httpx.AsyncClient):
    mod = "security"

    # SQL injection in search
    r = await req(client, "GET", f"{API}/problems/?search=' OR 1=1--",
                  headers=auth_headers(state.get("token_a", "")))
    if r.status_code == 200:
        report.pass_(mod, "GET", "/problems/?search=SQLi", "SQL injection in search", "200 no crash", "200 safe")
    else:
        report.fail(mod, "GET", "/problems/?search=SQLi", "SQL injection", "200 or 400", str(r.status_code))

    r = await req(client, "GET", f"{API}/users/search?q='; DROP TABLE users;--",
                  headers=auth_headers(state.get("token_a", "")))
    if r.status_code in (200, 401):
        report.pass_(mod, "GET", "/users/search SQLi", "SQL injection in user search", "no crash", str(r.status_code))
    else:
        report.fail(mod, "GET", "/users/search SQLi", "SQL injection", "no 500", str(r.status_code))

    # Large payload
    huge = "x" * 500_000
    r = await req(client, "POST", f"{API}/submissions/", headers=auth_headers(state.get("token_a", "")),
                  json={"problem_id": state.get("problem_id", str(uuid.uuid4())), "language": "python", "code": huge})
    if r.status_code in (201, 413, 422, 401):
        report.pass_(mod, "POST", "/submissions/", "Large payload", "handled gracefully", str(r.status_code))
    elif r.status_code == 500:
        report.fail(mod, "POST", "/submissions/", "Large payload", "413/422", "500", "Server error on large payload")
    else:
        report.pass_(mod, "POST", "/submissions/", "Large payload", "handled", str(r.status_code))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def main():
    print("=" * 70)
    print("AlgoArena Backend E2E QA Test Suite")
    print("=" * 70)

    async with httpx.AsyncClient() as client:
        # connectivity check
        try:
            r = await client.get(f"{BASE}/", timeout=5)
            if r.status_code != 200:
                print(f"FATAL: API not reachable at {BASE}")
                return
        except Exception as e:
            print(f"FATAL: Cannot connect to {BASE}: {e}")
            return

        await test_health(client)
        await test_auth(client)
        await test_problems(client)
        await test_users(client)
        await test_submissions(client)
        await test_friends(client)
        await test_battles(client)
        await test_analytics(client)
        await test_notifications(client)
        await test_codeforces(client)
        await test_leaderboard(client)
        await test_security(client)

    # Performance analysis
    slow = {k: v for k, v in report.perf.items() if v > 500}
    for k, v in slow.items():
        report.perf_issues.append(f"{k}: {v:.0f}ms (>500ms SLA)")

    passed = sum(1 for r in report.results if r.status == "PASS")
    failed = sum(1 for r in report.results if r.status == "FAIL")
    total = len(report.results)
    score = round((passed / total * 10) if total else 0, 1)

    print(f"\n{'='*70}")
    print(f"RESULTS: {passed}/{total} PASS, {failed} FAIL")
    print(f"Health Score: {score}/10")
    print(f"{'='*70}\n")

    # Write JSON report
    out = {
        "summary": {"passed": passed, "failed": failed, "total": total, "score": score},
        "critical_bugs": report.critical_bugs,
        "security_issues": report.security_issues,
        "perf_issues": report.perf_issues,
        "results": [r.__dict__ for r in report.results],
        "perf_ms": report.perf,
    }
    out_path = "tests/qa_report.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Full report written to {out_path}")

    # Print failures
    if failed:
        print("\n--- FAILURES ---")
        for r in report.results:
            if r.status == "FAIL":
                print(f"  [{r.module}] {r.method} {r.path} | {r.test_case}")
                print(f"    Expected: {r.expected} | Actual: {r.actual}")
                if r.notes:
                    print(f"    Notes: {r.notes}")

    return out


if __name__ == "__main__":
    asyncio.run(main())
