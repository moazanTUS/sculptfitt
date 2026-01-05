# SculpFit Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Frontend (HTML/CSS/JavaScript)                          │   │
│  │  - Image Upload Form                                    │   │
│  │  - Video Upload & Analysis                             │   │
│  │  - Workout Plan Display & Editing                      │   │
│  │  - Progress Tracking Dashboard                         │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTP/WebSocket
                    (Authorization: Bearer Token)
┌─────────────────────────────────────────────────────────────────┐
│                      RAILWAY (Cloud)                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    FastAPI Server                        │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  Routes & Middleware                               │  │   │
│  │  │  - CORS Protection                                │  │   │
│  │  │  - Rate Limiting (slowapi)                        │  │   │
│  │  │  - Clerk Authentication                           │  │   │
│  │  │  - Error Handling                                 │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │                                                           │   │
│  │  ┌──────────────────┐  ┌──────────────────────────────┐ │   │
│  │  │  API Endpoints   │  │  File Handling               │ │   │
│  │  │                  │  │  - Image Upload/Processing  │ │   │
│  │  │ - Image Analysis │  │  - Video Upload/Trimming    │ │   │
│  │  │ - Video Analysis │  │  - Temporary Storage        │ │   │
│  │  │ - Plan Management│  └──────────────────────────────┘ │   │
│  │  │ - Workout Logging│                                    │   │
│  │  │ - Video Library  │  ┌──────────────────────────────┐ │   │
│  │  │ - Static Files   │  │  AI/ML Components           │ │   │
│  │  └──────────────────┘  │  - UserImageAnalyzer        │ │   │
│  │                        │  - PushupAnalyzer           │ │   │
│  │                        │  - SquatAnalyzer            │ │   │
│  │                        │  - ShoulderPressAnalyzer    │ │   │
│  │                        │  - Gemini API (AI Analysis) │ │   │
│  │                        └──────────────────────────────┘ │   │
│  │                                                           │   │
│  │  ┌──────────────────────────────────────────────────────┐ │   │
│  │  │  Database Layer                                      │ │   │
│  │  │  ┌─────────────────────────────────────────────────┐ │ │   │
│  │  │  │  Core Functions (db.py)                         │ │ │   │
│  │  │  │  - Connection pooling                           │ │ │   │
│  │  │  │  - Query execution                             │ │ │   │
│  │  │  │  - Transaction handling                        │ │ │   │
│  │  │  │  - User isolation                              │ │ │   │
│  │  │  └─────────────────────────────────────────────────┘ │ │   │
│  │  │                                                       │ │   │
│  │  │  ┌─────────────────────────────────────────────────┐ │ │   │
│  │  │  │  Business Logic                                │ │ │   │
│  │  │  │  - user_plans.py (Plan CRUD)                 │ │ │   │
│  │  │  │  - editable_plans.py (Plan Editing)         │ │ │   │
│  │  │  │  - custom_workouts_api.py (Custom Plans)    │ │ │   │
│  │  │  │  - workout_logging_api.py (Logging)         │ │ │   │
│  │  │  │  - video_library_api.py (Exercise Videos)   │ │ │   │
│  │  │  └─────────────────────────────────────────────────┘ │ │   │
│  │  │                                                       │ │   │
│  │  │  ┌─────────────────────────────────────────────────┐ │ │   │
│  │  │  │  Migrations (Automatic on Startup)             │ │ │   │
│  │  │  │  - Schema initialization                       │ │ │   │
│  │  │  │  - Non-blocking (async)                        │ │ │   │
│  │  │  │  - Idempotent (safe to re-run)                │ │ │   │
│  │  │  └─────────────────────────────────────────────────┘ │ │   │
│  │  └──────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  MySQL Database (Railway or External)                   │   │
│  │  Tables:                                                │   │
│  │  - exercises (Exercise library)                        │   │
│  │  - workout_plans (Pre-built plan templates)            │   │
│  │  - plan_exercises (Exercises in pre-built plans)       │   │
│  │  - user_saved_plans (User-selected plans)              │   │
│  │  - user_workout_plans (Editable plans)                 │   │
│  │  - user_workout_days (Days in user plans)              │   │
│  │  - user_workout_day_items (Exercises in days)          │   │
│  │  - custom_workouts (User-created plans)                │   │
│  │  - custom_workout_days (Days in custom plans)          │   │
│  │  - custom_workout_exercises (Exercises in days)        │   │
│  │  - exercise_videos (Video library)                     │   │
│  │  - workout_sessions (Logged workout sessions)          │   │
│  │  - workout_session_exercises (Logged exercises)        │   │
│  │  - workout_progress (PRs and stats)                    │   │
│  │  - migrations (Schema version tracking)                │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                      (External Services)
┌─────────────────────────────────────────────────────────────────┐
│  Google Gemini API                                              │
│  - Analyzes workout form & posture                             │
│  - Generates personalized feedback                            │
│  - Creates AI workout plans                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow - Image Analysis

