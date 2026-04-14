"""Точка входа приложения CloudClipper.

Этот файл запускает главное окно приложения.
Вся логика интерфейса находится в gui/app.py.
"""

from core.utils import check_ffmpeg
from gui.app import App


def main():
    """Главная функция — запускает приложение."""
    print("CloudClipper запущен")
    print()

    # Проверяем, установлен ли FFmpeg
    ffmpeg_ok = check_ffmpeg()
    if not ffmpeg_ok:
        print()
        print("Приложение не может работать без FFmpeg.")
        input("Нажмите Enter для выхода...")
        return

    print()
    print("Запускаем графический интерфейс...")
    print()

    # Создаём и запускаем окно приложения.
    # app.mainloop() — это бесконечный цикл, который держит окно открытым
    # и обрабатывает все действия пользователя (нажатия кнопок, ввод текста и т.д.).
    # Программа «живёт» внутри mainloop(), пока пользователь не закроет окно.
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
