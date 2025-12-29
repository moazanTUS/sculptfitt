import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from backend.db import get_conn

with get_conn() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT DATABASE() AS db, NOW() AS now;")
        print(cur.fetchone())
        cur.execute("SELECT COUNT(*) AS c FROM workout_plans;")
        print(cur.fetchone())
