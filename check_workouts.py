from backend.db import get_conn

try:
    conn = get_conn()
    with conn.cursor() as cur:
        # Check custom_workouts data
        cur.execute("SELECT COUNT(*) as count FROM custom_workouts")
        count = cur.fetchone()['count']
        print(f'Custom workouts in database: {count}')
        
        if count > 0:
            cur.execute("SELECT id, clerk_user_id, name, difficulty FROM custom_workouts LIMIT 5")
            workouts = cur.fetchall()
            print('\nWorkouts:')
            for w in workouts:
                print(f"  ID: {w['id']}, User: {w['clerk_user_id']}, Name: {w['name']}, Difficulty: {w['difficulty']}")
                
                # Check exercises for this workout
                cur.execute("""
                    SELECT COUNT(*) as count FROM custom_workout_days 
                    WHERE custom_workout_id = %s
                """, (w['id'],))
                day_count = cur.fetchone()['count']
                print(f"    Days: {day_count}")
        else:
            print("\nNo custom workouts found in database!")
            
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
