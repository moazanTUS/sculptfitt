from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List
from .db import get_conn

router = APIRouter()

GET_PLAN_SQL = """
SELECT id, name, days_per_week, primary_focus
FROM workout_plans
WHERE id = %s
LIMIT 1;
"""

GET_PLAN_EXERCISES_SQL = """
SELECT id, plan_id, day, exercise_name, muscle_group, sets, reps, rest_seconds, sort_order
FROM plan_exercises
WHERE plan_id = %s
ORDER BY day ASC, sort_order ASC;
"""

DELETE_PLAN_EXERCISES_SQL = "DELETE FROM plan_exercises WHERE plan_id = %s;"

INSERT_EX_SQL = """
INSERT INTO plan_exercises (plan_id, day, exercise_name, muscle_group, sets, reps, rest_seconds, sort_order)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
"""


class ExerciseIn(BaseModel):
    day: int = Field(ge=1, le=7)
    exercise_name: str = Field(min_length=1, max_length=120)
    muscle_group: str = Field(min_length=1, max_length=20)
    sets: int = Field(ge=1, le=10)
    reps: str = Field(min_length=1, max_length=20)
    rest_seconds: int = Field(ge=0, le=600)
    sort_order: int = Field(ge=0, le=200)


class ReplaceExercisesPayload(BaseModel):
    exercises: List[ExerciseIn]


@router.get("/api/plans/{plan_id}")
def get_plan(plan_id: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(GET_PLAN_SQL, (plan_id,))
            plan = cur.fetchone()
            if not plan:
                return {"success": False, "error": "Plan not found"}

            cur.execute(GET_PLAN_EXERCISES_SQL, (plan_id,))
            exercises = cur.fetchall()

    return {"success": True, "plan": plan, "exercises": exercises}


@router.put("/api/plans/{plan_id}/exercises")
def replace_plan_exercises(plan_id: int, payload: ReplaceExercisesPayload):
    # Replace-all strategy: simple, consistent, avoids partial updates.
    # (Professional enough for MVP; can add per-row edits later.)
    with get_conn() as conn:
        with conn.cursor() as cur:
            # ensure plan exists
            cur.execute("SELECT id FROM workout_plans WHERE id=%s LIMIT 1;", (plan_id,))
            if not cur.fetchone():
                return {"success": False, "error": "Plan not found"}

            cur.execute(DELETE_PLAN_EXERCISES_SQL, (plan_id,))

            for ex in payload.exercises:
                cur.execute(
                    INSERT_EX_SQL,
                    (
                        plan_id,
                        ex.day,
                        ex.exercise_name,
                        ex.muscle_group.lower().strip(),
                        ex.sets,
                        ex.reps.strip(),
                        ex.rest_seconds,
                        ex.sort_order,
                    ),
                )

    return {"success": True}
