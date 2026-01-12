
import sys
import os

print(f"Python version: {sys.version}")

try:
    import flask
    print("Flask imported successfully.")
except ImportError as e:
    print(f"Error importing Flask: {e}")

try:
    import pymysql
    print("PyMySQL imported successfully.")
except ImportError as e:
    print(f"Error importing PyMySQL: {e}")

try:
    import dotenv
    print("python-dotenv imported successfully.")
except ImportError as e:
    print(f"Error importing python-dotenv: {e}")

try:
    import src.db
    print("src.db imported successfully.")
except ImportError as e:
    print(f"Error importing src.db: {e}")

print("Verification complete.")
