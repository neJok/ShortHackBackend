import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from security import get_password_hash
from core.config import settings
from db import collection

bot = Bot(token=settings.telegram_token)
dp = Dispatcher(storage=MemoryStorage())  # FSM работает через MemoryStorage


class Regist(StatesGroup):
    email = State()
    password = State()


@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Сап, чтобы зарегистрироваться нажми /reg")


@dp.message(Command("reg"))
async def reg_user(message: types.Message, state: FSMContext):
    await message.answer("Напиши мне свою почту")
    await state.set_state(Regist.email)


@dp.message(Regist.email)
async def set_email(message: types.Message, state: FSMContext):
    await state.update_data(email=message.text)
    await message.answer("Хорошо, теперь пароль")
    await state.set_state(Regist.password)


@dp.message(Regist.password)
async def set_password(message: types.Message, state: FSMContext):
    await state.update_data(password=message.text)
    data = await state.get_data()
    curr_email = data.get("email")
    password = data.get("password")  # 32
    user = collection.find_one(
        {"email": curr_email, "hashed_password": get_password_hash(password)})
    if user:
        await message.answer(f"Теперь тебе будут приходить оповещения {message.from_user.id}")
        collection.update_one(
            {"email": curr_email},
            {"$set": {"user_tg_id": message.from_user.id}}
        )
        await state.clear()
    else:
        await message.answer(f'Пользователя с такой почтой или паролем не существует')


async def send_notif(status, user_id):
    if status == 'approved':
        await bot.send_message(user_id, text=f'Событие "_" в аудитории _ разрешено для проведения')
    elif status == 'not_approved':
        await bot.send_message(user_id, text=f'Событие "_" в аудитории _ не может быть проведено')


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
