import sqlite3

def create_database():
    conn = sqlite3.connect('prompts.db')
    cursor = conn.cursor()

    # User Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        discord_username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')

    # Prompt Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prompts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        upvotes INTEGER DEFAULT 0,
        downvotes INTEGER DEFAULT 0,
        views INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    # Comments Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prompt_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (prompt_id) REFERENCES prompts (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    # Votes Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        prompt_id INTEGER NOT NULL,
        vote INTEGER NOT NULL,
        UNIQUE (user_id, prompt_id),
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (prompt_id) REFERENCES prompts (id)
    )
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database()