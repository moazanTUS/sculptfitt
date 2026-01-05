# SculpFit Code Flow & Implementation Guide

## High-Level Architecture

```
FastAPI Server (main.py)
├── Authentication (Clerk tokens)
├── Rate Limiting (slowapi)
├── API Endpoints (GET/POST/DELETE)
├── Analyzers (Image & Video)
├── Database Layer (db.py)
└── Business Logic (user_plans.py, editable_plans.py, etc.)
```

## Key Files & Responsibilities

### `main.py` - FastAPI Server
Main application server with all endpoints. **1169 lines**

**Key Sections:**
- Lines 81-98: Rate limiting key function (per-user token hashing)
- Lines 120-231: Health check & auth endpoints
- Lines 238-346: Plan browsing (available plans, plan details)
- Lines 348-397: POST `/api/select-plan` - Select pre-built plan
- Lines 399-535: POST `/api/analyze-image-v2` - Image analysis & plan generation
- Lines 537-680: GET/DELETE `/api/my-plans` - User's plans list
- Lines 694-770: Plan editing endpoints (title, add/remove items, reorder)
- Lines 771-925: Video analysis (upload + WebSocket streaming)
- Lines 926-1169: Export, auth utilities

### `db.py` - Database Connection Pool
Manages MySQL connections with context manager pattern.

```python
def get_conn():
    # Returns connection context manager
    # Auto-releases connection on exit
```

**Usage Pattern:**
```python
with get_conn() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM exercises")
```

### `user_plans.py` - Plan Management (170 lines)
Core functions for saving, listing, and retrieving plans.

**Functions:**
- `save_user_plan()` - Inserts into `user_saved_plans` table
- `list_user_plans()` - Gets all AI-generated + custom plans for user
- `get_saved_plan()` - Fetch single plan details
- `delete_user_plan()` - Delete by plan type (ai_, custom_, saved_)

**Key Logic:**
- Composite IDs: `ai_123`, `custom_456`, `saved_789`
- Distinguishes between saved pre-built plans and AI-generated plans

### `editable_plans.py` - Plan Editing
Functions to modify workout plans.

**Functions:**
- `ensure_editable_copy()` - Create editable copy from saved plan
- `update_day_title()` - Change day name (e.g., "Chest Day")
- `add_day_item()` - Add exercise to day
- `update_day_item()` - Modify exercise (sets, reps, etc.)
- `delete_day_item()` - Remove exercise from day
- `reorder_day_items()` - Change exercise order in day

### `analyzers/user_image_analyzer.py` - Image Analysis (237 lines)
Analyzes user photo to determine body type & generate personalized plan.

**Flow:**
1. User uploads image
2. Image loaded into memory as BytesIO (never saved to disk)
3. Gemini Vision API analyzes image
4. Gemini identifies:
   - `body_type`: ectomorph, mesomorph, endomorph
   - `primary_focus`: chest, back, shoulders, legs
   - `secondary_focuses`: [2 additional muscle groups]
5. Generate workout prompt based on body type + focus
6. Gemini generates complete workout plan JSON
7. Plan saved to `user_workout_plans` table

**Key Functions:**
- `analyze()` - Main entry point, returns full analysis
- `generate_workout_prompt()` - Creates prompt for plan generation
- Prompts defined for body type + difficulty combinations

### `analyzers/gemini_form_analyzer.py` - Video Form Analysis
Analyzes exercise videos to detect form issues.

**Flow:**
1. Video uploaded to `/api/analyze-video`
2. Video stored temporarily in `outputs/` directory
3. WebSocket connection established at `/ws/analyze-video/{video_id}`
4. Frame-by-frame analysis:
   - Extract frames from video
   - Detect pose landmarks
   - Identify exercise type
   - Find form issues
   - Send feedback to Gemini
5. Stream results back via WebSocket
6. Client displays real-time feedback