```
User Upload
    ↓
┌─────────────────────────────────────────┐
│ POST /api/analyze-image-v2              │
│ - Validate file (type, size)            │
│ - Check rate limit                      │
│ - Verify auth token                     │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ UserImageAnalyzer                       │
│ - Load image into memory                │
│ - Extract landmarks                     │
│ - Detect body type from silhouette      │
│ - Calculate symmetry & posture          │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Gemini API (AI Analysis)                │
│ - Send landmarks + body metrics         │
│ - Get detailed analysis                 │
│ - Generate focus areas                  │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Workout Plan Generation (main.py)       │
│ - Generate AI workout plan              │
│ - Query/create exercises                │
│ - Save to user_workout_plans            │
└─────────────────────────────────────────┘
    ↓
Response to Frontend
- body_type
- focus_areas
- generated_plan{}
    ↓
Plan automatically saved to database
┌─────────────────────────────────────────┐
│ POST /api/select-plan                   │
│ - Save plan to user_workout_plans       │
│ - Store plan days & exercises           │
│ - Return saved_id                       │
└─────────────────────────────────────────┘
    ↓
Plan displayed in "My Plans"
```

## Data Flow - Video Analysis

```
User Upload
    ↓
┌─────────────────────────────────────────┐
│ POST /api/analyze-video                 │
│ - Validate video file                   │
│ - Check rate limit                      │
│ - Extract frames (FFmpeg)               │
│ - Store temporarily                     │
└─────────────────────────────────────────┘
    ↓
Return video_id + WebSocket URL
    ↓
Frontend connects WebSocket
    ↓
┌─────────────────────────────────────────┐
│ Exercise-Specific Analyzer              │
│ - Process video frame by frame          │
│ - Detect pose and joint movements       │
│ - Track motion patterns                 │
│ - Count reps                            │
│ - Detect form issues                    │
└─────────────────────────────────────────┘
    ↓
For Each Issue Detected
    ↓
Send to Gemini API for explanation
    ↓
Stream via WebSocket to Frontend
- frame progress
- rep count updates
- form feedback
    ↓
Analysis Complete
    ↓
Frontend displays results:
- Total reps counted
- Form feedback
- Issues found
- Suggestions
```

## Data Flow - Workout Logging

```
User completes workout
    ↓
User opens "Log Workout" dialog
    ↓
User enters:
- Which day of plan
- Actual reps/sets/weight
- Difficulty rating
- Notes
    ↓
POST /api/workout-sessions
    ↓
┌─────────────────────────────────────────┐
│ Record Workout in Database              │
│ - Create workout_sessions row           │
│ - Link to day_id                        │
│ - Store exercise data                   │
│ - Calculate stats                       │
└─────────────────────────────────────────┘
    ↓
GET /api/progress/stats
    ↓
Return updated statistics:
- Total workouts
- Total minutes
- Average rating
- Top exercises
- Streaks
    ↓
Display on Progress page
```

