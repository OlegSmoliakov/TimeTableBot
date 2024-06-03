from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.i18n import gettext as _
from aiogram.fsm.context import FSMContext
from typing import Optional
from datetime import datetime, date, timedelta

from ..rest import get_groups
from ..utils.misc import Paginator, get_located_pathways


degree = {
    1: "bachelor",
    2: "master",
    3: "doctor",
}


class RegCallBack(CallbackData, prefix="reg"):
    level: int
    title: Optional[str] = None
    id: Optional[int] = None
    page: Optional[int] = 1


class LangCallBack(CallbackData, prefix="lang"):
    lang: str


class LessonsCallBack(CallbackData, prefix="les"):
    day: date
    group: str = ""


def get_start_keyboard():
    btns = {
        _("Change language"): "language",
        _("Schedule setup"): "registration",
        _("Help"): "help",
    }
    keyboard = InlineKeyboardBuilder()

    for text, data in btns.items():
        keyboard.button(text=text, callback_data=data)
    keyboard.adjust(2, 1)

    return keyboard.as_markup()


def get_back_to_start_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=_("<< Back to start menu"), callback_data="start")

    return keyboard.as_markup()


def get_degree_keyboard():
    keyboard = InlineKeyboardBuilder()

    btns = {
        _("Bachelor's"): RegCallBack(level=1, title="degree", id=1),
        _("Master's"): RegCallBack(level=1, title="degree", id=2),
        _("Doctorate"): RegCallBack(level=1, title="degree", id=3),
        _("Back"): "start",
    }

    for text, data in btns.items():
        keyboard.button(text=text, callback_data=data)

    return keyboard.adjust(2, 1, 1).as_markup()


def get_nav_keyboard(paginator: Paginator, level):
    next = paginator.has_next()
    prev = paginator.has_previous()

    keyboard = InlineKeyboardBuilder()
    if prev:
        keyboard.button(
            text=_("<< previous"), callback_data=RegCallBack(level=level, page=prev)
        )
    if next:
        keyboard.button(
            text=_("next >>"), callback_data=RegCallBack(level=level, page=next)
        )

    return keyboard


async def get_group_keyboard(state_data: dict[str,], page: int = 1, level: int = 1):
    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 2
    groups = await get_groups(state_data["pathway"])
    paginator = Paginator(groups, page=page, per_page=6)

    for group in paginator.get_page():
        keyboard.button(
            text=group["title"],
            callback_data=RegCallBack(level=3, title="group", id=group["id"]),
        )

    nav_keyboard = get_nav_keyboard(paginator, level)
    keyboard.attach(nav_keyboard)

    keyboard.row(
        InlineKeyboardButton(
            text=_("Back to Major list"),
            callback_data=RegCallBack(title="degree", level=2).pack(),
        )
    )

    return keyboard.as_markup()


async def get_pathway_keyboard(state_data: dict[str,], page: int = 1, level: int = 1):
    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 2
    pathways = await get_located_pathways(state_data["locale"])
    paginator = Paginator(pathways, page=page, per_page=6)

    for pathway in paginator.get_page():
        keyboard.button(
            text=pathway["title"],
            callback_data=RegCallBack(level=2, title="pathway", id=pathway["id"]),
        )

    nav_keyboard = get_nav_keyboard(paginator, level)
    keyboard.attach(nav_keyboard)

    keyboard.row(
        InlineKeyboardButton(
            text=_("Back to Degree list"), callback_data="registration"
        )
    )

    return keyboard.as_markup()


# TODO refactor later, can be more optimized
async def get_registration_keyboard(callback_data: RegCallBack, state: FSMContext):
    state_data = await state.get_data()
    level = callback_data.level
    page = callback_data.page

    if callback_data.title == "degree" and callback_data.id is not None and level == 1:
        level = 2

    if callback_data.title == "pathway" and callback_data.id is not None and level == 2:
        level = 3

    if callback_data.title == "group" and callback_data.id is not None and level == 3:
        level = 0
        text = _("Registration successfully finished")
        keyboard = None

    if level == 1:
        text = _("Choose your Degree")
        keyboard = get_degree_keyboard()
    elif level == 2:
        text = _("Choose your Major")
        keyboard = await get_pathway_keyboard(state_data, page, level)
    elif level == 3:
        text = _("Choose your Group")
        keyboard = await get_group_keyboard(state_data, page, level)

    return text, keyboard


def get_language_keyboard(add_back_to_start=False):
    keyboard = InlineKeyboardBuilder()
    btns = {
        "English": LangCallBack(lang="en"),
        "Русский": LangCallBack(lang="ru"),
        "ქართული": LangCallBack(lang="ka"),
    }

    for text, data in btns.items():
        keyboard.button(text=text, callback_data=data)

    if add_back_to_start:
        keyboard.button(text=_("<< Back to start menu"), callback_data="start")
        keyboard.adjust(3, 1)

    return keyboard.as_markup()


def get_lesson_keyboard(current_day: date, group: str):
    keyboard = InlineKeyboardBuilder()
    prev = current_day + timedelta(days=-1)
    next = current_day + timedelta(days=1)
    btns = {
        f"< {prev.strftime('%d%m')}": LessonsCallBack(day=prev, group=group),
        f"*{current_day.strftime('%d%m')}*": LessonsCallBack(
            day=current_day, group=group
        ),
        f"{next.strftime('%d%m')} >": LessonsCallBack(day=next, group=group),
    }

    for text, data in btns.items():
        keyboard.button(text=text, callback_data=data)

    return keyboard.as_markup()
