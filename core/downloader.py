"""Логика скачивания фрагментов видео через FFmpeg.

FFmpeg — это мощная программа для работы с видео/аудио.
Мы вызываем её из Python через модуль subprocess (запуск внешних программ).

Стратегия обрезки:
    Видео сжимается с помощью ключевых кадров (keyframes). FFmpeg может
    начать резать только с ближайшего ключевого кадра. Если пользователь
    хочет фрагмент с 1:00 по 2:00, мы запрашиваем с 0:57 по 2:03.
    Этот буфер в 3 секунды гарантирует, что нужный момент точно попадёт
    в скачанный фрагмент.

    Используем параметры FFmpeg:
    -ss ВРЕМЯ  (ПЕРЕД -i) — перемотать к указанному времени (быстрый поиск)
    -i URL                — входной файл (прямая ссылка на видео)
    -to ВРЕМЯ             — остановить запись в указанный момент
    -c copy               — не перекодировать, просто копировать потоки
                            (это быстро и не теряет качество)
"""

import subprocess
import os

from core.utils import parse_time_to_seconds, seconds_to_ffmpeg_time


# Буфер в секундах, который добавляется/вычитается из времени пользователя
BUFFER_SECONDS = 3


def download_fragment(
    direct_url: str,
    start_time: str,
    end_time: str,
    output_path: str
) -> str:
    """
    Скачивает фрагмент видео по прямой ссылке с помощью FFmpeg.

    Аргументы:
        direct_url:  Прямая ссылка на видео (полученная от провайдера).
        start_time:  Время начала фрагмента, строка вида "MM:SS" или "HH:MM:SS".
        end_time:    Время конца фрагмента, в том же формате.
        output_path: Полный путь к файлу, куда сохранить результат.
                     Например: "C:/Users/User/Downloads/fragment.mp4"

    Возвращает:
        Путь к сохранённому файлу (тот же output_path).

    Выбрасывает:
        ValueError: Если время указано неверно или начало >= конец.
        RuntimeError: Если FFmpeg завершился с ошибкой.
    """

    # --- 1. Парсим время начала и конца ---
    start_seconds = parse_time_to_seconds(start_time)
    end_seconds = parse_time_to_seconds(end_time)

    # Проверяем, что начало раньше конца
    if start_seconds >= end_seconds:
        raise ValueError(
            f"Время начала ({start_time}) должно быть меньше "
            f"времени конца ({end_time})."
        )

    # --- 2. Применяем буфер ±3 секунды ---
    # Вычитаем 3 секунды из начала (но не меньше 0)
    buffered_start = max(0, start_seconds - BUFFER_SECONDS)

    # Прибавляем 3 секунды к концу
    buffered_end = end_seconds + BUFFER_SECONDS

    # Конвертируем обратно в строки формата HH:MM:SS для FFmpeg
    ffmpeg_start = seconds_to_ffmpeg_time(buffered_start)
    ffmpeg_end = seconds_to_ffmpeg_time(buffered_end)

    # Вычисляем длительность фрагмента (для параметра -t)
    # Важно: -to при использовании с -ss ПЕРЕД -i работает относительно
    # начала файла, а не относительно точки seek. Поэтому используем -t
    # (длительность), чтобы точно указать, сколько секунд записывать.
    duration_seconds = buffered_end - buffered_start
    ffmpeg_duration = seconds_to_ffmpeg_time(duration_seconds)

    # --- 3. Создаём папку для сохранения, если её нет ---
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # --- 4. Формируем команду FFmpeg ---
    # Порядок параметров ВАЖЕН:
    # -ss перед -i = быстрый поиск (seek) на уровне входного потока
    # -t = длительность записи (сколько секунд от точки seek)
    # -c copy = не перекодировать (быстро, без потерь качества)
    # -y = перезаписывать выходной файл без вопросов
    command = [
        "ffmpeg",
        "-ss", ffmpeg_start,        # Перемотка к началу фрагмента
        "-i", direct_url,           # Входной файл (ссылка на видео)
        "-t", ffmpeg_duration,      # Длительность записи
        "-c", "copy",               # Копировать без перекодирования
        "-y",                       # Перезаписывать файл, если он существует
        output_path                 # Куда сохранить результат
    ]

    # --- 5. Выводим информацию для отладки ---
    print(f"Время пользователя:  {start_time} — {end_time}")
    print(f"С буфером ±{BUFFER_SECONDS}с: {ffmpeg_start} — {ffmpeg_end}")
    print(f"Длительность:        {ffmpeg_duration}")
    print(f"Сохраняем в:         {output_path}")
    print()
    print("Запускаем FFmpeg...")
    print()

    # --- 6. Запускаем FFmpeg ---
    try:
        result = subprocess.run(
            command,
            capture_output=True,    # Перехватываем вывод FFmpeg
            text=True,              # Читаем как текст
            creationflags=subprocess.CREATE_NO_WINDOW  # Без чёрного окна
        )
    except FileNotFoundError:
        raise RuntimeError(
            "FFmpeg не найден. Убедитесь, что он установлен и доступен в PATH."
        )

    # --- 7. Проверяем результат ---
    # FFmpeg возвращает код 0, если всё прошло успешно
    if result.returncode != 0:
        # Берём последние 5 строк вывода ошибок — обычно там самое важное
        error_lines = result.stderr.strip().split("\n")
        last_lines = "\n".join(error_lines[-5:])
        raise RuntimeError(
            f"FFmpeg завершился с ошибкой (код {result.returncode}).\n"
            f"Последние строки вывода:\n{last_lines}"
        )

    # Проверяем, что файл действительно создан
    if not os.path.exists(output_path):
        raise RuntimeError(
            "FFmpeg завершился без ошибок, но файл не был создан. "
            "Возможно, ссылка на видео недействительна."
        )

    # Размер файла в мегабайтах (для информации)
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Готово! Файл сохранён: {output_path}")
    print(f"Размер файла: {file_size_mb:.1f} МБ")

    return output_path
