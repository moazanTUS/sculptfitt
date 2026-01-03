from __future__ import annotations

from typing import Any
from .db import get_conn


def _get_or_create_exercise(cur, name: str, muscle_group: str | None = None) -> int:
    cur.execute("SELECT id FROM exercises WHERE name=%s LIMIT 1;", (name,))
    row = cur.fetchone()
    if row:
        return int(row["id"])

    cur.execute(
        "INSERT INTO exercises (name, primary_muscle, difficulty) VALUES (%s, %s, %s);",
        (name, muscle_group or "custom", 'beginner'),
    )
    return int(cur.lastrowid)


def ensure_editable_copy(saved_id: int, clerk_user_id: str) -> int:
    """
    Ensures user_saved_plans.user_plan_id exists. If not, clones from shared plan tables.
    Also handles AI-generated plans that are already in user_workout_plans.
    Returns user_plan_id.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            # First check if this is an AI-generated plan (directly in user_workout_plans)
            cur.execute(
                """
                SELECT id FROM user_workout_plans
                WHERE id=%s AND clerk_user_id=%s
                LIMIT 1;
                """,
                (saved_id, clerk_user_id),
            )
            ai_plan = cur.fetchone()
            if ai_plan:
                # It's already an AI-generated editable plan
                return int(ai_plan["id"])
            
            # Otherwise, check user_saved_plans
            cur.execute(
                """
                SELECT usp.id, usp.plan_id, usp.user_plan_id,
                       wp.name AS plan_name, wp.days_per_week, wp.primary_focus
                FROM user_saved_plans usp
                JOIN workout_plans wp ON wp.id = usp.plan_id
                WHERE usp.id=%s AND usp.clerk_user_id=%s
                LIMIT 1;
                """,
                (saved_id, clerk_user_id),
            )
            saved = cur.fetchone()
            if not saved:
                raise ValueError("Plan not found")

            if saved.get("user_plan_id"):
                return int(saved["user_plan_id"])

            source_plan_id = int(saved["plan_id"])

            # Create user_workout_plans
            cur.execute(
                """
                INSERT INTO user_workout_plans
                  (clerk_user_id, source_plan_id, name, days_per_week, primary_focus)
                VALUES (%s, %s, %s, %s, %s);
                """,
                (
                    clerk_user_id,
                    source_plan_id,
                    saved["plan_name"],
                    int(saved["days_per_week"]),
                    saved["primary_focus"],
                ),
            )
            user_plan_id = int(cur.lastrowid)

            # Clone days and exercises directly from plan_exercises
            # Get unique days for this plan
            cur.execute(
                """
                SELECT DISTINCT day_number FROM plan_exercises 
                WHERE plan_id=%s 
                ORDER BY day_number ASC;
                """,
                (source_plan_id,),
            )
            day_numbers = [row["day_number"] for row in cur.fetchall()]

            day_id_map: dict[int, int] = {}
            
            for day_num in day_numbers:
                cur.execute(
                    """
                    INSERT INTO user_workout_days (user_plan_id, day_number, title)
                    VALUES (%s, %s, %s);
                    """,
                    (
                        user_plan_id,
                        int(day_num),
                        f"Day {int(day_num)}",
                    ),
                )
                day_id_map[int(day_num)] = int(cur.lastrowid)

            # Clone items from plan_exercises
            for day_num, user_day_id in day_id_map.items():
                cur.execute(
                    """
                    SELECT exercise_id, sets, reps, rest_seconds, position
                    FROM plan_exercises
                    WHERE plan_id=%s AND day_number=%s
                    ORDER BY position ASC;
                    """,
                    (source_plan_id, day_num),
                )
                items = cur.fetchall()
                for it in items:
                    cur.execute(
                        """
                        INSERT INTO user_workout_day_items
                          (user_day_id, exercise_id, sets, reps, rest_seconds, position)
                        VALUES (%s, %s, %s, %s, %s, %s);
                        """,
                        (
                            user_day_id,
                            int(it["exercise_id"]),
                            int(it["sets"]),
                            str(it["reps"]),
                            int(it["rest_seconds"]),
                            int(it["position"]),
                        ),
                    )

            # Link saved history row -> user editable copy
            cur.execute(
                "UPDATE user_saved_plans SET user_plan_id=%s WHERE id=%s AND clerk_user_id=%s;",
                (user_plan_id, saved_id, clerk_user_id),
            )

            return user_plan_id


def get_editable_plan(saved_id: int, clerk_user_id: str) -> dict[str, Any]:
    """
    Returns payload with REQUIRED IDs:
      - days[] contains day_id
      - items[] contains item_id
    """
    user_plan_id = ensure_editable_copy(saved_id, clerk_user_id)

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, days_per_week, primary_focus, source_plan_id, created_at, updated_at
                FROM user_workout_plans
                WHERE id=%s AND clerk_user_id=%s
                LIMIT 1;
                """,
                (user_plan_id, clerk_user_id),
            )
            plan = cur.fetchone()
            if not plan:
                raise ValueError("Plan not found")

            cur.execute(
                """
                SELECT id, day_number, title
                FROM user_workout_days
                WHERE user_plan_id=%s
                ORDER BY day_number ASC;
                """,
                (user_plan_id,),
            )
            days = cur.fetchall()

            out_days = []
            for d in days:
                user_day_id = int(d["id"])

                cur.execute(
                    """
                    SELECT uwdi.id AS item_id,
                           e.id AS exercise_id,
                           e.name AS exercise,
                           e.muscle_group,
                           uwdi.sets, uwdi.reps, uwdi.rest_seconds, uwdi.position, uwdi.notes
                    FROM user_workout_day_items uwdi
                    JOIN exercises e ON e.id = uwdi.exercise_id
                    WHERE uwdi.user_day_id=%s
                    ORDER BY uwdi.position ASC;
                    """,
                    (user_day_id,),
                )
                items = cur.fetchall()

                out_days.append(
                    {
                        "day_id": user_day_id,                 # ✅ REQUIRED
                        "day": int(d["day_number"]),
                        "title": d.get("title") or "",
                        "items": items,                         # ✅ has item_id
                    }
                )

            return {"plan": plan, "days": out_days}


