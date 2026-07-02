# CodeClash Frontend

Production React frontend for the FastAPI CodeClash backend.

## Stack

- React + TypeScript + Vite
- Tailwind CSS entry layer with custom CodeClash theme CSS
- React Router protected routes
- TanStack React Query
- Axios with JWT refresh handling
- React Hook Form + Zod
- Recharts analytics
- Monaco editor for solution authoring

## Local Development

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The backend CORS configuration allows `localhost:5173`; use that host instead of `127.0.0.1`.

The frontend defaults to:

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

Copy `.env.example` to `.env` if you need to change those values.

## Backend Routes Integrated

- Auth: register, login, refresh, logout, current user
- Users: own profile, public profile, stats, search, profile update
- Problems: list, filters, tags, detail
- Submissions: run, submit, history, by-problem history
- Analytics: dashboard, topic performance, heatmap, difficulty breakdown, weak areas
- Friends: request, accept, reject, list, compare link surface
- Battles: create lobby, detail, history, battle submit shell
- Notifications: list, unread count, mark read, mark all read
- Codeforces: link, sync, profile, contests, unlink
- Leaderboard: global top users

## Verification

```bash
npm run lint
npm run build
```

The build may warn about a large JavaScript chunk because Monaco is bundled into the main application.
