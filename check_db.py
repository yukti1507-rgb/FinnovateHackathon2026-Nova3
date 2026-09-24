import sqlite3

conn = sqlite3.connect('DATA/database.db')

print("=== Tables in database ===")
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print(tables)

print("\n=== Users table contents ===")
try:
    users = conn.execute("SELECT * FROM users").fetchall()
    print(users)
except Exception as e:
    print(f"Error reading users table: {e}")

conn.close()
