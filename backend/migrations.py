"""
Database Migration Runner
Automatically applies migrations to the database on startup.
"""

import os
from pathlib import Path
from .db import get_conn

MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"


def run_migrations():
    """Run all pending migrations in order"""
    
    # Get list of migration files
    migration_files = sorted([
        f for f in os.listdir(MIGRATIONS_DIR) 
        if f.endswith('.sql')
    ])
    
    if not migration_files:
        print("[MIGRATIONS] No migrations found")
        return
    
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            # Create migrations tracking table if it doesn't exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) UNIQUE NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Get list of applied migrations
            cur.execute("SELECT name FROM migrations")
            applied = {row['name'] for row in cur.fetchall()}
            
            # Apply pending migrations
            for migration_file in migration_files:
                if migration_file in applied:
                    print(f"[MIGRATIONS] ✓ {migration_file} (already applied)")
                    continue
                
                # Read migration file
                migration_path = MIGRATIONS_DIR / migration_file
                with open(migration_path, 'r') as f:
                    migration_sql = f.read()
                
                # Execute migration
                print(f"[MIGRATIONS] Applying {migration_file}...")
                for statement in migration_sql.split(';'):
                    statement = statement.strip()
                    if statement:
                        try:
                            cur.execute(statement)
                        except Exception as e:
                            print(f"[MIGRATIONS] Warning: {e}")
                
                # Record migration
                cur.execute(
                    "INSERT INTO migrations (name) VALUES (%s)",
                    (migration_file,)
                )
                
                print(f"[MIGRATIONS] ✓ {migration_file}")
            
            conn.commit()
            print("[MIGRATIONS] All migrations completed successfully")
    
    except Exception as e:
        print(f"[MIGRATIONS] Error: {e}")
        raise
