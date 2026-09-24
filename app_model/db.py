import sqlite3

def get_connection():
    conn = sqlite3.connect('DATA/database.db', check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def delete_table(conn, table_name):
    cur = conn.cursor()
    sql = f'DROP TABLE IF EXISTS "{table_name}"'
    cur.execute(sql)
    conn.commit()
    print(f"Table {table_name} deleted successfully.")
#just in case you add the wrong table