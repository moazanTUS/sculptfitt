from .db import get_conn

PLAN_EX_SQL = """
SELECT day, exercise_name, muscle_group, sets, reps, rest_seconds, sort_order
FROM plan_exercises
WHERE plan_id = %s
ORDER BY day ASC, sort_order ASC;
"""

def match_plan(focus_areas: list[str], body_type: str = None):
    """
    Match a plan based on focus areas and optional body type.
    
    Args:
        focus_areas: List of focus areas (e.g., ['chest', 'arms', 'legs'])
        body_type: Optional body type ('ectomorph', 'mesomorph', 'endomorph')
    
    Returns:
        Dict with matched plan and exercises, or None if no match found
    """
    # normalize focus areas
    focus = [(str(x).strip().lower()) for x in (focus_areas or []) if x]
    focus = (focus + ["core", "legs", "back"])[:3]
    f1, f2, f3 = focus[0], focus[1], focus[2]
    
    # normalize body type
    body_type = (str(body_type).strip().lower()) if body_type else None
    if body_type not in ('ectomorph', 'mesomorph', 'endomorph'):
        body_type = None

    with get_conn() as conn:
        with conn.cursor() as cur:
            # Try to match with body_type first if provided
            if body_type:
                MATCH_SQL = """
                SELECT id, name, days_per_week, primary_focus, body_type
                FROM workout_plans
                WHERE body_type = %s AND primary_focus IN (%s, %s, %s)
                ORDER BY FIELD(primary_focus, %s, %s, %s)
                LIMIT 1;
                """
                cur.execute(MATCH_SQL, (body_type, f1, f2, f3, f1, f2, f3))
                plan = cur.fetchone()
            
            # Fallback: try any body type or 'all' plans
            if not plan:
                MATCH_SQL = """
                SELECT id, name, days_per_week, primary_focus, body_type
                FROM workout_plans
                WHERE (body_type = 'all' OR body_type IS NULL) AND primary_focus IN (%s, %s, %s)
                ORDER BY FIELD(primary_focus, %s, %s, %s)
                LIMIT 1;
                """
                cur.execute(MATCH_SQL, (f1, f2, f3, f1, f2, f3))
                plan = cur.fetchone()
            
            if not plan:
                return None

            cur.execute(PLAN_EX_SQL, (plan["id"],))
            rows = cur.fetchall()

    # group into days/items exactly how frontend expects
    days_map = {}
    for r in rows:
        d = int(r["day"])
        days_map.setdefault(d, []).append({
            "exercise": r["exercise_name"],
            "muscle_group": r["muscle_group"],
            "sets": r["sets"],
            "reps": r["reps"],
            "rest_seconds": r["rest_seconds"],
        })

    return {
        "plan": plan,
        "days": [{"day": d, "items": days_map[d]} for d in sorted(days_map.keys())]
    }
