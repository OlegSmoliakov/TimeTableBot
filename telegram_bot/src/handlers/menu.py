from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, lazy_gettext as __
from datetime import date

from src.keyboards.inline import LessonsCallBack, get_lesson_keyboard
from src.keyboards.reply import get_menu_keyboard
from ..rest import get_lessons_week, get_lessons_day
from ..utils.formatting import format_timetable


menu_router = Router()


@menu_router.message(F.text == __("Week schedule"))
async def handle_registration(message: Message, state: FSMContext):
    data = await state.get_data()
    week_timetable = await get_lessons_week(data["group"])
    week_timetable = format_timetable(week_timetable)
    markup = await get_menu_keyboard()

    await message.answer(week_timetable, "Markdown", reply_markup=markup)


@menu_router.message(F.text == __("Today's schedule"))
async def handle_registration(message: Message, state: FSMContext):
    state_data = await state.get_data()
    group = state_data["group"]

    day_timetable = await get_lessons_day(group)
    markup = get_lesson_keyboard(date.today(), group)

    if day_timetable:
        day_timetable = format_timetable(day_timetable)
    else:
        day_timetable = _("There's no class for today")

    await message.answer(day_timetable, "Markdown", reply_markup=markup)


@menu_router.callback_query(LessonsCallBack.filter())
async def handle_lesson_request(
    callback_query: CallbackQuery, callback_data: LessonsCallBack
):
    day_timetable = await get_lessons_day(callback_data.group)
    markup = get_lesson_keyboard(callback_data.day, callback_data.group)

    if day_timetable:
        day_timetable = format_timetable(day_timetable)
    else:
        day_timetable = _("There's no class for today")

    await callback_query.message.edit_text(
        day_timetable, parse_mode="Markdown", reply_markup=markup
    )
