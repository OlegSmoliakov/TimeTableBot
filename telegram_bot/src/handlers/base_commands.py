import logging as log

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, lazy_gettext as __
from aiogram.filters import or_f


from ..common.fsm import Form
from ..keyboards.inline import (
    LangCallBack,
    get_start_keyboard,
    get_language_keyboard,
    get_back_to_start_keyboard,
)
from src.keyboards.reply import get_menu_keyboard
from ..middlewares.i18n import fsm_i18n
from ..common import content

base_router = Router()


@base_router.callback_query(F.data == "start")
async def handle_callback_start(callback_query: CallbackQuery, state: FSMContext):
    text, markup = await process_start(state)
    await callback_query.message.edit_text(text, reply_markup=markup)
    await callback_query.answer()


@base_router.message(CommandStart())
async def handle_message_start(message: Message, state: FSMContext):
    text, markup = await process_start(state)
    await message.answer(text, reply_markup=markup)


@base_router.callback_query(F.data == "help")
@base_router.message(or_f(Command("help"), F.text == __("Help")))
async def handle_help(update: Message | CallbackQuery):
    text = await content.help()

    if isinstance(update, Message):
        await update.answer(text)
    elif isinstance(update, CallbackQuery):
        await update.message.edit_text(text, reply_markup=get_back_to_start_keyboard())
        await update.answer()


@base_router.message(or_f(Command("about"), F.text == __("About")))
async def handle_help(update: Message | CallbackQuery):
    text = await content.about()
    await update.answer(text)


@base_router.callback_query(F.data == "language")
async def handle_callback_language(callback_query: CallbackQuery):
    await callback_query.message.edit_text(
        _("Select a language"), reply_markup=get_language_keyboard(True)
    )
    await callback_query.answer()


@base_router.message(or_f(Command("language"), F.text == __("Language")))
async def handle_message_language(message: Message):
    await message.answer(_("Select a language"), reply_markup=get_language_keyboard())


@base_router.callback_query(LangCallBack.filter())
async def process_language(
    callback_query: CallbackQuery, callback_data: LangCallBack, state: FSMContext
):
    await fsm_i18n.set_locale(state, callback_data.lang)
    await callback_query.message.edit_text(_("Language successfully changed"))

    state_data = await state.get_data()

    if "group" in state_data:
        markup = await get_menu_keyboard()
        await callback_query.message.answer(_("Keyboard updated"), reply_markup=markup)

    if "degree" not in state_data:
        markup = get_start_keyboard()
        await callback_query.message.answer(await content.about(), reply_markup=markup)

    await callback_query.answer()


async def process_start(state: FSMContext):
    log.debug("set the start state")
    await state.set_state(Form.start)

    text = await content.about()
    markup = get_start_keyboard()
    return text, markup
