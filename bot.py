import asyncio
import os

from database import (
    add_task,
    get_tasks,
    update_task_status
)
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

    add_task(
        message.from_user.id,
        message.text
    )

    await message.answer(
        f"✅ Задача создана:\n\n📌 {message.text}",
        reply_markup=main_menu()
    )

    await state.clear()


# Мои задачи
@dp.callback_query(F.data == "my_tasks")
async def my_tasks(callback: CallbackQuery):

    user_tasks = get_tasks(callback.from_user.id)

    if not user_tasks:
        await callback.message.answer(
            "📭 У вас пока нет задач"
        )
        return

    for task in user_tasks:

        task_id = task[0]
        title = task[1]
        status = task[2]

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
            f"{status} {title}",
            reply_markup=keyboard
        )

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

@dp.callback_query(F.data.startswith("work_"))
async def set_work(callback: CallbackQuery):

    task_id = int(callback.data.split("_")[1])

    update_task_status(task_id, "⚙️")

    await callback.answer("Задача в работе")


@dp.callback_query(F.data.startswith("pause_"))
async def set_pause(callback: CallbackQuery):

    task_id = int(callback.data.split("_")[1])

    update_task_status(task_id, "⏸")

    await callback.answer("Задача на паузе")


@dp.callback_query(F.data.startswith("done_"))
async def set_done(callback: CallbackQuery):

    task_id = int(callback.data.split("_")[1])

    update_task_status(task_id, "✅")

    await callback.answer("Задача выполнена")


@dp.callback_query(F.data.startswith("cancel_"))
async def set_cancel(callback: CallbackQuery):

    task_id = int(callback.data.split("_")[1])

    update_task_status(task_id, "❌")

    await callback.answer("Задача отменена")

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