**Note:** Legacy exercise-specific analyzers (PushupAnalyzer, SquatAnalyzer, ShoulderPressAnalyzer) are in the codebase but not actively used. All video analysis now goes through GeminiFormAnalyzer for consistency.

### `clerk_auth.py` - Authentication
Validates Clerk JWT tokens.

```python
def require_clerk_user(request: Request):
    # Extract bearer token from Authorization header
    # Validate with Clerk API
    # Return user info (clerk_user_id, email, etc.)
```

## API Endpoints Reference

### Authentication Required Endpoints

**GET `/api/me`**
- Returns current user info from Clerk
- Used to verify authentication status

**GET `/api/my-plans` (60/min)**
- Returns all user's plans (AI + custom + saved)
- Returns composite IDs: `ai_123`, `custom_456`, `saved_789`

**GET `/api/my-plans/{saved_id}`**
- Get full plan structure with all days and exercises
- Handles all three plan types

**GET `/api/my-plans/{saved_id}/editable`**
- Get plan in editable format
- Returns structure for frontend editing

**POST `/api/select-plan` (30/min)**
- Select a pre-built workout plan
- Creates entry in `user_saved_plans`
- Creates editable copy in `user_workout_plans`

**POST `/api/analyze-image-v2` (5/min)**
- Upload photo for body analysis
- Returns: body_type, focus areas, generated workout plan
- Plan automatically saved to `user_workout_plans`

**POST `/api/edit/days/{user_day_id}/items`**
- Add exercise to workout day
- Request: `{ exercise_id, sets, reps, rest_seconds }`

**DELETE `/api/edit/items/{item_id}`**
- Remove exercise from day

**PATCH `/api/edit/days/{user_day_id}/title`**
- Update day title (e.g., "Chest & Triceps")

**POST `/api/analyze-video` (5/min)**
- Upload video for form analysis
- Returns video_id and WebSocket URL

**WebSocket `/ws/analyze-video/{video_id}`**
- Real-time video analysis stream
- Sends frame progress, rep count, form feedback

**GET `/api/available-plans`**
- Get pre-built workout plans (not user-specific)
- Optional `days` query parameter to filter

**GET `/api/plans/{plan_id}`**
- Get details of specific pre-built plan
- Returns all days and exercises

### Public Endpoints

**GET `/health`**
- Health check (no auth)
- Used by Railway deployment health checks

**GET `/`**
- Serves static HTML frontend

---

## Data Flow Examples

### Flow 1: User Uploads Photo & Gets Custom Plan

```
1. User uploads image file
   → POST /api/analyze-image-v2
   
2. Backend receives file
   → Read into BytesIO
   → Create UserImageAnalyzer
   
3. UserImageAnalyzer.analyze()
   → Call Gemini Vision API
   → Get body_type + focuses
   
4. Generate workout prompt based on:
   - body_type (ectomorph/mesomorph/endomorph)
   - primary_focus (chest/back/etc)
   - secondary_focuses (2 areas)
   - difficulty level
   - days_per_week
   
5. Call Gemini again to generate plan
   → Returns JSON with days[] and exercises[]
   
6. Save to user_workout_plans table
   → Insert name, primary_focus, body type
   
7. Create day rows in user_workout_days
   → day_number, title for each day
   
8. Create item rows in user_workout_day_items
   → Link exercises to days with sets/reps
   
9. Return to client with:
   - saved_id (composite: ai_123)
   - complete plan structure
   - Can now display in UI
```

### Flow 2: User Selects Pre-Built Plan

```
1. User browsing /api/available-plans
   → GET /api/available-plans
   → Returns list of pre-built plans from workout_plans table
   
2. User clicks "Select Plan" on plan ID 5
   → POST /api/select-plan with plan_id=5
   
3. Backend:
   a. Verify plan exists in workout_plans
   b. Insert into user_saved_plans
      → clerk_user_id, plan_id, body_type=null, focuses
   c. Call ensure_editable_copy()
      → Creates entry in user_workout_plans
      → Copies all days from plan_exercises
      → Creates user_workout_days for each day
      → Creates user_workout_day_items for each exercise
   
4. Return saved_id (composite: saved_123)
   
5. Plan now appears in /api/my-plans
```

