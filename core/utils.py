"""Вспомогательные функции: проверка FFmpeg, парсинг времени, валидация ввода.

Этот модуль содержит утилиты, которые используются в разных частях приложения:
- Проверка наличия FFmpeg в системе
- Определение пути к FFmpeg (встроенный или системный)
- Парсинг строк времени (MM:SS, HH:MM:SS) в секунды и обратно
- Валидация (проверка корректности) пользовательского ввода
"""

import subprocess
import os
import sys
import re


def get_ffmpeg_path() -> str:
    """
    Определяет путь к ffmpeg.exe.

    Логика поиска:
    1. Сначала ищем ffmpeg.exe рядом с приложением (в папке ffmpeg/).
       Это нужно для .exe-сборки — FFmpeg вложен в дистрибутив.
    2. Если не нашли — возвращаем просто "ffmpeg", чтобы система
       искала его в PATH (для разработчика, у которого FFmpeg установлен).

    Порядок поиска «рядом с приложением»:
    - Если запущены как .exe (PyInstaller): ищем в папке, где лежит .exe
    - Если запущены как Python-скрипт: ищем в корне проекта

    Возвращает:
        Полный путь к ffmpeg.exe, или просто "ffmpeg" если встроенный не найден.
    """
    # --- Вариант 1: Мы внутри .exe (PyInstaller) ---
    # При сборке через --onedir, .exe лежит в dist/CloudClipper/.
    # Рядом с ним мы положим папку ffmpeg/ с ffmpeg.exe.
    # sys.executable — путь к самому .exe файлу.
    if getattr(sys, 'frozen', False):
        # frozen = True означает, что мы запущены из .exe
        exe_dir = os.path.dirname(sys.executable)
        bundled_path = os.path.join(exe_dir, "ffmpeg", "ffmpeg.exe")
        if os.path.isfile(bundled_path):
            return bundled_path

    # --- Вариант 2: Обычный запуск из Python (разработка) ---
    # Ищем в папке ffmpeg/ в корне проекта.
    # __file__ — путь к этому файлу (core/utils.py).
    # Поднимаемся на два уровня вверх: core/ → корень проекта.
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_path = os.path.join(project_root, "ffmpeg", "ffmpeg.exe")
    if os.path.isfile(local_path):
        return local_path

    # --- Вариант 3: Системный FFmpeg (из PATH) ---
    # Если встроенный не найден — пусть система ищет сама.
    return "ffmpeg"


def check_ffmpeg() -> bool:
    """
    Проверяет, установлен ли FFmpeg и доступен ли он.

    Сначала ищет встроенный FFmpeg (в папке ffmpeg/ рядом с приложением),
    затем системный (в PATH). Если найден — выводит его версию.
    Если не найден — выводит инструкцию по установке.

    Возвращает:
        True — FFmpeg найден и работает.
        False — FFmpeg не найден.
    """
    ffmpeg_path = get_ffmpeg_path()

    try:
        # Запускаем "ffmpeg -version" и читаем результат.
        result = subprocess.run(
            [ffmpeg_path, "-version"],
            capture_output=True,      # Перехватываем вывод программы
            text=True,                # Читаем вывод как текст (не байты)
            creationflags=subprocess.CREATE_NO_WINDOW  # Не показываем чёрное окно консоли
        )

        # Берём первую строку вывода — в ней содержится версия FFmpeg
        first_line = result.stdout.strip().split("\n")[0]

        # Определяем, встроенный это FFmpeg или системный
        if ffmpeg_path != "ffmpeg":
            print(f"FFmpeg найден (встроенный): {ffmpeg_path}")
        else:
            print(f"FFmpeg найден (системный)")
        print(f"  {first_line}")
        return True

    except FileNotFoundError:
        # Эта ошибка возникает, если система не может найти программу "ffmpeg"
        print("ОШИБКА: FFmpeg не найден!")
        print()
        print("FFmpeg необходим для работы CloudClipper.")
        print("Как установить:")
        print("  1. Откройте сайт: https://ffmpeg.org/download.html")
        print("  2. Скачайте версию для Windows (раздел 'Windows builds')")
        print("  3. Распакуйте архив в удобную папку (например, C:\\ffmpeg)")
        print("  4. Добавьте путь C:\\ffmpeg\\bin в системную переменную PATH")
        print("  5. Перезапустите командную строку и попробуйте снова")
        print()
        print("Подробная инструкция: https://www.wikihow.com/Install-FFmpeg-on-Windows")
        return False


