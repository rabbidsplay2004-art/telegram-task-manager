import sqlite3

conn = sqlite3.connect("tasks.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT,
    status TEXT,
    assignee_id INTEGER,
    deadline TEXT
)
""")

conn.commit()


def add_task(
    user_id,
    title,
    assignee_id,
    deadline
):

    cursor.execute(
        """
        INSERT INTO tasks (
            user_id,
            title,
            status,
            assignee_id,
            deadline
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            title,
            "🆕",
            assignee_id,
            deadline
        )
    )

    conn.commit()

def get_tasks(user_id):
    cursor.execute(
        "SELECT id, title, status, assignee_id, deadline FROM tasks WHERE user_id = ?",
        (user_id,)
    )

    return cursor.fetchall()

def update_task_status(task_id, status):

    cursor.execute(
        "UPDATE tasks SET status = ? WHERE id = ?",
        (status, task_id)
    )

    conn.commit()
