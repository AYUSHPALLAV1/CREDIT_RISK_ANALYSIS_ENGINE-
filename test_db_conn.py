
import os
from dotenv import load_dotenv
from src.db import get_conn
import pymysql

load_dotenv()

print("Attempting to connect to database...")
try:
    conn = get_conn()
    print("Connection successful!")
    conn.close()
except pymysql.Error as e:
    print(f"Connection failed (as expected if DB not running/configured): {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
