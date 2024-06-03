from ..settings.config import I18N_DOMAIN, LOCALE_DIR
from aiogram.utils.i18n import FSMI18nMiddleware, I18n

i18n = I18n(path=LOCALE_DIR, domain=I18N_DOMAIN)
fsm_i18n = FSMI18nMiddleware(i18n)
