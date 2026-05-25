import asyncio
import os
import sqlite3

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
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =========================
# USERS
# =========================

USERS = {
    123456789: {
        "name": "Админ",
        "role": "admin"
    }
}

# =========================
# DATABASE
# =========================

conn = sqlite3.connect("tasks.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    status TEXT,
    assignee_id INTEGER,
    deadline TEXT
)
""")

conn.commit()


def add_task(title, assignee_id, deadline):

    cursor.execute(
        """
        INSERT INTO tasks (
            title,
            status,
            assignee_id,
            deadline
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            title,
            "🆕",
            assignee_id,
            deadline
        )
    )

    conn.commit()


def get_tasks():

    cursor.execute(
        """
        SELECT
            id,
            title,
            status,
            assignee_id,
            deadline
        FROM tasks
        """
    )

    return cursor.fetchall()


def update_task_status(task_id, status):

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


# =========================
# FSM
# =========================

class CreateTask(StatesGroup):

    waiting_for_title = State()
    waiting_for_assignee = State()
    waiting_for_deadline = State()


# =========================
# MENU
# =========================

def main_menu():

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Все задачи",
                    callback_data="all_tasks"
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

    return keyboard


# =========================
# START
# =========================

@dp.message(CommandStart())
async def start(message: Message):

    await message.answer(
        "👋 Task Manager Bot",
        reply_markup=main_menu()
    )


# =========================
# CREATE TASK
# =========================

@dp.callback_query(F.data == "new_task")
async def new_task(
    callback: CallbackQuery,
    state: FSMContext
):

    await callback.message.answer(
        "✍️ Введите название задачи"
    )

    await state.set_state(
        CreateTask.waiting_for_title
    )


# =========================
# GET TITLE
# =========================

@dp.message(CreateTask.waiting_for_title)
async def get_title(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        title=message.text
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

    await message.answer(
        "👤 Выберите исполнителя",
        reply_markup=keyboard
    )

    await state.set_state(
        CreateTask.waiting_for_assignee
    )


# =========================
# ASSIGN TASK
# =========================

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

    await callback.message.answer(
        "📅 Введите дедлайн\n\n"
        "Пример: 28.05.2026"
    )

    await state.set_state(
        CreateTask.waiting_for_deadline
    )


# =========================
# DEADLINE
# =========================

@dp.message(CreateTask.waiting_for_deadline)
async def get_deadline(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    title = data["title"]
    assignee_id = data["assignee_id"]

    add_task(
        title,
        assignee_id,
        message.text
    )

    assignee_name = USERS.get(
        assignee_id,
        {}
    ).get(
        "name",
        "Unknown"
    )

    await message.answer(
        f"✅ Задача создана\n\n"
        f"📌 {title}\n"
        f"👤 {assignee_name}\n"
        f"📅 {message.text}",
        reply_markup=main_menu()
    )

    await state.clear()


# =========================
# ALL TASKS
# =========================

@dp.callback_query(F.data == "all_tasks")
async def all_tasks(
    callback: CallbackQuery
):

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
        assignee_id = task[3]
        deadline = task[4]

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
                ]
            ]
        )

        await callback.message.answer(
            f"{status} {title}\n"
            f"👤 {assignee_name}\n"
            f"📅 {deadline}",
            reply_markup=keyboard
        )


# =========================
# STATUS HANDLERS
# =========================

@dp.callback_query(F.data.startswith("work_"))
async def set_work(
    callback: CallbackQuery
):

    task_id = int(
        callback.data.split("_")[1]
    )

    update_task_status(
        task_id,
        "⚙️"
    )

    await callback.answer(
        "Задача в работе"
    )


@dp.callback_query(F.data.startswith("pause_"))
async def set_pause(
    callback: CallbackQuery
):

    task_id = int(
        callback.data.split("_")[1]
    )

    update_task_status(
        task_id,
        "⏸"
    )

    await callback.answer(
        "Задача на паузе"
    )


@dp.callback_query(F.data.startswith("done_"))
async def set_done(
    callback: CallbackQuery
):

    task_id = int(
        callback.data.split("_")[1]
    )

    update_task_status(
        task_id,
        "✅"
    )

    await callback.answer(
        "Задача выполнена"
    )


@dp.callback_query(F.data.startswith("cancel_"))
async def set_cancel(
    callback: CallbackQuery
):

    task_id = int(
        callback.data.split("_")[1]
    )

    update_task_status(
        task_id,
        "❌"
    )

    await callback.answer(
        "Задача отменена"
    )


# =========================
# MAIN
# =========================

async def main():

    await dp.start_polling(bot)


if __name__ == "__main__":

    asyncio.run(main())