### Flow 3: User Edits Plan

```
1. User viewing plan from /api/my-plans/{saved_id}
   → Plan has user_day_id values for each day
   
2. User renames day "Chest & Triceps" to "Upper Body"
   → PATCH /api/edit/days/{user_day_id}/title
   → Request: { "title": "Upper Body" }
   → Updates user_workout_days.title
   
3. User adds new exercise (Dumbbell Curls) to day
   → POST /api/edit/days/{user_day_id}/items
   → Request: { "exercise_id": 22, "sets": 3, "reps": "8-12", "rest_seconds": 90 }
   → Inserts into user_workout_day_items
   
4. User removes Lat Pulldowns
   → DELETE /api/edit/items/{item_id}
   → Deletes from user_workout_day_items
   
5. Plan updated in real-time, visible in /api/my-plans/{saved_id}
```

### Flow 4: User Analyzes Video Form

```
1. User uploads video file
   → POST /api/analyze-video
   → file, exercise_type (optional)
   
2. Backend:
   a. Save video temporarily to outputs/ directory
   b. Generate video_id (UUID)
   c. Return video_id to client
   
3. Client connects WebSocket
   → /ws/analyze-video/{video_id}
   
4. Backend starts analysis:
   a. Load video file
   b. Extract frames
   c. For each frame:
      - Detect exercise type (pushup/squat/etc)
      - Extract pose landmarks
      - Analyze form
      - Detect issues
      - Send issues to Gemini for explanation
   
5. Stream updates via WebSocket:
   → { "type": "progress", "frames_processed": 150, "total": 300 }
   → { "type": "rep_count", "reps": 5, "form_quality": "good" }
   → { "type": "feedback", "issue": "Elbows flaring out", "tip": "... " }
   
6. When complete:
   → { "type": "complete", "total_reps": 12, "issues": [...] }
   
7. Client displays results to user
```

---

## Database Query Patterns

### Get User's All Plans (AI + Custom + Saved)

```python
# In user_plans.py list_user_plans()

# Query 1: AI-generated plans
SELECT CONCAT('ai_', uwp.id) as id, ...
FROM user_workout_plans uwp
WHERE uwp.clerk_user_id = ?

# Query 2: Custom user workouts
SELECT CONCAT('custom_', cw.id) as id, ...
FROM custom_workouts cw
WHERE cw.clerk_user_id = ?

# Combined and sorted by created_at DESC
```

### Get Full Plan With All Exercises

```python
# In main.py _get_editable_payload()

# Get plan metadata
SELECT * FROM user_workout_plans WHERE id = ?

# Get all days
SELECT * FROM user_workout_days WHERE user_plan_id = ?

# For each day, get exercises
SELECT uwdi.*, e.name, e.primary_muscle
FROM user_workout_day_items uwdi
JOIN exercises e ON uwdi.exercise_id = e.id
WHERE uwdi.user_day_id = ?
ORDER BY uwdi.position
```

### Delete Plan (Handles 3 Types)

```python
# In user_plans.py delete_user_plan()

if saved_id.startswith('custom_'):
    DELETE FROM custom_workouts WHERE id = ?
    
elif saved_id.startswith('ai_'):
    DELETE FROM user_workout_plans WHERE id = ?
    
elif saved_id.startswith('saved_'):
    DELETE FROM user_saved_plans WHERE id = ?
    # Cascade deletes user_workout_plans if exists
```

---

## Gemini API Integration

### Image Analysis Prompt
```
You are an expert fitness assessment specialist.
Analyze the image to determine:
1. Body type (ectomorph/mesomorph/endomorph)
2. Primary focus area (chest/back/shoulders/legs)
3. Secondary focuses (2 additional areas)
4. Rationale based on visible muscle development

Return ONLY valid JSON (no markdown)
```

