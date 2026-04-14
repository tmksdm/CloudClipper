"""Точка входа приложения CloudClipper."""

import os

from core.utils import check_ffmpeg
from providers.yadisk import YandexDiskProvider
from core.downloader import download_fragment
from config import DEFAULT_DOWNLOAD_PATH


def main():
    """Главная функция — запускает приложение."""
    print("CloudClipper запущен")
    print()

    # Проверяем, установлен ли FFmpeg
    ffmpeg_ok = check_ffmpeg()
    if not ffmpeg_ok:
        return
    print()

    # --- Тест этапа 3: скачивание фрагмента видео ---
    print("=== Тест: скачивание фрагмента видео ===")
    print()

    # Шаг 1: Получаем прямую ссылку с Яндекс.Диска
    provider = YandexDiskProvider()
    print(f"Провайдер: {provider.get_provider_name()}")
    print()

    public_url = input("Вставьте публичную ссылку на видео с Яндекс.Диска: ").strip()
    if not public_url:
        print("Ссылка не введена. Выходим.")
        return

    print()
    print("Получаем прямую ссылку...")

    try:
        direct_url = provider.get_direct_link(public_url)
        print("Прямая ссылка получена!")
        print()
    except (ValueError, ConnectionError) as e:
        print(f"Ошибка: {e}")
        return

    # Шаг 2: Запрашиваем время начала и конца
    start_time = input("Время начала (MM:SS или HH:MM:SS, например 0:30): ").strip()
    if not start_time:
        print("Время начала не введено. Выходим.")
        return

    end_time = input("Время конца  (MM:SS или HH:MM:SS, например 1:00): ").strip()
    if not end_time:
        print("Время конца не введено. Выходим.")
        return

    print()

    # Шаг 3: Формируем путь для сохранения
    # Сохраняем в папку «Загрузки» с именем "fragment.mp4"
    output_path = os.path.join(DEFAULT_DOWNLOAD_PATH, "fragment.mp4")

    # Шаг 4: Скачиваем фрагмент
    try:
        saved_path = download_fragment(direct_url, start_time, end_time, output_path)
        print()
        print(f"Фрагмент успешно сохранён: {saved_path}")
    except ValueError as e:
        print(f"Ошибка во времени: {e}")
    except RuntimeError as e:
        print(f"Ошибка FFmpeg: {e}")


if __name__ == "__main__":
    main()
