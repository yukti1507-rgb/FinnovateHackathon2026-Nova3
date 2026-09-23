#creating table
def create_user_table(conn):
    cur = conn.cursor()
    sql = '''CREATE TABLE IF NOT EXISTS users_login (        
    id INTEGER PRIMARY KEY AUTOINCREMENT,        
    username TEXT NOT NULL UNIQUE,        
    password_hash TEXT NOT NULL,
    failed_attempts INTEGER DEFAULT 0,
    locked BOOLEAN DEFAULT 0,
    token TEXT,
    token_expiry TEXT);'''
    cur.execute(sql)
    conn.commit()

def create_user_profile(conn):
    cur = conn.cursor()
    sql = '''CREATE TABLE IF NOT EXISTS user_profile (
    user_id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    avatar TEXT,
    background_color TEXT,
    role TEXT DEFAULT "user",
    FOREIGN KEY (user_id) REFERENCES users_login(id) ON DELETE CASCADE);'''
    cur.execute(sql)
    conn.commit()

def alter_users_login_table(conn):
    """Adding new column without having to delete the existing tables to start again."""
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(users_login)")
    existing_cols = [col[1] for col in cur.fetchall()]

    if 'lockout_count' not in existing_cols:
        cur.execute('ALTER TABLE users_login ADD COLUMN lockout_count INTEGER DEFAULT 0')

    if 'last_login_time' not in existing_cols:
        cur.execute('ALTER TABLE users_login ADD COLUMN last_login_time TEXT')
    conn.commit()

def create_audit_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            admin_id INTEGER,
            action TEXT NOT NULL,
            description TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

def delete_column(conn, column_name):
    cur = conn.cursor()
    sql = f'ALTER TABLE users DROP COLUMN {column_name}'
    cur.execute(sql)
    conn.commit()