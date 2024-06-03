import logging as log
import asyncio

from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import FSMI18nMiddleware

from ..middlewares.i18n import fsm_i18n


async def process_language(callback: CallbackQuery, state: FSMContext):
    await fsm_i18n.set_locale(state, callback.data)


async def process_degree(degree: str):
    data = {"prev_state": "registration.choose_language", "degree": degree}
    return data
