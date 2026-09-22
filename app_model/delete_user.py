from db import get_connection
from users import set_token

def delete_one_user(conn, name):
    cur = conn.cursor()
    sql = 'DELETE FROM users_login WHERE username = ?'
    param = (name,)
    cur.execute(sql, param)
    conn.commit()

def delete_db(conn):
    cur = conn.cursor()
    cur.execute("DELETE FROM users_login")
    conn.commit()

