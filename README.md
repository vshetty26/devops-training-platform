# 🎯 DevOps Training Platform

Interactive hands-on DevOps training platform with real-world troubleshooting challenges.

## ✨ Features

- 🐳 5 Real-World Challenges (Disk Full, Docker Restart Loop, Nginx 502, K8s CrashLoop, GitHub Actions)
- 💻 Web-Based Terminal with Docker integration
- ✅ Automated Validation
- 🏆 Leaderboard System
- 🔐 JWT Authentication

## 🚀 Quick Start

### Prerequisites
- Docker Desktop
- Node.js 20+
- Python 3.11+

### Setup

1. Clone:
```bash
git clone https://github.com/vshetty26/devops-training-platform.git
cd devops-training-platform
```

2. Build Docker images:
```bash
docker build -t devops-arena-disk-full ./challenges/disk-full
docker build -t devops-arena-docker-restart-loop ./challenges/docker-restart-loop
docker build -t devops-arena-nginx-502 ./challenges/nginx-502
docker build -t devops-arena-k8s-crashloop ./challenges/k8s-crashloop
docker build -t devops-arena-github-actions-yaml ./challenges/github-actions-yaml
```

3. Start backend:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

4. Start frontend:
```bash
cd frontend
npm install && npm run dev
```

5. Open http://localhost:5173 and login with demo/demo123

## 🛠️ Tech Stack

**Frontend:** React 18, Vite, Tailwind CSS, xterm.js
**Backend:** FastAPI, SQLAlchemy, SQLite, Docker SDK, JWT

## 📧 Contact

**Author:** Vamshi Shetty
**GitHub:** [@vshetty26](https://github.com/vshetty26)

⭐ Star this repo if you find it helpful!
