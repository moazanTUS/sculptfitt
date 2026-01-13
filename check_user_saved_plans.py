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
        # Check if table exists
        cur.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'user_saved_plans'
        """, (DB_NAME,))
        table_exists = cur.fetchone()
        
        if not table_exists:
            print("❌ TABLE DOES NOT EXIST: user_saved_plans")
        else:
            print("✅ Table exists: user_saved_plans")
        
        # Check table structure
        print("\n=== TABLE STRUCTURE ===")
        cur.execute("DESCRIBE user_saved_plans;")
        columns = cur.fetchall()
        if columns:
            for col in columns:
                print(f"  {col['Field']}: {col['Type']} (NULL: {col['Null']}, Key: {col['Key']}, Default: {col['Default']})")
        else:
            print("❌ No columns found!")
        
        # Check table rows
        print("\n=== TABLE CONTENT ===")
        cur.execute("SELECT COUNT(*) as count FROM user_saved_plans;")
        count_result = cur.fetchone()
        row_count = count_result['count'] if count_result else 0
        print(f"Total rows: {row_count}")
        
        if row_count > 0:
            cur.execute("SELECT * FROM user_saved_plans LIMIT 5;")
            rows = cur.fetchall()
            print("\nFirst few rows:")
            for row in rows:
                print(f"  {row}")
        else:
            print("❌ TABLE IS EMPTY - No saved plans")
        
    conn.close()
    print("\n✅ Connection successful!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
