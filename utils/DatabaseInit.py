import sqlite3

def InitializeDbStruct():
    conn = sqlite3.connect("forum.db")
    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(100) NOT NULL,
        display_name VARCHAR(150) NOT NULL,
        bio TEXT,
        encrypted_password TEXT NOT NULL,
        admin TINYINT(1) NOT NULL DEFAULT 0,
        banned TINYINT(1) NOT NULL DEFAULT 0,
        deleted TINYINT(1) NOT NULL DEFAULT 0,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        avatar_path TEXT DEFAULT 'static/user.png',
        token TEXT NOT NULL
    );""")

    conn.execute("""CREATE TABLE IF NOT EXISTS ip_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usr_name TEXT,
        success TINYINT(1) NOT NULL DEFAULT 0,
        path TEXT NOT NULL,
        ip TEXT NOT NULL,
        timestamp TEXT NOT NULL
    );""")

    conn.execute("""CREATE TABLE IF NOT EXISTS blocked_ip (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip TEXT NOT NULL,
        blocked TINYINT(1) NOT NULL DEFAULT 0
    );""")

    conn.execute("""CREATE TABLE IF NOT EXISTS threads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_username TEXT NOT NULL,
        name VARCHAR(200) NOT NULL,
        identifier VARCHAR(150) NOT NULL,
        description TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        image_url TEXT DEFAULT '/static/AFLOGO.png'
    );""")

    conn.execute("""CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_username TEXT NOT NULL,
        thread_identifier TEXT NOT NULL,
        title VARCHAR(50) NOT NULL,
        content TEXT NOT NULL,
        image_attachment TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );""")

    conn.execute("""CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_username TEXT NOT NULL,
        post_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );""")

    conn.execute("""
    CREATE TABLE IF NOT EXISTS subscribed_threads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        thread_identifier TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS liked_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        post_id TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS liked_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        comment_id TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        resource_id TEXT NOT NULL,
        type_of_report TEXT NOT NULL,
        type_of_resource TEXT NOT NULL,
        additional_info TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()