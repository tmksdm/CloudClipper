"""Вспомогательные функции: проверка FFmpeg, парсинг времени и т.д."""

import subprocess
import sys


def check_ffmpeg():
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
