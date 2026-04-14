"""Вспомогательные функции: проверка FFmpeg, парсинг времени и т.д."""

import subprocess
import re


def check_ffmpeg() -> bool:
    """
    Проверяет, установлен ли FFmpeg и доступен ли он из командной строки.

    FFmpeg — это бесплатная программа для обработки видео и аудио.
    Наше приложение использует её для вырезания фрагментов из видео.
    FFmpeg должен быть установлен отдельно и добавлен в PATH
    (системную переменную, которая позволяет запускать программы из любой папки).

    Если FFmpeg найден — выводит его версию.
    Если не найден — выводит инструкцию по установке и завершает программу.
    """
    try:
        # Запускаем команду "ffmpeg -version" и читаем результат.
        # subprocess.run — это способ запустить внешнюю программу из Python.
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,      # Перехватываем вывод программы
            text=True,                # Читаем вывод как текст (не байты)
            creationflags=subprocess.CREATE_NO_WINDOW  # Не показываем чёрное окно консоли
        )

        # Берём первую строку вывода — в ней содержится версия FFmpeg
        first_line = result.stdout.strip().split("\n")[0]
        print(f"FFmpeg найден: {first_line}")
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
                f"Используйте MM:SS или HH:MM:SS."
            )

    except (ValueError, IndexError):
        raise ValueError(
            f"Неверный формат времени: '{time_str}'. "
            f"Используйте MM:SS или HH:MM:SS (например, 1:30 или 0:05:00)."
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
