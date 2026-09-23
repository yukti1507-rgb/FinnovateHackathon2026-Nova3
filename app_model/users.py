import sqlite3
import secrets
from datetime import datetime, timedelta

#insert
def add_user(conn, name, hash, email):
    cur = conn.cursor()
    try:
        cur.execute(
            'INSERT INTO users_login (username, password_hash) VALUES (?, ?)',
            (name, hash)
        )
        user_id = cur.lastrowid
        cur.execute(
            'INSERT INTO user_profile (user_id, email) VALUES (?, ?)',
            (user_id, email)
        )
        conn.commit()
        print("User was successfully entered.")
    except sqlite3.IntegrityError:
        conn.rollback()
        print("This username or email already exists")

#adding users from user.txt to the db
def migrate_users(conn):
    with open ("DATA/users.txt", "r") as f:
        users = f.readlines()

    for user in users:
        name, hash, email = user.strip().split(",")
        add_user(conn, name, hash, email) 

#reading the entire db
def get_all_users(conn):
    cur = conn.cursor()
    sql = 'SELECT * FROM users_login'
    cur.execute(sql)
    users = cur.fetchall()
    return(users)

#read just one user based on name
def get_user(conn, name):
    cur = conn.cursor()
    sql = '''SELECT id, username, password_hash, failed_attempts, locked FROM users_login WHERE username = ?'''
    cur.execute(sql, (name,))
    return cur.fetchone()

#update username
def update_user(conn, new_username, old_username):
    cur = conn.cursor()
    sql = 'UPDATE users_login SET username = ? WHERE username = ? '
    param = ( new_username, old_username)
    try:
        cur.execute(sql, param)
        conn.commit()
        print("Successfully updated.")
    except sqlite3.IntegrityError:
        print("This username already exists.")

#increments the failed attempts and locked(if necessary) when the user is logging in
def update_login_attempts(conn, name):
    cur = conn.cursor()
    sql = 'UPDATE users_login SET failed_attempts = failed_attempts + 1 WHERE username = ?'
    param = (name,)
    cur.execute(sql, param)
    conn.commit()

    sql = 'SELECT failed_attempts FROM users_login WHERE username = ?'
    param = (name,)
    cur.execute(sql, param)
    no_attempts = cur.fetchone()[0]
    
    if no_attempts >= 3:
        sql = "UPDATE users_login SET  locked = 1, lockout_count = lockout_count + 1 WHERE username = ?"
        param = (name,)
        cur.execute(sql, param)
        conn.commit()
        print("Account locked after 3 failed attempts.")

#checks if the username is unique
def is_username_available(conn, name):
    """Checks if the username already exists in the db"""
    return get_user(conn, name) is None

#checks if the email is unique
def is_email_available(conn, email):
    cur = conn.cursor()
    sql = 'SELECT user_id FROM user_profile WHERE email = ?'
    cur.execute(sql, (email,))
    return cur.fetchone() is None

#gets the email based on username
def get_email(conn, username):
    cur = conn.cursor()
    sql = '''
        SELECT p.email FROM user_profile p
        JOIN users_login u ON p.user_id = u.id
        WHERE u.username = ?
    '''
    cur.execute(sql, (username,))
    result = cur.fetchone()
    return result[0] if result and result[0] else None

#resets the failed attempts during login and if user resets password
def reset_login(conn, name):
    cur = conn.cursor()
    sql = "UPDATE users_login SET failed_attempts = 0, locked = 0 WHERE username = ?"
    cur.execute(sql, (name,))
    conn.commit()

#delete user
def delete_user(conn, name):
    cur = conn.cursor()
    sql = 'DELETE FROM users_login WHERE username = ?'
    param = (name,)
    cur.execute(sql, param)
    conn.commit()

def set_token(conn, email):
    cur = conn.cursor()
    sql = '''
        SELECT u.username FROM users_login u
        JOIN user_profile p ON u.id = p.user_id
        WHERE p.email = ?
    '''
    cur.execute(sql, (email,))
    result = cur.fetchone()
    if result is None:
        return None
    username = result[0]

    token = secrets.token_urlsafe(16)
    expiry = (datetime.now() + timedelta(minutes=15)).isoformat()

    sql = 'UPDATE users_login SET token = ?, token_expiry = ? WHERE username = ?'
    cur.execute(sql, (token, expiry, username))
    conn.commit()
    return token


