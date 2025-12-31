# SculpFit Deployment Guide

## Security & Privacy Setup

### Secrets Management
✅ **All secrets are environment variables** (never hardcoded)
- `GEMINI_API_KEY` - Google Gemini API key
- `CLERK_SECRET_KEY` - Clerk authentication secret
- `DB_HOST`, `DB_USER`, `DB_PASS`, `DB_NAME`, `DB_PORT` - Database credentials
- `ALLOWED_ORIGINS` - CORS allowed domains (default: localhost:8000)

### Authentication
✅ **All sensitive endpoints require Clerk authentication**
- Image analysis: `/api/analyze-image-v2` ✅ Protected
- Video analysis: `/api/analyze-video` ✅ Protected
- User plans: `/api/my-plans` ✅ Protected
- Plan editing: `/api/edit/*` ✅ Protected
- Public endpoints only: `/`, `/signin`, `/health`, `/api/available-plans`, `/api/plans/{id}`

### CORS Policy
✅ **Restricted to specific domains** (not `*`)
- Set via `ALLOWED_ORIGINS` environment variable
- For local: `http://localhost:8000`
- For production: `https://yourdomain.com,https://app.yourdomain.com`

## Deployment Steps

### 1. GitHub Setup
```bash
cd c:\Users\waqar\sculpt
git init
git add .
git commit -m "Initial commit - SculpFit deployment ready"
git branch -M main
git remote add origin https://github.com/moazanTUS/sculptfitt.git
git push -u origin main
```

### 2. Railway Deployment
1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub"
4. Connect your GitHub account and select the `sculpt` repo
5. Wait for build to complete

### 3. Environment Variables in Railway
Set in Railway dashboard under "Variables":
```
GEMINI_API_KEY=your_actual_api_key
CLERK_SECRET_KEY=your_actual_secret
DB_HOST=your_db_host
DB_PORT=3306
DB_USER=your_db_user
DB_PASS=your_db_password
DB_NAME=sculpfit
ALLOWED_ORIGINS=https://your-domain.railway.app,https://www.your-domain.com
```

### 4. Database Options
**Option A: Railway's MySQL** (easiest)
- Click "Add" → Select "MySQL"
- Railway auto-populates `DB_*` variables

**Option B: External Database**
- Manually set all `DB_*` variables above

### 5. Update Clerk
1. Go to https://dashboard.clerk.com
2. Settings → Domains
3. Add your Railway domain: `https://your-app.railway.app`
4. Update all auth redirect URLs

### 6. Update Frontend
In `backend/static/app.js`, change:
```javascript
const API_URL = "https://your-app.railway.app";
```

## File Structure
```
.env                    ← DO NOT COMMIT (secrets)
.env.example           ← Commit this (template)
.gitignore             ← Already protects .env
.dockerignore          ← Excludes non-essential files
Dockerfile             ← Multi-stage optimized
requirements.txt       ← All dependencies pinned
railway.json           ← Railway config
backend/
├── main.py           ← FastAPI app (all endpoints)
├── clerk_auth.py     ← Authentication logic
├── db.py             ← Database connection (env vars)
├── user_plans.py     ← User plan management
├── editable_plans.py ← Plan editing
└── analyzers/
    ├── user_image_analyzer.py  ← Gemini body analysis
    └── gemini_form_analyzer.py ← Gemini form analysis
static/
├── index.html        ← Frontend UI
├── app.js           ← API client
└── styles.css       ← Styling
```

## Security Checklist
- [x] No hardcoded API keys
- [x] No hardcoded database passwords
- [x] All secrets in environment variables
- [x] CORS restricted to your domains
- [x] All sensitive endpoints require auth
- [x] File uploads processed in-memory only
- [x] .env file in .gitignore
- [x] No unnecessary files in Docker image

## Testing Deployment

### Health Check
```bash
curl https://your-app.railway.app/health
# Should return: {"status": "ok"}
```

### Authentication Test
```bash
curl https://your-app.railway.app/api/available-plans
# Should return plans (no auth needed)

curl https://your-app.railway.app/api/my-plans
# Should return 401 without auth token
```

## Auto-Deployment
- Any push to GitHub main branch auto-deploys to Railway
- Check deployment status in Railway dashboard

## Support
- Railway docs: https://docs.railway.app
- Clerk docs: https://clerk.com/docs
