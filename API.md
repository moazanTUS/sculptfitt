# SculpFit API Reference

Complete API documentation for all endpoints.

## Base URL
- **Development**: `http://localhost:8000`
- **Production**: `https://sculptfitt-production.up.railway.app` (or your Railway domain)

## Authentication
Most endpoints require Clerk JWT authentication. Include in header:
```
Authorization: Bearer <jwt_token>
```

## Response Format
All responses are JSON:
```json
{
  "success": true/false,
  "data": {...},
  "error": "error message if success is false"
}
```

---

## Endpoints

### Health Check
**GET** `/health`
- No authentication required
- Used by Railway for health checks
- Returns: `{ "status": "ok", "db_host": "...", ... }`

---

## Image Analysis

### Analyze Image
**POST** `/api/analyze-image-v2`

Analyzes user's body type and physique from uploaded photo.

**Rate Limit**: 5 requests/minute

**Request**:
```
Content-Type: multipart/form-data

Parameters:
- file: UploadFile (required) - JPEG/PNG image, max 10MB
- consent: boolean (required) - User consent for analysis
- difficulty: string (optional) - "beginner", "intermediate", "advanced" (default: "intermediate")
- plan_days: string (optional) - "3" or "5" day split (default: "3")
```

**cURL**:
```bash
curl -X POST http://localhost:8000/api/analyze-image-v2 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@photo.jpg" \
  -F "consent=true" \
  -F "difficulty=intermediate"
```

**Response** (200):
```json
{
  "success": true,
  "type": "image_v2",
  "body_type": "mesomorph",
  "primary_focus": "chest",
  "secondary_focuses": ["back", "shoulders"],
  "difficulty": "intermediate",
  "rationale": "Detected lean build with narrow shoulders...",
  "workout_plan": {
    "days": [
      {
        "day": 1,
        "focus": "Chest",
        "exercises": [
          {
            "name": "Bench Press",
            "muscle_group": "chest",
            "reps": "6-12",
            "sets": 3,
            "rest_seconds": 90,
            "form_tips": "Keep shoulder blades retracted..."
          }
        ]
      }
    ],
    "days_per_week": 4,
    "notes": "This plan is tailored for your body type..."
  }
}
```

**Errors**:
- 400: No consent provided
- 413: File too large
- 415: Invalid file type
- 429: Rate limit exceeded

---

## Video Analysis

### Analyze Video
**POST** `/api/analyze-video`

Analyzes exercise form from uploaded video.

**Rate Limit**: 5 requests/minute

**Request**:
```
Content-Type: multipart/form-data

Parameters:
- file: UploadFile (required) - MP4/MOV video
- exercise: string (required) - Exercise name (pushup, squat, etc.)
- consent: boolean (required) - User consent
- start_time: float (optional) - Start at time in seconds
- end_time: float (optional) - End at time in seconds
- rep_count: int (optional) - Expected rep count for validation
```

**cURL**:
```bash
curl -X POST http://localhost:8000/api/analyze-video \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@exercise.mp4" \
  -F "exercise=pushup" \
  -F "consent=true"
```

**Response** (200):
```json
{
  "success": true,
  "type": "gemini_analysis",
  "exercise": "pushup",
  "feedback": "Great form on descent. Keep core tight.",
  "raw_response": "...",
  "num_frames_analyzed": 7,
  "detected_reps": null
}
```

