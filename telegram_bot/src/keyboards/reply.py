from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.i18n import gettext as _


async def get_menu_keyboard():
    keyboard = ReplyKeyboardBuilder()
    keyboard.button(text=_("Week schedule"))
    keyboard.button(text=_("Today's schedule"))
    keyboard.button(text=_("Help"))
    keyboard.button(text=_("About"))
    keyboard.button(text=_("Language"))
    keyboard.adjust(2, 3)
    return keyboard.as_markup()
