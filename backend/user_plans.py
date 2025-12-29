from .db import get_conn


def save_user_plan(
    clerk_user_id: str,
    plan_id: int,
    body_type: str | None,
    focus_areas: list[str] | None,
) -> int:
    """
    Saves a row into user_saved_plans and returns saved_id.
    """
    fa = (focus_areas or []) + ["", "", ""]
    f1, f2, f3 = fa[0], fa[1], fa[2]

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_saved_plans (clerk_user_id, plan_id, body_type, focus1, focus2, focus3)
                VALUES (%s, %s, %s, %s, %s, %s);
                """,
                (clerk_user_id, plan_id, body_type, f1, f2, f3),
            )
            return int(cur.lastrowid)


def list_user_plans(clerk_user_id: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT usp.id, usp.created_at, usp.body_type, usp.focus1, usp.focus2, usp.focus3,
                       usp.user_plan_id,
                       wp.id AS plan_id, wp.name AS plan_name, wp.primary_focus, wp.days_per_week
                FROM user_saved_plans usp
                JOIN workout_plans wp ON wp.id = usp.plan_id
                WHERE usp.clerk_user_id = %s
                ORDER BY usp.created_at DESC;
                """,
                (clerk_user_id,),
            )
            return cur.fetchall()


def get_saved_plan(saved_id: int, clerk_user_id: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT usp.id, usp.created_at, usp.body_type, usp.focus1, usp.focus2, usp.focus3,
                       usp.user_plan_id,
                       wp.id AS plan_id, wp.name AS plan_name, wp.primary_focus, wp.days_per_week
                FROM user_saved_plans usp
                JOIN workout_plans wp ON wp.id = usp.plan_id
                WHERE usp.id = %s AND usp.clerk_user_id = %s
                LIMIT 1;
                """,
                (saved_id, clerk_user_id),
            )
            return cur.fetchone()


def get_plan_days(plan_id: int):
    """
    Read-only view of template plan days from shared tables.
    (Editing uses /api/my-plans/{id}/editable instead.)
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, day_number FROM workout_days WHERE plan_id=%s ORDER BY day_number ASC;",
                (plan_id,),
            )
            days = cur.fetchall()

            out_days = []
            for d in days:
                cur.execute(
                    """
                    SELECT e.name AS exercise, e.muscle_group, wdi.sets, wdi.reps, wdi.rest_seconds
                    FROM workout_day_items wdi
                    JOIN exercises e ON e.id = wdi.exercise_id
                    WHERE wdi.day_id = %s
                    ORDER BY wdi.position ASC;
                    """,
                    (d["id"],),
                )

                items = cur.fetchall()
                out_days.append({"day": d["day_number"], "items": items})

            return out_days


def delete_user_plan(saved_id: int, clerk_user_id: str) -> bool:
    """
    Delete a saved plan (from user_saved_plans).
    Also cascade-delete the editable copy (user_workout_plans) if it exists.
    Returns True if deleted, False if not found.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Get the user_plan_id (editable copy) if it exists
            cur.execute(
                """
                SELECT user_plan_id FROM user_saved_plans
                WHERE id = %s AND clerk_user_id = %s
                LIMIT 1;
                """,
                (saved_id, clerk_user_id),
            )
            row = cur.fetchone()
            if not row:
                return False

            user_plan_id = row.get("user_plan_id")

            # Delete the saved plan record
            cur.execute(
                "DELETE FROM user_saved_plans WHERE id = %s AND clerk_user_id = %s;",
                (saved_id, clerk_user_id),
            )

            # If there was an editable copy, delete it too (cascade)
            if user_plan_id:
                cur.execute("DELETE FROM user_workout_plans WHERE id = %s AND clerk_user_id = %s;",
                           (user_plan_id, clerk_user_id))

            conn.commit()
            return True

