import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Временное хранилище задач
tasks = []


# FSM
class CreateTask(StatesGroup):
    waiting_for_title = State()


# Главное меню
def main_menu():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Мои задачи",
                    callback_data="my_tasks"
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
                    text="📊 Все задачи",
                    callback_data="all_tasks"
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
                    text="⚠️ Просроченные",
                    callback_data="overdue"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ Настройки",
                    callback_data="settings"
                )
            ]
        ]
    )

    return keyboard


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "👋 Добро пожаловать в Task Manager",
        reply_markup=main_menu()
    )


# Создание задачи
@dp.callback_query(F.data == "new_task")
async def new_task(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "✍️ Введите название задачи"
    )

    await state.set_state(CreateTask.waiting_for_title)


# Получение названия задачи
@dp.message(CreateTask.waiting_for_title)
async def get_task_title(message: Message, state: FSMContext):
    task = {
        "title": message.text,
        "user_id": message.from_user.id
    }

    tasks.append(task)

    await message.answer(
        f"✅ Задача создана:\n\n📌 {message.text}",
        reply_markup=main_menu()
    )

    await state.clear()


# Мои задачи
@dp.callback_query(F.data == "my_tasks")
async def my_tasks(callback: CallbackQuery):

    user_tasks = [
        task for task in tasks
        if task["user_id"] == callback.from_user.id
    ]

    if not user_tasks:
        await callback.message.answer(
            "📭 У вас пока нет задач"
        )
        return

    text = "📋 Ваши задачи:\n\n"

    for i, task in enumerate(user_tasks, start=1):
        text += f"{i}. {task['title']}\n"

    await callback.message.answer(text)


# Остальные кнопки
@dp.callback_query(F.data == "today")
async def today(callback: CallbackQuery):
    await callback.message.answer("📅 Задачи на сегодня")


@dp.callback_query(F.data == "all_tasks")
async def all_tasks(callback: CallbackQuery):
    await callback.message.answer("📊 Все задачи")


@dp.callback_query(F.data == "overdue")
async def overdue(callback: CallbackQuery):
    await callback.message.answer("⚠️ Просроченные задачи")


@dp.callback_query(F.data == "settings")
async def settings(callback: CallbackQuery):
    await callback.message.answer("⚙️ Настройки")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