def get_user_by_token(conn, token):
    cur = conn.cursor()
    sql = 'SELECT username, token_expiry FROM users_login WHERE token = ?'
    param = (token,)
    cur.execute(sql, param)

    result = cur.fetchone()
    if result is None:
        return None  
    else:
        username, expiry_str = result
        expiry = datetime.fromisoformat(expiry_str)
        if datetime.now() > expiry:
            return None  
        else:
            return username
    
#allows user to reset their password - functionality used in profile dashboard and in 'forgot password' button
def reset_password(conn, name, new_hash):
    cur = conn.cursor()
    sql = 'UPDATE users_login SET password_hash = ?, token = NULL, token_expiry = NULL, failed_attempts = 0, locked = 0 WHERE username = ?'
    param = (new_hash, name)
    cur.execute(sql, param)
    conn.commit()

#allows user to update their avatar 
def update_avatar(conn, name, avatar):
    cur = conn.cursor()
    sql = '''
        UPDATE user_profile SET avatar = ?
        WHERE user_id = (SELECT id FROM users_login WHERE username = ?)
    '''
    cur.execute(sql, (avatar, name))
    conn.commit()

#returns the role of the user
def get_role(conn, username):
    cur = conn.cursor()
    sql = '''
        SELECT p.role FROM user_profile p
        JOIN users_login u ON p.user_id = u.id
        WHERE u.username = ?
    '''
    cur.execute(sql, (username,))
    result = cur.fetchone()
    return result[0] if result else None

#allows users to update their email 
def update_email(conn, name, email):
    cur = conn.cursor()
    sql = '''
        UPDATE user_profile SET email = ?
        WHERE user_id = (SELECT id FROM users_login WHERE username = ?)
    '''
    cur.execute(sql, (email, name))
    conn.commit()

#used to display the users username and email in profile dashboard
def get_user_info(conn, name):
    cur = conn.cursor()
    sql = '''
        SELECT u.username, p.email FROM users_login u
        JOIN user_profile p ON u.id = p.user_id
        WHERE u.username = ?
    '''
    cur.execute(sql, (name,))
    return cur.fetchone()

#feature for user to delete their account
def delete_one_user(conn, name):
    cur = conn.cursor()
    cur.execute('''
        DELETE FROM user_profile
        WHERE user_id = (SELECT id FROM users_login WHERE username = ?)
    ''', (name,))
    cur.execute('DELETE FROM users_login WHERE username = ?', (name,))
    conn.commit()

#delete entire db - code used if intialisation of db is needed but this feature is not accessible to anyone but the programmer - it is not a feature found in the streamlit
def delete_db(conn):
    cur = conn.cursor()
    cur.execute("DELETE FROM users_login")
    conn.commit()

#get the users theme colour
def get_user_theme(conn, username):
    cur = conn.cursor()
    sql = '''
        SELECT p.background_color FROM user_profile p
        JOIN users_login u ON p.user_id = u.id
        WHERE u.username = ?
    '''
    cur.execute(sql, (username,))
    result = cur.fetchone()
    return result[0] if result and result[0] else "Light Mode"

#change the theme colour
def update_background(conn, username, color):
    cur = conn.cursor()
    sql = '''
        UPDATE user_profile SET background_color = ?
        WHERE user_id = (SELECT id FROM users_login WHERE username = ?)
    '''
    cur.execute(sql, (color, username))
    conn.commit()

def set_admin(conn, username):
    cur = conn.cursor()
    sql = '''
        UPDATE user_profile SET role = "Admin"
        WHERE user_id = (SELECT id FROM users_login WHERE username = ?)
    '''
    cur.execute(sql, (username,))
    conn.commit()

def record_time_login(conn, name):
    cur = conn.cursor()
    login_time = datetime.now().isoformat()
    sql = ''' UPDATE users_login SET last_login_time = ? WHERE username = ?'''
    param = (login_time, name)
    cur.execute(sql, param)
    conn.commit()

def get_login_stats(conn, name):
    cur = conn.cursor()
    sql = '''SELECT lockout_count, last_login_time FROM users_login WHERE username = ?'''
    param = (name,)
    cur.execute(sql, param)
    result = cur.fetchone()
    if result:
        return {"lockout_count": result[0], "last_login_time" : result[1]}
    return None

