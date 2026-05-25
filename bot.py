import asyncio
import os
import sqlite3
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =====================================
# USERS
# =====================================

USERS = {
    807467627: {
        "name": "паньк",
        "role": "admin"
    },

    966721440: {
        "name": "татьянус",
        "role": "user"
    },

    290304196: {
        "name": "максон либовский",
        "role": "user"
    }
}

# =====================================
# DATABASE
# =====================================

conn = sqlite3.connect(
    "tasks.db"
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    status TEXT,
    priority TEXT,
    assignee_id INTEGER,
    deadline TEXT,
    comment TEXT
)
""")

conn.commit()

# =====================================
# DB FUNCTIONS
# =====================================

def add_task(
    title,
    priority,
    assignee_id,
    deadline
):

    cursor.execute(
        """
        INSERT INTO tasks (
            title,
            status,
            priority,
            assignee_id,
            deadline,
            comment
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            title,
            "🆕",
            priority,
            assignee_id,
            deadline,
            ""
        )
    )

    conn.commit()


def get_tasks():

    cursor.execute(
        """
        SELECT * FROM tasks
        ORDER BY deadline ASC
        """
    )

    return cursor.fetchall()


def update_status(task_id, status):

    cursor.execute(
        """
        UPDATE tasks
        SET status = ?
        WHERE id = ?
        """,
        (
            status,
            task_id
        )
    )

    conn.commit()


def update_comment(task_id, comment):

    cursor.execute(
        """
        UPDATE tasks
        SET comment = ?
        WHERE id = ?
        """,
        (
            comment,
            task_id
        )
    )

    conn.commit()

# =====================================
# FSM
# =====================================

class CreateTask(StatesGroup):

    waiting_for_title = State()
    waiting_for_priority = State()
    waiting_for_assignee = State()
    waiting_for_deadline = State()


class AddComment(StatesGroup):

    waiting_for_comment = State()

# =====================================
# MENU
# =====================================

def main_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="📋 Активные задачи",
                    callback_data="all_tasks"
                )
            ],

            [
                InlineKeyboardButton(
                    text="✅ Выполненные",
                    callback_data="done_tasks"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📅 Календарь",
                    callback_data="calendar"
                )
            ],

            [
                InlineKeyboardButton(
                    text="⚠️ Просроченные",
                    callback_data="overdue"
                )
            ],

            [
                InlineKeyboardButton(
                    text="➕ Новая задача",
                    callback_data="new_task"
                )
            ]
        ]
    )

# =====================================
# START
# =====================================

@dp.message(CommandStart())
async def start(message: Message):

    await message.answer(
        "ну привет чертила",
        reply_markup=main_menu()
    )

# =====================================
# CREATE TASK
# =====================================

@dp.callback_query(F.data == "new_task")
async def new_task(
    callback: CallbackQuery,
    state: FSMContext
):

    reply_markup=main_menu()
        "✍️ Введите название задачи"
    )

    await state.set_state(
        CreateTask.waiting_for_title
    )

# =====================================
# TITLE
# =====================================

@dp.message(CreateTask.waiting_for_title)
async def get_title(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        title=message.text
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔴 Высокий",
                    callback_data="priority_high"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🟡 Средний",
                    callback_data="priority_medium"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🟢 Низкий",
                    callback_data="priority_low"
                )
            ]
        ]
    )

    reply_markup=main_menu()
        "🔥 Выберите приоритет",
        reply_markup=keyboard
    )

    await state.set_state(
        CreateTask.waiting_for_priority
    )

# =====================================
# PRIORITY
# =====================================

@dp.callback_query(
    CreateTask.waiting_for_priority,
    F.data.startswith("priority_")
)
async def get_priority(
    callback: CallbackQuery,
    state: FSMContext
):

    priority_map = {

        "priority_high": "🔴 Высокий",
        "priority_medium": "🟡 Средний",
        "priority_low": "🟢 Низкий"
    }

    priority = priority_map[
        callback.data
    ]

    await state.update_data(
        priority=priority
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[]
    )

    for user_id, user_data in USERS.items():

        keyboard.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=user_data["name"],
                    callback_data=f"assign_{user_id}"
                )
            ]
        )

    reply_markup=main_menu()
        "👤 Выберите исполнителя",
        reply_markup=keyboard
    )

    await state.set_state(
        CreateTask.waiting_for_assignee
    )

# =====================================
# ASSIGNEE
# =====================================