## Component Dependencies

```
main.py (FastAPI App)
├── clerk_auth.py (Authentication)
├── db.py (Database Connection)
├── user_plans.py (User CRUD)
│   └── db.py
├── editable_plans.py (Plan Editing)
│   └── db.py
├── custom_workouts_api.py
│   └── db.py
├── video_library_api.py
│   └── db.py
├── workout_logging_api.py
│   └── db.py
├── analyzers/
│   ├── base_analyzer.py (Base class)
│   ├── user_image_analyzer.py (Body type detection - ACTIVE)
│   │   ├── base_analyzer.py
│   │   └── Gemini API
│   ├── gemini_form_analyzer.py (AI form feedback - ACTIVE)
│   │   └── Gemini API
│   ├── pushup_analyzer.py (Not used in app)
│   ├── squat_analyzer.py (Not used in app)
│   ├── shoulder_press_analyzer.py (Not used in app)
│   └── __init__.py
└── static/ (Frontend)
    ├── index.html
    ├── app.js
    └── styles.css
```

## Deployment Architecture

```
GitHub Repository
    ↓ (push to main)
Railway Webhook
    ↓
┌──────────────────────────────┐
│ Docker Build                 │
│ - Install Python 3.11        │
│ - Install system deps        │
│ - pip install requirements   │
│ - Copy app code              │
└──────────────────────────────┘
    ↓
┌──────────────────────────────┐
│ Docker Image                 │
│ - Uploaded to Railway        │
│ - Stored in registry         │
└──────────────────────────────┘
    ↓
┌──────────────────────────────┐
│ Container Deployment         │
│ - Start container(s)         │
│ - Set environment variables  │
│ - Expose port 8000           │
│ - Run migrations (async)     │
└──────────────────────────────┘
    ↓
┌──────────────────────────────┐
│ Health Check                 │
│ - Ping /health endpoint      │
│ - Verify DB connection       │
│ - Check 3 times (30s window) │
└──────────────────────────────┘
    ↓
┌──────────────────────────────┐
│ Load Balancer                │
│ - Route traffic to container │
│ - Handle HTTPS               │
│ - Auto-scale if needed       │
└──────────────────────────────┘
    ↓
Public URL
https://sculptfitt-production.up.railway.app
```

## Rate Limiting Architecture

```
Request Comes In
    ↓
SlowAPI Middleware
    ↓
┌─────────────────────────────────────────┐
│ Identify User                           │
│                                         │
│ If Authorization header present:       │
│   - Extract Bearer token               │
│   - Hash token to create unique ID     │
│   - Use as rate limit key             │
│                                         │
│ Else:                                  │
│   - Use client IP address              │
│   - Use as rate limit key             │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Check Rate Limit                        │
│                                         │
│ Look up: <key>:<endpoint>               │
│ Count requests in window (1 minute)     │
│                                         │
│ If count < limit:                      │
│   - Increment counter                  │
│   - Allow request                      │
│   - Process normally                   │
│                                         │
│ Else:                                  │
│   - Return 429 Too Many Requests       │
│   - Don't process request              │
└─────────────────────────────────────────┘
```

## Security Flow

```
Request
    ↓
├─ Public Endpoint (/health)?
│  └─ No auth required, continue
│
├─ CORS Check
│  ├─ Origin in ALLOWED_ORIGINS?
│  │  └─ Yes, continue
│  └─ No, reject request
│
├─ Rate Limit Check
│  ├─ Below limit?
│  │  └─ Yes, continue
│  └─ No, return 429
│
└─ Authentication Check
   ├─ Authorization header present?
   │  ├─ Yes, extract token
   │  └─ No, reject
   │
   ├─ Token valid (Clerk)?
   │  ├─ Yes, extract user_id
   │  └─ No, reject
   │
   └─ User isolated data access
      └─ Only see own data

Process Request
    ↓
Return Response
```

