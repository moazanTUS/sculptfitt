from .db import get_conn


def get_available_plans_by_days(days_per_week: int = None):
    """
    Get all available workout plans grouped by focus area.
    If days_per_week is specified (3 or 5), return only plans with that many days.
    Otherwise, return all plans grouped by days_per_week and focus.
    
    Returns:
      {
        "3": [{"id": 1, "name": "...", "primary_focus": "shoulders", "days_per_week": 3}, ...],
        "5": [{"id": 8, "name": "...", "primary_focus": "shoulders", "days_per_week": 5}, ...],
      }
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            if days_per_week:
                cur.execute(
                    """
                    SELECT id, name, primary_focus, days_per_week
                    FROM workout_plans
                    WHERE days_per_week = %s
                    ORDER BY primary_focus, id;
                    """,
                    (days_per_week,),
                )
            else:
                cur.execute(
                    """
                    SELECT id, name, primary_focus, days_per_week
                    FROM workout_plans
                    ORDER BY days_per_week, primary_focus, id;
                    """
                )
            
            plans = cur.fetchall()
            
            # Group by days_per_week
            grouped = {}
            for plan in plans:
                days = str(plan.get("days_per_week", 3))
                if days not in grouped:
                    grouped[days] = []
                grouped[days].append({
                    "id": int(plan["id"]),
                    "name": plan["name"],
                    "primary_focus": plan["primary_focus"],
                    "days_per_week": int(plan["days_per_week"]),
                })
            
            return grouped


def _get_or_create_exercise(cur, name: str, muscle_group: str) -> int:
    cur.execute("SELECT id FROM exercises WHERE name=%s LIMIT 1;", (name,))
    row = cur.fetchone()
    if row:
        return int(row["id"])

    cur.execute(
        "INSERT INTO exercises (name, muscle_group) VALUES (%s, %s);",
        (name, muscle_group),
    )
    return int(cur.lastrowid)

def ensure_plan_in_db(matched_workout: dict) -> int:
    """
    Takes your matched_workout payload:
      {
        "plan": {"id":?, "name":..., "days_per_week":..., "primary_focus":...},
        "days": [{"day": 1, "items":[{exercise,muscle_group,sets,reps,rest_seconds}, ...]}, ...]
      }
    Ensures it's fully stored in DB and returns the DB plan_id.
    """
    plan = matched_workout.get("plan") or {}
    days = matched_workout.get("days") or []

    name = plan.get("name")
    primary_focus = plan.get("primary_focus")
    days_per_week = int(plan.get("days_per_week") or len(days) or 3)

    if not name or not primary_focus:
        raise ValueError("Matched plan missing name/primary_focus")

    with get_conn() as conn:
        with conn.cursor() as cur:
            # 1) Find or create plan by name (unique-ish)
            cur.execute("SELECT id FROM workout_plans WHERE name=%s LIMIT 1;", (name,))
            row = cur.fetchone()
            if row:
                plan_id = int(row["id"])
            else:
                cur.execute(
                    """
                    INSERT INTO workout_plans (name, days_per_week, primary_focus)
                    VALUES (%s, %s, %s);
                    """,
                    (name, days_per_week, primary_focus),
                )
                plan_id = int(cur.lastrowid)

            # 2) Ensure days exist
            # If you want to overwrite existing structure, delete & recreate items/days:
            cur.execute("DELETE FROM workout_day_items WHERE day_id IN (SELECT id FROM workout_days WHERE plan_id=%s);", (plan_id,))
            cur.execute("DELETE FROM workout_days WHERE plan_id=%s;", (plan_id,))

            for d in days:
                day_number = int(d.get("day"))
                cur.execute(
                    "INSERT INTO workout_days (plan_id, day_number, title) VALUES (%s, %s, %s);",
                    (plan_id, day_number, f"Day {day_number}"),
                )
                day_id = int(cur.lastrowid)

                items = d.get("items") or []
                for idx, it in enumerate(items, start=1):
                    ex_name = it.get("exercise")
                    mg = it.get("muscle_group")
                    sets = int(it.get("sets"))
                    reps = str(it.get("reps"))
                    rest = int(it.get("rest_seconds"))

                    ex_id = _get_or_create_exercise(cur, ex_name, mg)

                    cur.execute(
                        """
                        INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position)
                        VALUES (%s, %s, %s, %s, %s, %s);
                        """,
                        (day_id, ex_id, sets, reps, rest, idx),
                    )

            return plan_id
