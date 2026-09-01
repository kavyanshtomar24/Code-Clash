# ⚔️ Code Clash

**Code Clash** is a real-time 1v1 competitive programming platform where developers can challenge each other, solve DSA problems, and compete in live coding battles.

The platform combines a coding environment with real-time multiplayer functionality to make DSA practice more interactive and competitive.

## 🚀 Live Demo

**Live Application:** https://code-clash-omega.vercel.app

## 📌 Features

- ⚔️ **Real-time 1v1 coding battles**
- 🧑‍💻 **Monaco Code Editor** for writing and editing code
- 🔴 **Live battle synchronization** using WebSockets
- 🏠 **Battle lobby system** for creating and joining matches
- 🧩 **DSA problem-based battles**
- ⏱️ **Competitive timed coding experience**
- 🏁 **Battle lifecycle management**
  - Pending
  - Active
  - Finished
  - Cancelled
- 🛑 **End Battle functionality**
  - Pending battles can be cancelled
  - Active battles can be ended without declaring a winner
- 📡 REST APIs for application and battle management
- 🗄️ PostgreSQL database for persistent data
- 🔄 Database migrations using Alembic
- 🌐 Production deployment with Vercel and Render

## 🛠️ Tech Stack

### Frontend
- React
- Vite
- JavaScript
- HTML5
- CSS3
- Monaco Editor

### Backend
- FastAPI
- Python
- SQLAlchemy
- Uvicorn
- WebSockets
- Alembic

### Database & Infrastructure
- PostgreSQL
- Neon
- Upstash
- Render
- Vercel

## 🏗️ Architecture

```text
                        ┌─────────────────────┐
                        │       User 1        │
                        │   React + Vite UI   │
                        └──────────┬──────────┘
                                   │
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │      FastAPI        │
                        │      Backend        │
                        └──────┬───────┬──────┘
                               │       │
                  REST APIs    │       │ WebSockets
                               │       │
                               ▼       ▼
                       ┌──────────┐  ┌──────────────┐
                       │PostgreSQL│  │ Live Battle  │
                       │  (Neon)  │  │ Synchronizer │
                       └──────────┘  └──────┬───────┘
                                            │
                                            │
                                            ▼
                                  ┌─────────────────────┐
                                  │       User 2        │
                                  │   React + Vite UI   │
                                  └─────────────────────┘
```

## 🔄 Battle Flow

```text
Create Lobby
     │
     ▼
Waiting for Opponent
     │
     ▼
Opponent Joins
     │
     ▼
Battle Starts
     │
     ▼
Players Solve Problem
     │
     ├──────────────► Player Solves First ──► Winner
     │
     └──────────────► End Battle ──────────► Finished / No Winner
```

## 📂 Project Structure

A typical structure of the project is:

```text
Code-Clash/
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
├── backend/
│   ├── app/
│   ├── alembic/
│   ├── requirements.txt
│   └── ...
│
├── README.md
└── ...
```

> The exact folder structure may vary depending on the current version of the project.

## ⚙️ Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/kavyanshtomar24/Code-Clash.git
cd Code-Clash
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will normally be available at:

```text
http://localhost:5173
```

### 3. Backend Setup

Create and activate a Python virtual environment:

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI server:

```bash
uvicorn <your_app_module>:app --reload
```

> Replace `<your_app_module>` with the actual FastAPI application module used in the repository.

## 🔐 Environment Variables

Create the required environment files for the frontend and backend.

Typical configuration may include:

```env
DATABASE_URL=your_database_url
UPSTASH_REDIS_URL=your_upstash_url
UPSTASH_REDIS_TOKEN=your_upstash_token
```

For the frontend, add any required API base URL configuration, for example:

```env
VITE_API_URL=your_backend_url
```

**Never commit secret keys, database credentials, or private environment variables to GitHub.**

## 🧠 How Code Clash Works

1. A user creates a battle lobby.
2. Another user joins the lobby.
3. Both players enter the same DSA challenge.
4. The battle becomes active.
5. Players write and submit their solutions using the Monaco editor.
6. WebSockets keep the battle state synchronized in real time.
7. The battle finishes when a player wins or the battle is manually ended.
8. The final battle state is stored in the backend/database.

## ⚡ Real-Time Communication

Code Clash uses **WebSockets** to support real-time battle functionality.

This allows the application to synchronize important battle events between connected players without repeatedly polling the server.

Examples of real-time events include:

- Player joining a battle
- Battle state changes
- Battle starting
- Battle ending
- Opponent status updates

## 🗄️ Database

The backend uses **PostgreSQL** with **SQLAlchemy** for database interaction.

**Alembic** is used to manage database schema migrations.

The database stores application data such as users, battles, lobbies, and other persistent information required by the platform.

## 🧪 Testing

Before deployment, the application should be tested for:

- Lobby creation
- Lobby joining
- Two-player battle synchronization
- Battle start/end states
- Successful and unsuccessful submissions
- Disconnect/reconnect scenarios
- Invalid battle IDs
- Expired/cancelled lobbies
- API error handling
- WebSocket connection failures

## 🌐 Deployment

The project is designed with separate frontend and backend deployments:

```text
Frontend  → Vercel
Backend   → Render
Database  → Neon PostgreSQL
```

## 🔮 Future Improvements

Some possible improvements for Code Clash include:

- 🏆 Global leaderboard and player rankings
- 👤 User profiles and battle history
- 📊 Detailed performance statistics
- 🥇 ELO/rating-based matchmaking
- 🧑‍🤝‍🧑 Team battles
- 🧩 Larger DSA problem library
- 💬 In-battle chat
- 🔔 Real-time notifications
- 🧪 Automated code execution and test-case evaluation
- 🎯 Difficulty-based matchmaking
- 🏅 Achievements and competitive badges

## 👨‍💻 Author

**Kavyansh Tomar**

B.Tech Mechanical Engineering — Delhi Technological University

- GitHub: https://github.com/kavyanshtomar24
- Code Clash Repository: https://github.com/kavyanshtomar24/Code-Clash

## ⭐ Support

If you find **Code Clash** interesting, consider giving the repository a ⭐ on GitHub.

---

<p align="center">
  Built with ⚔️ for competitive programmers.
</p>
