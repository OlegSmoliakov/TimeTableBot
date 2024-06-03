import os
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# i18n
I18N_DOMAIN = "base"
LOCALE_DIR = os.path.join(BASE_DIR, "locale")

# Telegram
BOT_TOKEN = os.environ["BOT_TOKEN"]

# Rest
URL_REST = os.environ["URL_REST"]
MAX_CONNECTIONS = int(os.environ.get("MAX_CONNECTIONS", 1))

# logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_LEVEL = getattr(logging, LOG_LEVEL.upper())