# ──────────────────────────────────────────────
#  Парсинг и форматирование времени
# ──────────────────────────────────────────────

def parse_time_to_seconds(time_str: str) -> float:
    """
    Преобразует строку времени в секунды.

    Поддерживаемые форматы:
        "MM:SS"      → например, "1:30"  = 90 секунд
        "HH:MM:SS"   → например, "1:02:30" = 3750 секунд
        "SS"          → например, "90"    = 90 секунд

    Аргументы:
        time_str: Строка с временем, например "1:30" или "0:05:00".

    Возвращает:
        Число секунд (float).

    Выбрасывает:
        ValueError: Если формат строки не распознан.
    """
    # Убираем лишние пробелы по краям
    time_str = time_str.strip()

    # Проверяем, что строка не пустая
    if not time_str:
        raise ValueError("Время не может быть пустым.")

    # Разделяем строку по символу ":"
    # "1:30"    → ["1", "30"]
    # "1:02:30" → ["1", "02", "30"]
    # "90"      → ["90"]
    parts = time_str.split(":")

    try:
        if len(parts) == 3:
            # Формат HH:MM:SS
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            return hours * 3600 + minutes * 60 + seconds

        elif len(parts) == 2:
            # Формат MM:SS
            minutes = int(parts[0])
            seconds = int(parts[1])
            return minutes * 60 + seconds

        elif len(parts) == 1:
            # Просто число секунд
            return float(parts[0])

        else:
            raise ValueError(
                f"Неверный формат времени: '{time_str}'. "
                f"Используйте ММ:СС или ЧЧ:ММ:СС."
            )

    except (ValueError, IndexError):
        raise ValueError(
            f"Неверный формат времени: '{time_str}'. "
            f"Используйте ММ:СС или ЧЧ:ММ:СС (например, 1:30 или 0:05:00)."
        )


def seconds_to_ffmpeg_time(seconds: float) -> str:
    """
    Преобразует число секунд в строку формата HH:MM:SS для FFmpeg.

    FFmpeg принимает время в формате HH:MM:SS (часы:минуты:секунды).
    Эта функция конвертирует, например, 90.0 секунд в "00:01:30".

    Аргументы:
        seconds: Число секунд (не может быть отрицательным).

    Возвращает:
        Строку вида "HH:MM:SS".
    """
    # Защита от отрицательных значений
    if seconds < 0:
        seconds = 0

    # Вычисляем часы, минуты и оставшиеся секунды
    # int() отбрасывает дробную часть: int(3750) = 3750
    total_seconds = int(seconds)
    hours = total_seconds // 3600          # Целочисленное деление на 3600
    minutes = (total_seconds % 3600) // 60  # Остаток от деления на 3600, затем на 60
    secs = total_seconds % 60              # Остаток от деления на 60

    # f-строка с форматированием: 02d означает "целое число, минимум 2 цифры"
    # Например: 1 → "01", 30 → "30"
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


# ──────────────────────────────────────────────
#  Валидация пользовательского ввода
# ──────────────────────────────────────────────

