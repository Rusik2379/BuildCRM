import asyncio

from aiogram import Bot, Dispatcher

from app.bot.handlers.tasks import router as task_router
from app.core.config import settings


async def main():
    if not settings.tg_bot_token:
        raise RuntimeError("TG_BOT_TOKEN is empty. Fill it in .env")

    bot = Bot(token=settings.tg_bot_token)
    dp = Dispatcher()
    dp.include_router(task_router)

    print("Telegram bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
