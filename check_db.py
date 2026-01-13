#!/usr/bin/env python3
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")
DB_NAME = os.getenv("DB_NAME", "sculpfit")
DB_PORT = int(os.getenv("DB_PORT", "3306"))

try:
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS if DB_PASS else None,
        database=DB_NAME,
        port=DB_PORT,
        cursorclass=pymysql.cursors.DictCursor,
    )
    
    with conn.cursor() as cur:
        # Check exercises table structure
        cur.execute("DESCRIBE exercises;")
        columns = cur.fetchall()
        
        print("\n=== EXERCISES TABLE STRUCTURE ===")
        for col in columns:
            print(f"  {col['Field']}: {col['Type']} (NULL: {col['Null']}, Key: {col['Key']}, Default: {col['Default']})")
        
        # Check if primary_muscle exists
        muscle_cols = [c for c in columns if 'muscle' in c['Field'].lower()]
        print(f"\n=== MUSCLE COLUMNS ===")
        print(f"Columns with 'muscle' in name: {[c['Field'] for c in muscle_cols]}")
        
    conn.close()
    print("\n✅ Connection successful!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
