"""Точка входа приложения CloudClipper."""

from core.utils import check_ffmpeg


def main():
    """Главная функция — запускает приложение."""
    print("CloudClipper запущен")
    print()

    # Проверяем, установлен ли FFmpeg
    check_ffmpeg()


if __name__ == "__main__":
    main()
