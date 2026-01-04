#!/usr/bin/env python3
from backend.db import get_conn

conn = get_conn()
with conn.cursor() as cur:
    cur.execute("SET FOREIGN_KEY_CHECKS = 0")
    cur.execute("DELETE FROM migrations WHERE name IN ('005_video_library.sql', '006_populate_video_library.sql')")
    cur.execute("DELETE FROM exercise_videos")
    cur.execute("DELETE FROM exercises")
    cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()
    print("✅ Reset complete - migrations cleared and tables emptied")
