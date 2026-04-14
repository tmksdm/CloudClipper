"""Точка входа приложения CloudClipper."""

from core.utils import check_ffmpeg
from providers.yadisk import YandexDiskProvider


def main():
    """Главная функция — запускает приложение."""
    print("CloudClipper запущен")
    print()

    # Проверяем, установлен ли FFmpeg
    ffmpeg_ok = check_ffmpeg()
    if not ffmpeg_ok:
        return
    print()

    # --- Тест этапа 2: получение прямой ссылки с Яндекс.Диска ---
    print("=== Тест: получение прямой ссылки с Яндекс.Диска ===")
    print()

    # Создаём экземпляр провайдера
    provider = YandexDiskProvider()
    print(f"Провайдер: {provider.get_provider_name()}")
    print()

    # Запрашиваем ссылку у пользователя
    public_url = input("Вставьте публичную ссылку на файл с Яндекс.Диска: ").strip()

    if not public_url:
        print("Ссылка не введена. Выходим.")
        return

    print()
    print("Запрашиваем прямую ссылку...")

    try:
        direct_link = provider.get_direct_link(public_url)
        print()
        print("Прямая ссылка получена!")
        print(f"URL: {direct_link[:120]}...")  # Показываем первые 120 символов
    except ValueError as e:
        print(f"Ошибка: {e}")
    except ConnectionError as e:
        print(f"Ошибка соединения: {e}")


if __name__ == "__main__":
    main()