@dp.callback_query(
    CreateTask.waiting_for_assignee,
    F.data.startswith("assign_")
)
async def assign_task(
    callback: CallbackQuery,
    state: FSMContext
):

    assignee_id = int(
        callback.data.split("_")[1]
    )

    await state.update_data(
        assignee_id=assignee_id
    )

    reply_markup=main_menu()
        "📅 Введите дедлайн\n\n"
        "Пример:\n"
        "28.05.2026 18:30"
    )

    await state.set_state(
        CreateTask.waiting_for_deadline
    )

# =====================================
# DEADLINE
# =====================================

@dp.message(CreateTask.waiting_for_deadline)
async def get_deadline(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    title = data["title"]
    priority = data["priority"]
    assignee_id = data["assignee_id"]

    add_task(
        title,
        priority,
        assignee_id,
        message.text
    )

    assignee_name = USERS[
        assignee_id
    ]["name"]

    reply_markup=main_menu()
        f"✅ Задача создана\n\n"
        f"📌 {title}\n"
        f"🔥 {priority}\n"
        f"👤 {assignee_name}\n"
        f"📅 {message.text}",
        reply_markup=main_menu()
    )

    await state.clear()

# =====================================
# ACTIVE TASKS
# =====================================

@dp.callback_query(F.data == "all_tasks")
async def all_tasks(
    callback: CallbackQuery
):

    tasks = get_tasks()

    active_tasks = [
        task for task in tasks
        if task[2] != "✅"
    ]

    if not active_tasks:

        reply_markup=main_menu()
            "📭 Активных задач нет"
        )

        return

    text = "📋 АКТИВНЫЕ ЗАДАЧИ\n\n"

    for task in active_tasks:

        task_id = task[0]
        title = task[1]
        status = task[2]
        priority = task[3]
        assignee_id = task[4]
        deadline = task[5]
        comment = task[6]

        assignee_name = USERS.get(
            assignee_id,
            {}
        ).get(
            "name",
            "Unknown"
        )

        text += (
            f"#{task_id} {status} {title}\n"
            f"🔥 {priority}\n"
            f"👤 {assignee_name}\n"
            f"📅 {deadline}\n"
        )

        if comment:
            text += f"💬 {comment}\n"

        text += "\n"

    keyboard_buttons = []

    for task in active_tasks:

        task_id = task[0]

        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"⚙️ #{task_id}",
                callback_data=f"work_{task_id}"
            ),

            InlineKeyboardButton(
                text=f"⏸ #{task_id}",
                callback_data=f"pause_{task_id}"
            ),

            InlineKeyboardButton(
                text=f"✅ #{task_id}",
                callback_data=f"done_{task_id}"
            )
        ])

        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"💬 Комментарий #{task_id}",
                callback_data=f"comment_{task_id}"
            )
        ])

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=keyboard_buttons
    )

    reply_markup=main_menu()
        text,
        reply_markup=keyboard
    )

# =====================================
# DONE TASKS
# =====================================

@dp.callback_query(F.data == "done_tasks")
async def done_tasks(
    callback: CallbackQuery
):

    tasks = get_tasks()

    completed_tasks = [
        task for task in tasks
        if task[2] == "✅"
    ]

    if not completed_tasks:

        reply_markup=main_menu()
            "📭 Выполненных задач нет"
        )

        return

    text = "✅ ВЫПОЛНЕННЫЕ ЗАДАЧИ\n\n"

    for task in completed_tasks:

        title = task[1]
        priority = task[3]
        assignee_id = task[4]
        deadline = task[5]

        assignee_name = USERS.get(
            assignee_id,
            {}
        ).get(
            "name",
            "Unknown"
        )

        text += (
            f"✅ {title}\n"
            f"🔥 {priority}\n"
            f"👤 {assignee_name}\n"
            f"📅 {deadline}\n\n"
        )

    reply_markup=main_menu()text)

# =====================================
# CALENDAR
# =====================================

@dp.callback_query(F.data == "calendar")
async def calendar(
    callback: CallbackQuery
):

    tasks = get_tasks()

    if not tasks:

        reply_markup=main_menu()
            "📭 Задач нет"
        )

        return

    text = "📅 КАЛЕНДАРЬ ЗАДАЧ\n\n"

    grouped = {}

    for task in tasks:

        deadline = task[5]

        if deadline not in grouped:
            grouped[deadline] = []

        grouped[deadline].append(task)

    for deadline, items in grouped.items():

        text += f"📅 {deadline}\n"

        for task in items:

            text += (
                f"• {task[2]} {task[1]}\n"
            )

        text += "\n"

    reply_markup=main_menu()text)

# =====================================
# OVERDUE
# =====================================

@dp.callback_query(F.data == "overdue")
async def overdue_tasks(
    callback: CallbackQuery
):

    tasks = get_tasks()

    text = "⚠️ ПРОСРОЧЕННЫЕ\n\n"

    found = False

    for task in tasks:

        try:

            deadline = datetime.strptime(
                task[5],
                "%d.%m.%Y %H:%M"
            )

            if (
                deadline < datetime.now()
                and task[2] != "✅"
            ):

                found = True

                text += (
                    f"{task[2]} {task[1]}\n"
                    f"📅 {task[5]}\n\n"
                )

        except:
            pass

    if not found:

        reply_markup=main_menu()
            "✅ Просроченных задач нет"
        )

        return

    reply_markup=main_menu()text)

# =====================================
# COMMENTS
# =====================================

@dp.callback_query(
    F.data.startswith("comment_")
)
async def add_comment(
    callback: CallbackQuery,
    state: FSMContext
):

    task_id = int(
        callback.data.split("_")[1]
    )

    await state.update_data(
        task_id=task_id
    )

    reply_markup=main_menu()
        "💬 Введите комментарий"
    )

    await state.set_state(
        AddComment.waiting_for_comment
    )

@dp.message(AddComment.waiting_for_comment)
async def save_comment(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    task_id = data["task_id"]

    update_comment(
        task_id,
        message.text
    )

    reply_markup=main_menu()
        "✅ Комментарий добавлен",
        reply_markup=main_menu()
    )

    await state.clear()

# =====================================
# STATUS HANDLERS
# =====================================

# =====================================
# STATUS HANDLERS
# =====================================

@dp.callback_query(
    F.data.startswith("work_")
)
async def set_work(
    callback: CallbackQuery
):

    task_id = int(
        callback.data.split("_")[1]
    )

    update_status(
        task_id,
        "⚙️"
    )

    reply_markup=main_menu()
        "✅ Статус изменён: В работе",
        reply_markup=main_menu()
    )

    await callback.answer()


@dp.callback_query(
    F.data.startswith("pause_")
)
async def set_pause(
    callback: CallbackQuery
):

    task_id = int(
        callback.data.split("_")[1]
    )

    update_status(
        task_id,
        "⏸"
    )

    reply_markup=main_menu()
        "✅ Статус изменён: На паузе",
        reply_markup=main_menu()
    )

    await callback.answer()


@dp.callback_query(
    F.data.startswith("done_")
)
async def set_done(
    callback: CallbackQuery
):

    task_id = int(
        callback.data.split("_")[1]
    )

    update_status(
        task_id,
        "✅"
    )

    reply_markup=main_menu()
        "✅ Задача выполнена",
        reply_markup=main_menu()
    )

    await callback.answer()


@dp.callback_query(
    F.data.startswith("cancel_")
)
async def set_cancel(
    callback: CallbackQuery
):

    task_id = int(
        callback.data.split("_")[1]
    )

    update_status(
        task_id,
        "❌"
    )

    reply_markup=main_menu()
        "❌ Задача отменена",
        reply_markup=main_menu()
    )

    await callback.answer()

# =====================================
# REMINDERS
# =====================================

async def check_deadlines():

    tasks = get_tasks()

    now = datetime.now()

    for task in tasks:

        try:

            deadline = datetime.strptime(
                task[5],
                "%d.%m.%Y %H:%M"
            )

            delta = deadline - now

            hours_left = delta.total_seconds() / 3600

            if 23 <= hours_left <= 24:

                await bot.send_message(
                    task[4],
                    f"⏰ Напоминание\n\n"
                    f"До дедлайна задачи "
                    f"'{task[1]}' остались сутки"
                )

            if 2 <= hours_left <= 3:

                await bot.send_message(
                    task[4],
                    f"⏰ Срочное напоминание\n\n"
                    f"До дедлайна задачи "
                    f"'{task[1]}' осталось 3 часа"
                )

        except:
            pass

scheduler = AsyncIOScheduler()

scheduler.add_job(
    check_deadlines,
    "interval",
    minutes=30
)

# =====================================
# MAIN
# =====================================

async def main():

    scheduler.start()

    await dp.start_polling(bot)

if __name__ == "__main__":

    asyncio.run(main())
