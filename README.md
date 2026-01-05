# SculpFit - AI-Powered Workout Analysis Platform

A full-stack web application that uses AI and computer vision to analyze workout form, generate personalized fitness plans, and track progress.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Running Locally](#running-locally)
- [Deployment](#deployment)
- [API Documentation](#api-documentation)
- [Architecture Overview](#architecture-overview)
- [Feature Documentation](#feature-documentation)
- [Security](#security)

---

## Features

### Core Features
- **AI Image Analysis**: Upload a photo to get personalized workout recommendations based on your body type
- **Video Form Analysis**: Record or upload exercise videos to get real-time form feedback with rep counting
- **Workout Plan Generation**: AI-generated custom workout plans based on your fitness level and goals
- **Plan Customization**: Edit generated plans - add/remove exercises, adjust sets/reps
- **Progress Tracking**: Log completed workouts and track statistics over time
- **Video Library**: Browse exercise videos with proper form demonstrations

### Security Features
- **Clerk Authentication**: OAuth-based user authentication with Clerk
- **Rate Limiting**: Per-user rate limits to prevent abuse (5 req/min for analysis, 30-60 req/min for other endpoints)
- **CORS Protection**: Restricted to allowed origins
- **File Upload Validation**: Validated image and video uploads

---

## Tech Stack

### Frontend
- **HTML/CSS/JavaScript** - Vanilla JS (no framework)
- **Responsive Design** - Mobile-optimized UI
- **Real-time UI Updates** - Progress indicators, auto-scroll

### Backend
- **FastAPI** - Python web framework
- **Uvicorn** - ASGI server
- **MySQL** - Database
- **MediaPipe** - Pose detection for form analysis
- **Google Gemini API** - AI for analysis and recommendations
- **PyJWT** - Token handling
- **slowapi** - Rate limiting middleware

### Deployment
- **Docker** - Containerization
- **Railway** - Cloud hosting platform

---

## Project Structure

```
sculpt/
├── backend/
│   ├── main.py                          # FastAPI app, all endpoints
│   ├── db.py                            # Database connection & utilities
│   ├── clerk_auth.py                    # Clerk authentication
│   ├── user_plans.py                    # User plan management
│   ├── editable_plans.py                # Plan editing logic
│   ├── custom_workouts_api.py           # Custom workout routes
│   ├── video_library_api.py             # Video library routes
│   ├── workout_logging_api.py           # Workout logging routes
│   ├── analyzers/
│   │   ├── base_analyzer.py             # Base analyzer class
│   │   ├── user_image_analyzer.py       # Image analysis (body type detection)
│   │   ├── gemini_form_analyzer.py      # Gemini API integration for analysis
│   │   ├── pushup_analyzer.py           # Exercise-specific analyzers (not used)
│   │   ├── squat_analyzer.py            # (not used)
│   │   └── shoulder_press_analyzer.py   # (not used)
│   ├── static/
│   │   ├── index.html                   # Main UI
│   │   ├── app.js                       # Frontend logic
│   │   └── styles.css                   # Styling
│   └── __pycache__/                     # Python cache
├── Dockerfile                           # Docker build instructions
├── requirements.txt                     # Python dependencies
├── .env                                 # Environment variables (local)
├── .env.example                         # Environment template
├── railway.json                         # Railway config
├── init_database.sql                    # Database initialization
├── migrations/                          # SQL migration files
└── README.md                            # This file
```

---

## Setup & Installation

### Prerequisites
- Python 3.11+
- MySQL 8.0+
- FFmpeg (for video processing)
- pip/virtualenv

### Local Setup

1. **Clone the repository**
```bash
git clone https://github.com/moazanTUS/sculptfitt.git
cd sculpt
```

2. **Create virtual environment**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your values:
# - GEMINI_API_KEY (from Google AI Studio)
# - DB_HOST, DB_USER, DB_PASS, DB_NAME, DB_PORT
# - CLERK_SECRET_KEY (from Clerk dashboard)
# - ALLOWED_ORIGINS (for CORS)
```

5. **Create database**
```bash
mysql -u root -p < init_database.sql
# Or use your migration system
```

6. **Run the server**
```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000` in your browser.

---

## Running Locally

### Development Mode
```bash
# From project root with virtual env activated
.venv\Scripts\python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The server will:
- Start on `http://0.0.0.0:8000`
- Auto-reload on file changes
- Run migrations on startup
- Load all API routes

### Testing Rate Limiting
```bash
# Make 6 rapid requests to trigger 5/min limit:
for /L %i in (1,1,6) do curl -X POST http://localhost:8000/api/analyze-image-v2 -H "Content-Type: application/json" -d "{}"
# 6th request returns 429 Too Many Requests
```

---

## Deployment

### Railway Deployment

1. **Push to GitHub**
```bash
git add -A
git commit -m "Your message"
git push
```

2. **Connect Railway**
   - Go to [Railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select `moazanTUS/sculptfitt`
   - Add environment variables (same as `.env`)

3. **Railway auto-deploys** on push to main branch

### Docker Build (Manual)
```bash
docker build -t sculptfitt .
docker run -p 8000:8000 -e DB_HOST=localhost sculptfitt
```

### Health Check
Railway pings `/health` endpoint. App responds with status and DB info:
```json
{
  "status": "ok",
  "db_host": "...",
  "db_user": "...",
  "db_name": "...",
  "db_pass_set": true
}
```

---

## API Documentation

### Authentication
All endpoints except `/health` require Clerk JWT token in header:
```
Authorization: Bearer <token>
```

### Core Endpoints

#### Image Analysis
**POST** `/api/analyze-image-v2`
- Analyzes user's physique from photo
- Returns body type, focus areas, and matching plans
- Rate limit: 5/minute
- Requires: `consent` form field, `file` upload

```javascript
const form = new FormData();
form.append("file", imageFile);
form.append("consent", true);
form.append("difficulty", "beginner");
const res = await fetch("/api/analyze-image-v2", {
  method: "POST",
  headers: { "Authorization": `Bearer ${token}` },
  body: form
});
const data = await res.json();
// Returns: { success, body_type, focus_areas, matched_plans: [...] }
```

#### Video Analysis
**POST** `/api/analyze-video`
- Analyzes exercise form from video
- Returns form feedback and rep count
- Rate limit: 5/minute
- WebSocket support for live analysis

```javascript
const form = new FormData();
form.append("file", videoFile);
form.append("exercise", "pushup");
form.append("consent", true);
const res = await fetch("/api/analyze-video", {
  method: "POST",
  headers: { "Authorization": `Bearer ${token}` },
  body: form
});
const data = await res.json();
// Returns: { success, feedback, detected_reps, video_id }
```

#### Plan Selection
**POST** `/api/select-plan`
- Save a generated plan to user's account
- Rate limit: 30/minute

```javascript
const res = await fetch("/api/select-plan", {
  method: "POST",
  headers: { 
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json" 
  },
  body: JSON.stringify({
    plan_id: 123,
    plan_type: "ai"  // or "saved", "custom"
  })
});
```

#### My Plans
**GET** `/api/my-plans`
- List user's saved plans
- Rate limit: 60/minute

```javascript
const res = await fetch("/api/my-plans", {
  headers: { "Authorization": `Bearer ${token}` }
});
const plans = await res.json();
// Returns: { success, plans: [...] }
```

**DELETE** `/api/my-plans/{id}`
- Delete a plan
- Rate limit: 30/minute

#### Edit Plan
**POST** `/api/edit/days/{day_id}/items`
- Add exercise to a day
- Rate limit: 60/minute

**DELETE** `/api/edit/items/{item_id}`
- Remove exercise from plan
- Rate limit: 60/minute

#### Workout Logging
**POST** `/api/workout-sessions`
- Log a completed workout
- Rate limit: 60/minute

```javascript
const res = await fetch("/api/workout-sessions", {
  method: "POST",
  headers: { 
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json" 
  },
  body: JSON.stringify({
    day_id: 1,
    completed_exercises: [
      { exercise_id: 1, actual_sets: 3, actual_reps: 10, weight: 225 }
    ],
    rating: 8,
    notes: "Good form today"
  })
});
```

**GET** `/api/progress/stats`
- Get workout statistics

### Static Files
**GET** `/static/{path}`
- Serves HTML, CSS, JS files

**GET** `/outputs/{path}`
- Serves generated analysis outputs

**GET** `/health`
- Health check (no auth required)
- Returns status and database info

---

## Architecture Overview

### Request Flow

```
Browser (Frontend)
    ↓
FastAPI Server (main.py)
    ↓
├─ Authentication (Clerk)
├─ Rate Limiting (slowapi)
├─ CORS Middleware
└─ Routes
    ├─ Image Analysis
    │  └─ UserImageAnalyzer (Gemini AI + MediaPipe)
    ├─ Video Analysis
    │  └─ ExerciseAnalyzer (Pose detection + AI feedback)
    ├─ Plan Management
    │  └─ Plan APIs (user_plans.py, plan_api.py)
    ├─ Workout Logging
    │  └─ Workout Session APIs
    └─ Static Files
        └─ Frontend UI
    ↓
MySQL Database
```

### Key Components

#### 1. **Authentication (clerk_auth.py)**
- Verifies JWT tokens from Clerk
- Extracts user ID from token
- Dependency injection for protected routes

#### 2. **Image Analysis (analyzers/user_image_analyzer.py)**
- Takes user photo as input
- Uses MediaPipe to detect pose/body landmarks
- Sends to Gemini AI for analysis
- Returns body type and focus areas
- Triggers automatic plan matching

#### 3. **Video Analysis (analyzers/\*_analyzer.py)**
- Exercise-specific form checking
- Detects reps from pose sequence
- Provides real-time WebSocket updates
- Generates form feedback via Gemini

#### 4. **Plan Management (user_plans.py, plan_api.py)**
- Saves user plans to database
- Stores plan structure (days → exercises)
- Allows editing (add/remove exercises)
- Tracks which plans are AI-generated vs custom

#### 5. **Database (db.py)**
- MySQL connection pooling
- Utility functions for common queries
- Transaction handling

---

## Feature Documentation

### Image Analysis Workflow

1. User uploads photo + grants consent
2. `/api/analyze-image-v2` receives request
3. UserImageAnalyzer processes image:
   - Detects body type (ectomorph, mesomorph, endomorph)
   - Identifies focus areas (upper body, legs, core)
   - Analyzes posture and symmetry
4. Results sent to Gemini AI for detailed analysis
5. Plan matcher finds 3 best matching plans
6. Frontend displays results + allows saving plan

### Video Analysis Workflow

1. User uploads video + selects exercise
2. `/api/analyze-video` processes video
3. Video stored temporarily, video_id returned
4. Frontend initiates WebSocket connection with video_id
5. ExerciseAnalyzer (specific to exercise type) processes frames:
   - Detects pose in each frame
   - Counts reps from pose sequence
   - Identifies form issues
6. Results streamed via WebSocket in real-time
7. Frontend displays feedback + rep count

### Workout Plan System

**Types of Plans:**
- **AI-Generated**: Created from image analysis, saved with prefix `ai_`
- **Saved Templates**: Pre-made plans, saved with prefix `saved_`
- **Custom**: User-created from scratch, saved with prefix `custom_`

**Plan Structure:**
```
Plan
├─ ID
├─ Name
├─ Days (3 or 5 day split)
│  ├─ Day 1 (chest + triceps)
│  │  ├─ Exercise 1 (Bench Press - 4x8)
│  │  ├─ Exercise 2 (Incline DB Press - 3x10)
│  │  └─ Exercise 3 (Tricep Rope - 3x12)
│  ├─ Day 2 (back + biceps)
│  └─ ...
```

### Progress Tracking

**Logged Data:**
- Workout sessions (date, duration, exercises completed)
- Exercise performance (actual reps, sets, weight used)
- User ratings (subjective difficulty)
- Notes (what went well, form notes)

**Statistics:**
- Total workouts completed
- Total minutes trained
- Average rating
- Top exercises (by frequency)
- Personal records

---

## Security

### Rate Limiting
- **Per-user tracking**: Uses hashed auth token for unique identification
- **IP fallback**: Uses client IP for unauthenticated requests
- **Limits applied**:
  - Image analysis: 5/minute (heavy computation)
  - Video analysis: 5/minute (video processing)
  - Plan selection: 30/minute
  - Data endpoints: 60/minute
- **Response**: 429 Too Many Requests when limit exceeded

### Authentication
- **Clerk JWT**: Verifies token on every protected request
- **Token extraction**: From Authorization header
- **User isolation**: Each user only sees their own data

### Input Validation
- File type checking (images, videos only)
- File size limits
- Form field validation
- SQL injection prevention (parameterized queries)

### Error Handling
- Database errors hidden from user responses
- Detailed errors logged server-side
- Generic error messages returned to client
- No schema information leaked

### CORS
- Only whitelisted origins allowed
- Prevents cross-site attacks
- Configured via `ALLOWED_ORIGINS` env var

---

## Troubleshooting

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8000
kill -9 <PID>
```

### Database Connection Issues
- Verify credentials in `.env`
- Ensure MySQL is running
- Check network/firewall access
- Verify database exists: `SHOW DATABASES;`

### Missing Dependencies
```bash
pip install -r requirements.txt --upgrade
```

### Rate Limiting Too Strict
- Edit limits in `/api/` endpoints (@limiter.limit decorator)
- Default: 5/min for analysis, 30-60/min for other endpoints

### Video Analysis Not Working
- Ensure FFmpeg is installed: `ffmpeg -version`
- Check video codec compatibility
- Verify MediaPipe is installed: `pip show mediapipe`

---

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and test locally
3. Push to GitHub: `git push origin feature/your-feature`
4. Create Pull Request
5. Railway auto-deploys after merge to main

---

## License

[Add your license here]

---

## Contact

- GitHub: [moazanTUS/sculptfitt](https://github.com/moazanTUS/sculptfitt)
- Issues: [GitHub Issues](https://github.com/moazanTUS/sculptfitt/issues)