def validate_url(url: str) -> str | None:
    """
    Проверяет, похожа ли ссылка на публичную ссылку Яндекс.Диска.

    Мы не делаем сложную проверку — просто убеждаемся, что это
    действительно ссылка на Яндекс.Диск, а не случайный текст.

    Аргументы:
        url: Строка из поля ввода ссылки.

    Возвращает:
        None — если всё в порядке (ошибки нет).
        Строку с сообщением об ошибке — если ссылка некорректна.
    """
    if not url or not url.strip():
        return "Вставьте ссылку на видео."

    url = url.strip()

    # Проверяем, что ссылка начинается с http:// или https://
    if not url.startswith("http://") and not url.startswith("https://"):
        return "Ссылка должна начинаться с https://."

    # Проверяем, что это ссылка на Яндекс.Диск
    # Допустимые домены: disk.yandex.ru, yadi.sk, disk.yandex.com
    valid_domains = ["disk.yandex.ru", "yadi.sk", "disk.yandex.com"]
    domain_ok = any(domain in url for domain in valid_domains)

    if not domain_ok:
        return (
            "Ссылка не похожа на Яндекс.Диск. "
            "Поддерживаются ссылки вида disk.yandex.ru/... или yadi.sk/..."
        )

    return None  # Всё в порядке


def validate_time_format(time_str: str, field_name: str) -> str | None:
    """
    Проверяет, что строка времени имеет допустимый формат.

    Допустимые форматы: MM:SS, HH:MM:SS, или просто число секунд.
    Каждая часть должна содержать только цифры.

    Аргументы:
        time_str:   Строка из поля ввода времени.
        field_name: Название поля ("начала" или "конца") — для сообщения об ошибке.

    Возвращает:
        None — если формат правильный.
        Строку с сообщением об ошибке — если формат неверный.
    """
    if not time_str or not time_str.strip():
        return f"Укажите время {field_name}."

    time_str = time_str.strip()

    # Регулярное выражение (шаблон для проверки текста).
    # ^ — начало строки, $ — конец строки.
    # \d+ — одна или более цифр.
    # (:\d+)? — необязательная группа ":цифры" (может повторяться 0-2 раза).
    #
    # Что проходит проверку:
    #   "90"       — просто секунды
    #   "1:30"     — минуты:секунды
    #   "1:02:30"  — часы:минуты:секунды
    #
    # Что НЕ проходит:
    #   "abc"      — буквы
    #   "1:2:3:4"  — слишком много частей
    #   ":30"      — начинается с двоеточия
    #   "1:"       — заканчивается двоеточием
    pattern = r"^\d+(:\d+){0,2}$"

    if not re.match(pattern, time_str):
        return (
            f"Неверный формат времени {field_name}: «{time_str}». "
            f"Используйте ММ:СС (например, 1:30) или ЧЧ:ММ:СС (например, 0:05:00)."
        )

    # Дополнительно: пробуем распарсить, чтобы убедиться, что значения адекватны
    try:
        seconds = parse_time_to_seconds(time_str)
        if seconds < 0:
            return f"Время {field_name} не может быть отрицательным."
    except ValueError:
        return (
            f"Неверный формат времени {field_name}: «{time_str}». "
            f"Используйте ММ:СС (например, 1:30) или ЧЧ:ММ:СС (например, 0:05:00)."
        )

    return None  # Всё в порядке


def validate_time_range(start_str: str, end_str: str) -> str | None:
    """
    Проверяет, что время начала меньше времени конца.

    Эта функция вызывается ПОСЛЕ того, как оба времени прошли
    проверку формата (validate_time_format). Поэтому мы уверены,
    что parse_time_to_seconds не упадёт.

    Аргументы:
        start_str: Строка времени начала.
        end_str:   Строка времени конца.

    Возвращает:
        None — если начало < конца (всё хорошо).
        Строку с ошибкой — если начало >= конца.
    """
    start_seconds = parse_time_to_seconds(start_str)
    end_seconds = parse_time_to_seconds(end_str)

    if start_seconds >= end_seconds:
        return (
            f"Время начала ({start_str}) должно быть меньше "
            f"времени конца ({end_str})."
        )

    return None  # Всё в порядке
