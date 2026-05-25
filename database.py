import sqlite3

conn = sqlite3.connect("tasks.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT,
    status TEXT
)
""")

conn.commit()


def add_task(user_id, title):

    cursor.execute(
        "INSERT INTO tasks (user_id, title, status) VALUES (?, ?, ?)",
        (user_id, title, "🆕")
    )

    conn.commit()


def get_tasks(user_id):
    cursor.execute(
        "SELECT id, title, status FROM tasks WHERE user_id = ?",
        (user_id,)
    )

    return cursor.fetchall()

def update_task_status(task_id, status):

    cursor.execute(
        "UPDATE tasks SET status = ? WHERE id = ?",
        (status, task_id)
    )

    conn.commit()
