from backend.db import get_conn

try:
    conn = get_conn()
    with conn.cursor() as cur:
        # Check if migrations table exists
        cur.execute("SHOW TABLES LIKE 'migrations'")
        migrations_exists = cur.fetchone() is not None
        print(f'Migrations table exists: {migrations_exists}')
        
        # Check if custom_workouts table exists
        cur.execute("SHOW TABLES LIKE 'custom_workouts'")
        custom_workouts_exists = cur.fetchone() is not None
        print(f'Custom workouts table exists: {custom_workouts_exists}')
        
        # Show all tables
        cur.execute('SHOW TABLES')
        tables = cur.fetchall()
        print(f'\nAll tables in database:')
        for table in tables:
            print(f'  - {list(table.values())[0]}')
except Exception as e:
    print(f'Database Error: {e}')