**WebSocket** (Live Analysis):
```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/analyze-video/${videoId}`);
ws.onmessage = (e) => {
  const data = JSON.parse(e.data);
  // { type: "analysis_complete", feedback: "...", exercise: "..." }
  // { type: "error", message: "..." }
};
```

**Errors**:
- 400: No exercise specified
- 415: Invalid video format
- 429: Rate limit exceeded

---

## Plans

### Get My Plans
**GET** `/api/my-plans`

Get all saved plans for current user.

**Rate Limit**: 60 requests/minute

**Response** (200):
```json
{
  "success": true,
  "plans": [
    {
      "id": "ai_123",
      "name": "Personalized Chest Focus",
      "type": "ai",
      "created_at": "2026-01-04T10:00:00Z",
      "days": 5,
      "exercises_count": 15
    }
  ]
}
```

### Select Plan
**POST** `/api/select-plan`

Save a matched plan to user's account.

**Rate Limit**: 30 requests/minute

**Request**:
```json
{
  "plan_id": 1,
  "plan_type": "ai"
}
```

**Response** (201):
```json
{
  "success": true,
  "saved_id": "ai_456",
  "message": "Plan saved successfully"
}
```

### Available Plans
**GET** `/api/available-plans`

Get all available pre-built workout plans.

**Response** (200):
```json
{
  "plans": [
    {
      "id": 1,
      "name": "Upper Body Strength",
      "body_type": "mesomorph",
      "primary_focus": "chest",
      "difficulty": "intermediate",
      "days_per_week": 4
    }
  ]
}
```

### Get Plan Details
**GET** `/api/plans/{plan_id}`

Get full details of a specific plan including all days and exercises.

**Response** (200):
```json
{
  "plan": {
    "id": 1,
    "name": "Upper Body Strength",
    "days": [
      {
        "day_number": 1,
        "exercises": [
          {
            "exercise_id": 1,
            "name": "Bench Press",
            "sets": 4,
            "reps": "6-8"
          }
        ]
      }
    ]
  }
}
```

### Delete Plan
**DELETE** `/api/my-plans/{id}`

Delete a saved plan.

**Rate Limit**: 30 requests/minute

**Response** (200):
```json
{
  "success": true,
  "message": "Plan deleted"
}
```

---

## Plan Editing

### Get Editable Plan
**GET** `/api/my-plans/{saved_id}/editable`

Get the full editable version of a plan with all day and item IDs needed for editing.

**Rate Limit**: 60 requests/minute

**Path Parameters**:
- `saved_id`: Composite ID like `custom_9`, `ai_27`, or `saved_123`

**Response** (200):
```json
{
  "plan": {
    "id": 5,
    "name": "Custom Chest Routine",
    "days_per_week": 4,
    "primary_focus": "chest"
  },
  "days": [
    {
      "day_id": 14,
      "day": 1,
      "title": "Chest Day",
      "items": [
        {
          "item_id": 42,
          "exercise_id": 5,
          "exercise": "Bench Press",
          "muscle_group": "chest",
          "sets": 4,
          "reps": "6-8",
          "rest_seconds": 90,
          "position": 10,
          "notes": null
        }
      ]
    }
  ]
}
```

### Update Day Title
**PATCH** `/api/edit/days/{day_id}`

Update the title of a workout day.

**Rate Limit**: 60 requests/minute

**Request**:
```json
{
  "title": "Heavy Chest Day"
}
```

**Response** (200):
```json
{
  "success": true
}
```

### Add Exercise to Plan Day
**POST** `/api/edit/days/{day_id}/items`

Add an exercise to a specific day.

**Rate Limit**: 60 requests/minute

**Request**:
```json
{
  "exercise_name": "Incline Dumbbell Press",
  "muscle_group": "chest",
  "sets": 3,
  "reps": "10-12",
  "rest_seconds": 60
}
```

**Response** (201):
```json
{
  "success": true,
  "item_id": 43
}
```

### Remove Exercise from Plan
**DELETE** `/api/edit/items/{item_id}`

Remove an exercise from a plan day.

**Rate Limit**: 60 requests/minute

**Response** (200):
```json
{
  "success": true
}
```

### Update Exercise in Plan
**PATCH** `/api/edit/items/{item_id}`

Update an exercise in a plan day. Works for both user workout plans and custom workouts.

**Rate Limit**: 60 requests/minute

**Request**:
```json
{
  "exercise_name": "Incline Bench Press",
  "sets": 4,
  "reps": "6-8",
  "rest_seconds": 90,
  "notes": "Focus on upper chest",
  "item_type": "custom"
}
```

**Parameters**:
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| exercise_name | string | No | New exercise name |
| sets | int | No | Number of sets |
| reps | string | No | Rep range (e.g., "8-12") |
| rest_seconds | int | No | Rest time in seconds |
| notes | string | No | Optional notes |
| item_type | string | **Recommended** | `"custom"` or `"user"` - specifies which table to update |

**Note**: The `item_type` field is important when item IDs might overlap between `user_workout_day_items` and `custom_workout_exercises` tables. Pass `"custom"` when editing custom workouts (plans with `custom_` prefix) and `"user"` for AI-generated or pre-built plans.

**Response** (200):
```json
{
  "success": true
}
```

---

## Workout Logging

### Log Workout Session
**POST** `/api/workout-sessions`

Record a completed workout.

**Rate Limit**: 60 requests/minute

**Request**:
```json
{
  "day_id": 1,
  "completed_exercises": [
    {
      "exercise_id": 1,
      "actual_sets": 3,
      "actual_reps": 10,
      "weight": 185,
      "notes": "Felt strong"
    }
  ],
  "rating": 8,
  "duration_minutes": 45,
  "notes": "Great workout overall"
}
```

**Response** (201):
```json
{
  "success": true,
  "session_id": "sess_789",
  "message": "Workout logged"
}
```

### Get Workout History
**GET** `/api/workout-sessions`

Get user's past workout sessions.

**Response** (200):
```json
{
  "success": true,
  "sessions": [
    {
      "session_id": "sess_789",
      "date": "2026-01-04",
      "exercises": 5,
      "duration_minutes": 45,
      "rating": 8
    }
  ]
}
```

### Get Progress Statistics
**GET** `/api/progress/stats`

Get workout statistics and trends.

**Response** (200):
```json
{
  "success": true,
  "stats": {
    "total_workouts": 42,
    "total_minutes": 2100,
    "average_rating": 7.8,
    "streak_days": 5
  },
  "top_exercises": [
    {
      "exercise_name": "Bench Press",
      "total_times_completed": 12,
      "personal_record_weight": 315
    }
  ]
}
```

---

## Custom Workouts

### Create Custom Workout
**POST** `/api/custom-workouts`

Create a custom workout from scratch.

**Request**:
```json
{
  "name": "My Custom Routine",
  "exercises": [
    {
      "name": "Push-ups",
      "sets": 3,
      "reps": "15"
    }
  ]
}
```

**Response** (201):
```json
{
  "success": true,
  "workout_id": "cust_123"
}
```

### Get Custom Workouts
**GET** `/api/custom-workouts`

List all user's custom workouts.

**Response** (200):
```json
{
  "success": true,
  "workouts": [
    {
      "id": "cust_123",
      "name": "Home Workout",
      "exercises": 5
    }
  ]
}
```

---

## Video Library

### Get Exercise Videos
**GET** `/api/video-library`

Browse available exercise videos.

**Query Parameters**:
- `exercise`: Filter by exercise name (optional)
- `difficulty`: Filter by difficulty (optional)
- `muscle_group`: Filter by muscle group (optional)

**Response** (200):
```json
{
  "success": true,
  "videos": [
    {
      "video_id": 1,
      "exercise": "pushup",
      "title": "Perfect Push-up Form",
      "url": "https://...",
      "difficulty": "beginner",
      "duration_seconds": 120
    }
  ]
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "success": false,
  "error": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "success": false,
  "error": "Invalid or missing authentication token"
}
```

### 404 Not Found
```json
{
  "success": false,
  "error": "Resource not found"
}
```

### 429 Too Many Requests
```json
{
  "detail": "Too many requests. Please try again later."
}
```

### 500 Internal Server Error
```json
{
  "success": false,
  "error": "Internal server error"
}
```

---

## Rate Limits

| Endpoint | Limit | Per |
|----------|-------|-----|
| `/api/analyze-image-v2` | 5 | minute |
| `/api/analyze-video` | 5 | minute |
| `/api/select-plan` | 30 | minute |
| `/api/my-plans` | 60 | minute |
| `/api/my-plans/{id}` (DELETE) | 30 | minute |
| `/api/edit/days/{id}/items` | 60 | minute |
| `/api/edit/items/{id}` | 60 | minute |
| `/api/workout-sessions` | 60 | minute |

Limits are **per user** (identified by auth token hash). Unauthenticated requests use IP address.

---

## Code Examples

### JavaScript/Fetch
```javascript
// Get auth token from Clerk
const token = await clerk.session.getToken();

// Make API request
const response = await fetch('/api/my-plans', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});

const data = await response.json();
```

### Python/Requests
```python
import requests

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

response = requests.get(
    'http://localhost:8000/api/my-plans',
    headers=headers
)

data = response.json()
```

### cURL
```bash
curl -X GET http://localhost:8000/api/my-plans \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

