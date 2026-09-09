import sqlite3

DATABASE = 'budget_tracker.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            username        TEXT NOT NULL UNIQUE,
            email           TEXT NOT NULL UNIQUE,
            password_hash   TEXT NOT NULL,
            date_registered TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            type        TEXT NOT NULL CHECK(type IN ('income','expense')),
            amount      REAL NOT NULL CHECK(amount > 0),
            category    TEXT NOT NULL,
            description TEXT,
            date        TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()