### Workout Generation Prompt
```
You are an expert personal trainer.
Create a detailed {days_per_week}-day workout split for a {body_type} individual.

Profile:
- Body Type: {body_type}
- Primary Focus: {primary_focus}
- Secondary Focuses: [...]
- Difficulty: {difficulty}
- Rep Range: {rep_range}
- Sets per Exercise: {sets}

For each day include:
- Day title
- List of exercises with:
  - Exercise name
  - Muscle group
  - Sets x Reps
  - Rest time
  - Form tips

Return ONLY valid JSON
```

### Form Analysis Prompt
```
Analyze this exercise form for {exercise_type}.
Issues detected: {pose_analysis}

Provide:
1. Specific form corrections needed
2. How to fix each issue
3. Benefits of correct form
4. Injury prevention tips

Be concise and actionable.
```

---

## Rate Limiting

Rate limits are **per-user** (keyed by hashed Bearer token) with **IP fallback**.

| Endpoint | Limit |
|----------|-------|
| `/api/analyze-image-v2` | 5/minute |
| `/api/analyze-video` | 5/minute |
| `/api/select-plan` | 30/minute |
| `/api/my-plans` | 60/minute |
| `/api/edit/days/*/items` | 60/minute |
| `/api/edit/items/*` | 60/minute |

**Implementation:**
```python
def get_rate_limit_key(request: Request) -> str:
    if "Authorization" header present:
        token = extract_bearer_token()
        return f"user_{hashlib.md5(token).hexdigest()}"
    else:
        return get_remote_address(request)  # IP fallback
```

---

## Error Handling

### Common Responses

**401 Unauthorized**
```json
{
  "detail": "Unauthorized"
}
```

**429 Too Many Requests**
```json
{
  "detail": "Too many requests. Please try again later."
}
```

**404 Not Found**
```json
{
  "success": false,
  "error": "Plan not found"
}
```

**400 Bad Request**
```json
{
  "success": false,
  "error": "Error message here"
}
```

---

## Performance Optimizations

1. **Image Upload**: Never saves to disk, uses BytesIO for memory-only processing
2. **Rate Limiting**: Per-user token hashing ensures fair quotas
3. **CORS**: Whitelist specific origins with ALLOWED_ORIGINS env var
4. **Connection Pooling**: Database uses connection pool via `get_conn()`
5. **Plan Cache**: `plan_cache` table stores matched plans by user profile hash

---

## Security

1. **Auth**: Clerk JWT token validation on all protected endpoints
2. **CORS**: Only allowed origins can make requests
3. **Rate Limiting**: Prevents API abuse
4. **Input Validation**: Difficulty level validated, file types checked
5. **SQL Injection**: All queries use parameterized prepared statements
6. **User Isolation**: All queries filtered by `clerk_user_id`

---

## File Structure for Reference

```
backend/
├── main.py (1169 lines) - FastAPI server with all endpoints
├── db.py - Database connection pool
├── user_plans.py (170) - Plan CRUD operations
├── editable_plans.py - Plan editing functions
├── clerk_auth.py - Clerk JWT validation
├── custom_workouts_api.py - Custom workout endpoints
├── video_library_api.py - Video library endpoints
├── workout_logging_api.py - Workout logging endpoints
├── analyzers/
│   ├── base_analyzer.py - Base class for analyzers
│   ├── user_image_analyzer.py (237) - Image analysis & plan generation
│   ├── gemini_form_analyzer.py - Video form analysis (ACTIVE)
│   ├── pushup_analyzer.py - Legacy (not used)
│   ├── squat_analyzer.py - Legacy (not used)
│   ├── shoulder_press_analyzer.py - Legacy (not used)
│   └── __init__.py
├── outputs/ - Temporary video storage
├── static/ - Frontend files (index.html, app.js, styles.css)
└── uploads/ - Temporary upload directory
```
