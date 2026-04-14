"""Настройки приложения CloudClipper."""

import os

# Папка для сохранения скачанных фрагментов.
# По умолчанию — стандартная папка «Загрузки» текущего пользователя.
DEFAULT_DOWNLOAD_PATH = os.path.join(os.path.expanduser("~"), "Downloads")

# Название приложения
APP_NAME = "CloudClipper"

# Версия
APP_VERSION = "0.1.0"
