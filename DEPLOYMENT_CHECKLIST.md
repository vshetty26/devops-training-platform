# ✅ Deployment Checklist

## Frontend (Vercel) - ✅ DONE
- [x] Repository connected
- [x] Deployment successful
- [x] Live URL available
- [ ] Add VITE_API_URL environment variable (after backend is deployed)

## Backend (Render.com) - TODO

### Steps:
1. Go to https://render.com
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Select repository: vshetty26/devops-training-platform
5. Configure:
   - Name: devops-training-backend
   - Root Directory: backend
   - Environment: Docker (auto-detected)
   - Plan: Free
6. Add Environment Variables:
   ```
   SECRET_KEY=your-random-secret-here
   DATABASE_URL=/app/data/devops_arena.db
   ```
7. Click "Create Web Service"
8. Wait for deployment (5-10 minutes first time)
9. Copy backend URL: https://devops-training-backend.onrender.com

## Final Configuration

### Update Frontend Environment:
1. Go to Vercel Dashboard
2. Your Project → Settings → Environment Variables
3. Add/Update:
   ```
   VITE_API_URL = https://devops-training-backend.onrender.com
   ```
4. Redeploy frontend (Deployments → ... → Redeploy)

### Test:
1. Visit your Vercel URL
2. Try to login (demo/demo123)
3. Check if challenges load
4. Start a challenge and test terminal

## URLs:
- Frontend: https://your-project.vercel.app
- Backend: https://devops-training-backend.onrender.com
- GitHub: https://github.com/vshetty26/devops-training-platform

## ⚠️ Important Notes:
- Render free tier spins down after 15 minutes of inactivity
- First request after spin-down takes 30-60 seconds
- Docker challenges work on Render (not on Railway free tier)
