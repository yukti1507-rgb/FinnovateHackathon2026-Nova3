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

def alter_user_profile_table(conn):
    """Adding new column without having to delete the existing tables to start again."""
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(user_profile)")
    existing_cols = [col[1] for col in cur.fetchall()]

    if 'occupation' not in existing_cols:
        cur.execute('ALTER TABLE user_profile ADD COLUMN occupation TEXT')

    if 'living_situation' not in existing_cols:
        cur.execute('ALTER TABLE user_profile ADD COLUMN living_situation TEXT')

    if 'dependants' not in existing_cols:
        cur.execute('ALTER TABLE user_profile ADD COLUMN dependants TEXT')

    if 'financial_experience' not in existing_cols:
        cur.execute('ALTER TABLE user_profile ADD COLUMN financial_experience TEXT')

    if 'personalisation_enabled' not in existing_cols:
        cur.execute(
            'ALTER TABLE user_profile ADD COLUMN personalisation_enabled BOOLEAN DEFAULT 0'
        )

    if 'profile_pic' not in existing_cols:
        cur.execute('ALTER TABLE user_profile ADD COLUMN profile_pic TEXT')

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

def create_income_table(conn):
    """
    Stores the user's income sources and amounts.

    IMPORTANT:
    Monetary values are converted to integer cents first,
    then encrypted before being stored in SQLite.

    Example:
        MUR 1,250.50 -> 125050
        MUR 500.00   -> 50000

    The value is converted back to a decimal only when displayed
    to the user.
    """
    cur = conn.cursor()

    sql = '''
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            source TEXT NOT NULL,
            currency TEXT DEFAULT 'MUR',
            amount_encrypted TEXT NOT NULL,
            frequency TEXT NOT NULL
                CHECK (
                    frequency IN (
                        'daily',
                        'weekly',
                        'monthly',
                        'yearly'
                    )
                ),
            FOREIGN KEY (user_id)
                REFERENCES users_login(id)
                ON DELETE CASCADE
        )
    '''

    cur.execute(sql)
    conn.commit()

def create_expenses_table(conn):
    """
    Stores recurring or regular user expenses.

    Monetary values are converted to integer cents first,
    then encrypted before being stored in SQLite.

    frequency controls how often the expense occurs.
    """
    cur = conn.cursor()

    sql = '''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            currency TEXT DEFAULT 'MUR',
            amount_encrypted TEXT NOT NULL,
            frequency TEXT NOT NULL
                CHECK (
                    frequency IN (
                        'daily',
                        'weekly',
                        'monthly',
                        'yearly'
                    )
                ),
            expense_type TEXT DEFAULT 'Need'
                CHECK (
                    expense_type IN (
                        'Need',
                        'Want'
                    )
                ),
            FOREIGN KEY (user_id)
                REFERENCES users_login(id)
                ON DELETE CASCADE
        )
    '''

    cur.execute(sql)
    conn.commit()

def create_loans_table(conn):
    """
    Stores the user's loans.

    Monetary values are converted to integer cents first,
    then encrypted before being stored in SQLite.
    """

    cur = conn.cursor()

    sql = '''
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            currency TEXT DEFAULT 'MUR',
            principal_encrypted TEXT NOT NULL,
            interest_rate REAL DEFAULT 0,
            monthly_payment_encrypted TEXT NOT NULL,
            FOREIGN KEY (user_id)
                REFERENCES users_login(id)
                ON DELETE CASCADE
        )
    '''

    cur.execute(sql)
    conn.commit()
    
def create_savings_table(conn):
    """
    Stores the user's savings information.

    Monetary values are converted to integer cents first,
    then encrypted before being stored in SQLite.
    """
    cur = conn.cursor()

    sql = '''
        CREATE TABLE IF NOT EXISTS savings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            current_savings_encrypted TEXT,
            monthly_savings_encrypted TEXT,
            savings_rate REAL DEFAULT 0,
            currency TEXT DEFAULT 'MUR',
            FOREIGN KEY (user_id)
                REFERENCES users_login(id)
                ON DELETE CASCADE
        )
    '''

    cur.execute(sql)
    conn.commit()

def create_financial_goals_table(conn):
    """
    Stores the user's financial goals.

    All monetary values are converted to integer cents first,
    then encrypted before being stored in SQLite.

    status:
        in_progress
        achieved
        postponed
    """
    cur = conn.cursor()

    sql = '''
        CREATE TABLE IF NOT EXISTS financial_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            goal_name TEXT NOT NULL,
            currency TEXT DEFAULT 'MUR',
            target_amount_encrypted TEXT NOT NULL,
            current_amount_encrypted TEXT,
            target_date DATE,
            priority INTEGER DEFAULT 0
                CHECK (priority >= 0),
            status TEXT DEFAULT 'in_progress'
                CHECK (
                    status IN (
                        'in_progress',
                        'achieved',
                        'postponed'
                    )
                ),
            FOREIGN KEY (user_id)
                REFERENCES users_login(id)
                ON DELETE CASCADE
        )
    '''

    cur.execute(sql)
    conn.commit()

def create_all_tables(conn):
    """
    Creates all database tables required by the application.

    Running this function multiple times is safe because
    the individual table functions use CREATE TABLE IF NOT EXISTS.
    """

    create_user_table(conn)
    alter_users_login_table(conn)

    create_user_profile(conn)
    alter_user_profile_table(conn)

    create_audit_table(conn)

    create_income_table(conn)
    create_expenses_table(conn)
    create_loans_table(conn)
    create_savings_table(conn)
    create_financial_goals_table(conn)