from ..rest import get_last_update
from aiogram.utils.i18n import gettext as _


async def about():
    date, id = await get_last_update()
    lines = [
        _("GTU Schedule Bot"),
        _("Version: {0}").format("0.1.0"),
        _("Last schedule update: {0}, id: {1}").format(date, id),
        _("Support: {0}, {1}").format("@smai1s", "@dabecow"),
    ]

    return "\n".join(lines)


async def help():
    lines = [
        _("Commands:"),
        "/help " + _("- show this message"),
        "/about " + _("- show information about bot"),
        "/language" + _("- change language"),
    ]

    return "\n".join(lines)
