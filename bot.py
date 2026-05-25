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
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


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


@dp.callback_query(F.data == "my_tasks")
async def my_tasks(callback: CallbackQuery):
    await callback.message.answer("📋 Здесь будут ваши задачи")


@dp.callback_query(F.data == "today")
async def today(callback: CallbackQuery):
    await callback.message.answer("📅 Задачи на сегодня")


@dp.callback_query(F.data == "all_tasks")
async def all_tasks(callback: CallbackQuery):
    await callback.message.answer("📊 Все задачи")


@dp.callback_query(F.data == "new_task")
async def new_task(callback: CallbackQuery):
    await callback.message.answer("➕ Создание новой задачи")


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
