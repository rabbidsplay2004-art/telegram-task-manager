import sqlite3

conn = sqlite3.connect("tasks.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT
)
""")

conn.commit()


def add_task(user_id, title):
    cursor.execute(
        "INSERT INTO tasks (user_id, title) VALUES (?, ?)",
        (user_id, title)
    )

    conn.commit()


def get_tasks(user_id):
    cursor.execute(
        "SELECT title FROM tasks WHERE user_id = ?",
        (user_id,)
    )

    return cursor.fetchall()