def update_day_title(user_day_id: int, clerk_user_id: str, title: str) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE user_workout_days d
                JOIN user_workout_plans p ON p.id = d.user_plan_id
                SET d.title=%s
                WHERE d.id=%s AND p.clerk_user_id=%s;
                """,
                (title, user_day_id, clerk_user_id),
            )
            if cur.rowcount == 0:
                raise ValueError("Day not found")


def add_day_item(
    user_day_id: int,
    clerk_user_id: str,
    *,
    exercise_name: str,
    muscle_group: str | None,
    sets: int,
    reps: str,
    rest_seconds: int,
) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Ensure day belongs to user
            cur.execute(
                """
                SELECT d.id
                FROM user_workout_days d
                JOIN user_workout_plans p ON p.id=d.user_plan_id
                WHERE d.id=%s AND p.clerk_user_id=%s
                LIMIT 1;
                """,
                (user_day_id, clerk_user_id),
            )
            if not cur.fetchone():
                raise ValueError("Day not found")

            ex_id = _get_or_create_exercise(cur, exercise_name, muscle_group)

            cur.execute(
                "SELECT COALESCE(MAX(position), 0) AS m FROM user_workout_day_items WHERE user_day_id=%s;",
                (user_day_id,),
            )
            m = int(cur.fetchone()["m"] or 0)
            pos = m + 10

            cur.execute(
                """
                INSERT INTO user_workout_day_items
                  (user_day_id, exercise_id, sets, reps, rest_seconds, position)
                VALUES (%s, %s, %s, %s, %s, %s);
                """,
                (user_day_id, ex_id, int(sets), str(reps), int(rest_seconds), pos),
            )
            return int(cur.lastrowid)


def update_day_item(item_id: int, clerk_user_id: str, patch: dict[str, Any]) -> None:
    allowed = {"exercise_name", "muscle_group", "sets", "reps", "rest_seconds", "notes"}
    patch = {k: v for k, v in patch.items() if k in allowed}
    if not patch:
        return

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT uwdi.id, uwdi.exercise_id
                FROM user_workout_day_items uwdi
                JOIN user_workout_days d ON d.id=uwdi.user_day_id
                JOIN user_workout_plans p ON p.id=d.user_plan_id
                WHERE uwdi.id=%s AND p.clerk_user_id=%s
                LIMIT 1;
                """,
                (item_id, clerk_user_id),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("Item not found")

            exercise_id = int(row["exercise_id"])
            if patch.get("exercise_name") is not None:
                exercise_id = _get_or_create_exercise(
                    cur,
                    str(patch["exercise_name"]),
                    patch.get("muscle_group"),
                )

            cur.execute(
                """
                UPDATE user_workout_day_items
                SET exercise_id=%s,
                    sets=COALESCE(%s, sets),
                    reps=COALESCE(%s, reps),
                    rest_seconds=COALESCE(%s, rest_seconds),
                    notes=COALESCE(%s, notes)
                WHERE id=%s;
                """,
                (
                    exercise_id,
                    patch.get("sets"),
                    patch.get("reps"),
                    patch.get("rest_seconds"),
                    patch.get("notes"),
                    item_id,
                ),
            )


def delete_day_item(item_id: int, clerk_user_id: str) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE uwdi
                FROM user_workout_day_items uwdi
                JOIN user_workout_days d ON d.id=uwdi.user_day_id
                JOIN user_workout_plans p ON p.id=d.user_plan_id
                WHERE uwdi.id=%s AND p.clerk_user_id=%s;
                """,
                (item_id, clerk_user_id),
            )
            if cur.rowcount == 0:
                raise ValueError("Item not found")


def reorder_day_items(user_day_id: int, clerk_user_id: str, ordered_item_ids: list[int]) -> None:
    if not ordered_item_ids:
        return

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT d.id
                FROM user_workout_days d
                JOIN user_workout_plans p ON p.id=d.user_plan_id
                WHERE d.id=%s AND p.clerk_user_id=%s
                LIMIT 1;
                """,
                (user_day_id, clerk_user_id),
            )
            if not cur.fetchone():
                raise ValueError("Day not found")

            for idx, item_id in enumerate(ordered_item_ids, start=1):
                cur.execute(
                    """
                    UPDATE user_workout_day_items
                    SET position=%s
                    WHERE id=%s AND user_day_id=%s;
                    """,
                    (idx * 10, int(item_id), int(user_day_id)),
                )
