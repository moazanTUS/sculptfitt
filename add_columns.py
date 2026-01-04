from backend.db import get_conn

conn = get_conn()
cur = conn.cursor()

try:
    cur.execute('ALTER TABLE exercises ADD COLUMN description TEXT')
    print('✅ Added description column')
except Exception as e:
    print(f'❌ Description column: {e}')

try:
    cur.execute('ALTER TABLE exercises ADD COLUMN muscle_group VARCHAR(100)')
    print('✅ Added muscle_group column')
except Exception as e:
    print(f'❌ Muscle group column: {e}')

conn.commit()

# Verify columns exist
cur.execute('SHOW COLUMNS FROM exercises')
cols = cur.fetchall()
col_names = [c['Field'] for c in cols]
print(f'\nColumns in exercises table: {col_names}')
print(f'Has description: {"description" in col_names}')
print(f'Has muscle_group: {"muscle_group" in col_names}')
