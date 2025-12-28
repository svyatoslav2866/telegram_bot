import asyncio
from config import TOKEN
from aiogram import Bot, Dispatcher
from handlers import router as handlers_router
from keyboards import router as keyboards_router
from database.models import create_tables

async def main():
    await create_tables()
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(handlers_router)
    dp.include_router(keyboards_router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Выключение бота')