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
            # Get AI-generated user plans
            cur.execute(
                """
                SELECT CONCAT('ai_', uwp.id) as id, uwp.created_at, NULL as body_type, uwp.primary_focus as focus1, NULL as focus2, NULL as focus3,
                       uwp.id as user_plan_id,
                       uwp.id AS plan_id, uwp.name AS plan_name, uwp.primary_focus, uwp.days_per_week,
                       'ai' as plan_type
                FROM user_workout_plans uwp
                WHERE uwp.clerk_user_id = %s
                ORDER BY uwp.created_at DESC;
                """,
                (clerk_user_id,),
            )
            user_plans = list(cur.fetchall())
            
            # Get custom user-created workouts
            cur.execute(
                """
                SELECT CONCAT('custom_', cw.id) as id, cw.created_at, NULL as body_type, cw.name as focus1, cw.description as focus2, NULL as focus3,
                       cw.id as user_plan_id,
                       cw.id AS plan_id, cw.name AS plan_name, cw.name as primary_focus, cw.days_per_week,
                       'custom' as plan_type
                FROM custom_workouts cw
                WHERE cw.clerk_user_id = %s
                ORDER BY cw.created_at DESC;
                """,
                (clerk_user_id,),
            )
            custom_workouts = list(cur.fetchall())
            
            # Combine all lists
            all_plans = user_plans + custom_workouts
            return sorted(all_plans, key=lambda x: x.get('created_at'), reverse=True)


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


# DEPRECATED: Old function for pre-built plans (no longer used)
# def get_plan_days(plan_id: int):
#     """
#     Read-only view of template plan days from shared tables.
#     (Editing uses /api/my-plans/{id}/editable instead.)
#     """
#     # This used to read from workout_days which no longer exists
#     # Plans now use plan_exercises directly


def delete_user_plan(saved_id: str, clerk_user_id: str) -> bool:
    """
    Delete a saved plan (from user_saved_plans), AI-generated plan (from user_workout_plans),
    or custom workout (from custom_workouts).
    Also cascade-delete the editable copy (user_workout_plans) if it exists.
    Returns True if deleted, False if not found.
    
    saved_id is composite: 'custom_123', 'ai_456', 'saved_789'
    """
    # Parse the composite ID
    if saved_id.startswith('custom_'):
        plan_type = 'custom'
        actual_id = int(saved_id.split('_')[1])
    elif saved_id.startswith('ai_'):
        plan_type = 'ai'
        actual_id = int(saved_id.split('_')[1])
    elif saved_id.startswith('saved_'):
        plan_type = 'saved'
        actual_id = int(saved_id.split('_')[1])
    else:
        # Fallback for backward compatibility
        plan_type = 'ai'
        actual_id = int(saved_id)
    
    with get_conn() as conn:
        with conn.cursor() as cur:
            if plan_type == 'custom':
                # Delete custom workout
                cur.execute(
                    """
                    DELETE FROM custom_workouts
                    WHERE id = %s AND clerk_user_id = %s;
                    """,
                    (actual_id, clerk_user_id),
                )
                if cur.rowcount > 0:
                    conn.commit()
                    return True
                return False
                
            elif plan_type == 'ai':
                # Delete AI-generated plan
                cur.execute(
                    """
                    DELETE FROM user_workout_plans
                    WHERE id = %s AND clerk_user_id = %s;
                    """,
                    (actual_id, clerk_user_id),
                )
                
                if cur.rowcount > 0:
                    conn.commit()
                    return True
                return False
            
            else:  # plan_type == 'saved'
                # Delete saved pre-built plan
                # Get the user_plan_id (editable copy) if it exists
                cur.execute(
                    """
                    SELECT user_plan_id FROM user_saved_plans
                    WHERE id = %s AND clerk_user_id = %s
                    LIMIT 1;
                    """,
                    (actual_id, clerk_user_id),
                )
                row = cur.fetchone()
                if not row:
                    return False

                user_plan_id = row.get("user_plan_id")

                # Delete the saved plan record
                cur.execute(
                    "DELETE FROM user_saved_plans WHERE id = %s AND clerk_user_id = %s;",
                    (actual_id, clerk_user_id),
                )

                # If there was an editable copy, delete it too (cascade)
                if user_plan_id:
                    cur.execute("DELETE FROM user_workout_plans WHERE id = %s AND clerk_user_id = %s;",
                               (user_plan_id, clerk_user_id))

                conn.commit()
                return True
