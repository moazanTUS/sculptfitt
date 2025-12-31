import pymysql
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration from environment variables
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")
DB_NAME = os.getenv("DB_NAME", "sculpfit")
DB_PORT = int(os.getenv("DB_PORT", "3306"))


def get_conn():
    """
    Returns a PyMySQL connection using environment variables.
    DB_PASS can be empty if the database has no password.
    """
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS if DB_PASS else None,
        database=DB_NAME,
        port=DB_PORT,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )
