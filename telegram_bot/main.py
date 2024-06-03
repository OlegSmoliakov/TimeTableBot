import uvloop
import logging as log

from aiogram import Bot, Dispatcher
from src.settings.config import BOT_TOKEN, LOG_LEVEL
from src.middlewares.i18n import fsm_i18n
from src.handlers import registration_router, base_router, menu_router


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.update.middleware(fsm_i18n)
    dp.include_routers(base_router, menu_router, registration_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    LOG_LEVEL = log.DEBUG
    log.basicConfig(level=LOG_LEVEL, format="%(asctime)s: %(levelname)s: %(message)s")
    uvloop.run(main())
