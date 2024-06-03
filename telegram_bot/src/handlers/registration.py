import logging as log

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.i18n import gettext as _

from ..keyboards.reply import get_menu_keyboard
from ..keyboards.inline import (
    RegCallBack,
    get_degree_keyboard,
    get_language_keyboard,
    get_registration_keyboard,
)
from ..common.fsm import Form

registration_router = Router()


@registration_router.callback_query(F.data == "registration")
async def handle_registration(callback_query: CallbackQuery, state: FSMContext):
    markup = get_degree_keyboard()

    await state.set_state(Form.registration)
    await callback_query.message.edit_text(_("Choose your degree"), reply_markup=markup)
    await callback_query.answer()


@registration_router.callback_query(RegCallBack.filter())
async def handle_registration_process(
    callback_query: CallbackQuery, callback_data: RegCallBack, state: FSMContext
):
    log.debug(f"handle_registration_process data: {await state.get_data()}")

    if callback_data.id:
        await state.update_data({callback_data.title: callback_data.id})

    text, markup = await get_registration_keyboard(callback_data, state=state)

    await callback_query.message.edit_text(text, reply_markup=markup)

    if markup is None:
        await state.set_state(Form.idle)
        text = _("Now you can get a schedule for the day or week")
        markup = await get_menu_keyboard()
        await callback_query.message.answer(text, reply_markup=markup)

    await callback_query.answer()
