import pymysql

# ✅ Hardcoded per your request
DB_HOST = "127.0.0.1"
DB_USER = "root"
DB_PASS = ""              # <-- put password here if your MariaDB user has one
DB_NAME = "sculpfit"
DB_PORT = 3307


def get_conn():
    """
    Returns a PyMySQL connection using hardcoded settings.
    """
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        port=DB_PORT,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )
