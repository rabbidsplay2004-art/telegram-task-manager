
import asyncio
import csv
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
    CallbackQuery,
    FSInputFile
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
    111111111: {
        "name": "Админ",
        "role": "admin"
    },
    222222222: {
        "name": "Иван",
        "role": "user"
    },
    333333333: {
        "name": "Мария",
        "role": "user"
    }
}

# =====================================
# DATABASE
# =====================================

conn = sqlite3.connect("tasks.db")
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


def add_task(title, priority, assignee_id, deadline):
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
        ORDER BY id DESC
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
        (status, task_id)
    )

    conn.commit()



def update_comment(task_id, comment):
    cursor.execute(
        """
        UPDATE tasks
        SET comment = ?
        WHERE id = ?
        """,
        (comment, task_id)
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
                    text="📋 Все задачи",
                    callback_data="all_tasks"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📅 Сегодня",
                    callback_data="today"
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
            ],
            [
                InlineKeyboardButton(
                    text="📁 Экспорт CSV",
                    callback_data="export"
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
        "👋 Task Manager Bot",
        reply_markup=main_menu()
    )


# =====================================
# CREATE TASK
# =====================================

@dp.callback_query(F.data == "new_task")
async def new_task(callback: CallbackQuery, state: FSMContext):

    await callback.message.answer(
        "✍️ Введите название задачи"
    )

    await state.set_state(
        CreateTask.waiting_for_title
    )


@dp.message(CreateTask.waiting_for_title)
async def get_title(message: Message, state: FSMContext):

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

    await message.answer(
        "🔥 Выберите приоритет",
        reply_markup=keyboard
    )

    await state.set_state(
        CreateTask.waiting_for_priority
    )


@dp.callback_query(
    CreateTask.waiting_for_priority,
    F.data.startswith("priority_")
)
async def get_priority(callback: CallbackQuery, state: FSMContext):

    priority_map = {
        "priority_high": "🔴 Высокий",
        "priority_medium": "🟡 Средний",
        "priority_low": "🟢 Низкий"
    }

    priority = priority_map[callback.data]

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

    await callback.message.answer(
        "👤 Выберите исполнителя",
        reply_markup=keyboard
    )

    await state.set_state(
        CreateTask.waiting_for_assignee
    )


@dp.callback_query(
    CreateTask.waiting_for_assignee,
    F.data.startswith("assign_")
)
async def assign_task(callback: CallbackQuery, state: FSMContext):

    assignee_id = int(
        callback.data.split("_")[1]
    )

    await state.update_data(
        assignee_id=assignee_id
    )

    await callback.message.answer(
        "📅 Введите дедлайн\n\nПример: 28.05.2026"
    )

    await state.set_state(
        CreateTask.waiting_for_deadline
    )


@dp.message(CreateTask.waiting_for_deadline)
async def get_deadline(message: Message, state: FSMContext):

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

    assignee_name = USERS[assignee_id]["name"]

    await message.answer(
        f"✅ Задача создана\n\n"
        f"📌 {title}\n"
        f"🔥 {priority}\n"
        f"👤 {assignee_name}\n"
        f"📅 {message.text}",
        reply_markup=main_menu()
    )

    await state.clear()


# =====================================
# ALL TASKS
# =====================================

@dp.callback_query(F.data == "all_tasks")
async def all_tasks(callback: CallbackQuery):

    tasks = get_tasks()

    if not tasks:
        await callback.message.answer(
            "📭 Задач пока нет"
        )
        return

    for task in tasks:

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

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⚙️",
                        callback_data=f"work_{task_id}"
                    ),
                    InlineKeyboardButton(
                        text="⏸",
                        callback_data=f"pause_{task_id}"
                    ),
                    InlineKeyboardButton(
                        text="✅",
                        callback_data=f"done_{task_id}"
                    ),
                    InlineKeyboardButton(
                        text="❌",
                        callback_data=f"cancel_{task_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="💬 Комментарий",
                        callback_data=f"comment_{task_id}"
                    )
                ]
            ]
        )

        text = (
            f"{status} {title}\n"
            f"🔥 {priority}\n"
            f"👤 {assignee_name}\n"
            f"📅 {deadline}"
        )

        if comment:
            text += f"\n💬 {comment}"

        await callback.message.answer(
            text,
            reply_markup=keyboard
        )


# =====================================
# COMMENTS
# =====================================

@dp.callback_query(F.data.startswith("comment_"))
async def add_comment(callback: CallbackQuery, state: FSMContext):

    task_id = int(
        callback.data.split("_")[1]
    )

    await state.update_data(
        task_id=task_id
    )

    await callback.message.answer(
        "💬 Введите комментарий"
    )

    await state.set_state(
        AddComment.waiting_for_comment
    )


@dp.message(AddComment.waiting_for_comment)
async def save_comment(message: Message, state: FSMContext):

    data = await state.get_data()

    task_id = data["task_id"]

    update_comment(
        task_id,
        message.text
    )

    await message.answer(
        "✅ Комментарий добавлен",
        reply_markup=main_menu()
    )

    await state.clear()


# =====================================
# TODAY
# =====================================

@dp.callback_query(F.data == "today")
async def today_tasks(callback: CallbackQuery):

    today = datetime.now().strftime("%d.%m.%Y")

    tasks = get_tasks()

    found = False

    for task in tasks:

        if task[5] == today:

            found = True

            await callback.message.answer(
                f"{task[2]} {task[1]}\n📅 {task[5]}"
            )

    if not found:
        await callback.message.answer(
            "📭 На сегодня задач нет"
        )


# =====================================
# OVERDUE
# =====================================

@dp.callback_query(F.data == "overdue")
async def overdue_tasks(callback: CallbackQuery):

    today = datetime.now()

    tasks = get_tasks()

    found = False

    for task in tasks:

        try:
            deadline = datetime.strptime(
                task[5],
                "%d.%m.%Y"
            )

            if deadline < today and task[2] != "✅":

                found = True

                await callback.message.answer(
                    f"⚠️ {task[1]}\n📅 {task[5]}"
                )

        except:
            pass

    if not found:
        await callback.message.answer(
            "✅ Просроченных задач нет"
        )


# =====================================
# EXPORT
# =====================================

@dp.callback_query(F.data == "export")
async def export_tasks(callback: CallbackQuery):

    tasks = get_tasks()

    with open("tasks_export.csv", "w", newline="", encoding="utf-8") as file:

        writer = csv.writer(file)

        writer.writerow([
            "ID",
            "Название",
            "Статус",
            "Приоритет",
            "Исполнитель",
            "Дедлайн",
            "Комментарий"
        ])

        for task in tasks:

            assignee_name = USERS.get(
                task[4],
                {}
            ).get(
                "name",
                "Unknown"
            )

            writer.writerow([
                task[0],
                task[1],
                task[2],
                task[3],
                assignee_name,
                task[5],
                task[6]
            ])

    document = FSInputFile("tasks_export.csv")

    await callback.message.answer_document(document)


# =====================================
# STATUS HANDLERS
# =====================================

@dp.callback_query(F.data.startswith("work_"))
async def set_work(callback: CallbackQuery):

    task_id = int(
        callback.data.split("_")[1]
    )

    update_status(task_id, "⚙️")

    await callback.answer(
        "Задача в работе"
    )


@dp.callback_query(F.data.startswith("pause_"))
async def set_pause(callback: CallbackQuery):

    task_id = int(
        callback.data.split("_")[1]
    )

    update_status(task_id, "⏸")

    await callback.answer(
        "Задача на паузе"
    )


@dp.callback_query(F.data.startswith("done_"))
async def set_done(callback: CallbackQuery):

    task_id = int(
        callback.data.split("_")[1]
    )

    update_status(task_id, "✅")

    await callback.answer(
        "Задача выполнена"
    )


@dp.callback_query(F.data.startswith("cancel_"))
async def set_cancel(callback: CallbackQuery):

    task_id = int(
        callback.data.split("_")[1]
    )

    update_status(task_id, "❌")

    await callback.answer(
        "Задача отменена"
    )


# =====================================
# REMINDERS
# =====================================

async def check_deadlines():

    tasks = get_tasks()

    today = datetime.now()

    for task in tasks:

        try:
            deadline = datetime.strptime(
                task[5],
                "%d.%m.%Y"
            )

            delta = (deadline - today).days

            if delta == 1:

                assignee_id = task[4]

                await bot.send_message(
                    assignee_id,
                    f"⏰ Напоминание\n\n"
                    f"До дедлайна задачи '{task[1]}' остался 1 день"
                )

        except:
            pass


scheduler = AsyncIOScheduler()
scheduler.add_job(check_deadlines, "interval", hours=6)


# =====================================
# MAIN
# =====================================

async def main():

    scheduler.start()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

