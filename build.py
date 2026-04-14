"""Скрипт сборки CloudClipper в .exe с помощью PyInstaller.

Этот файл запускает PyInstaller с нужными параметрами.
Запуск: python build.py

После сборки готовый .exe будет лежать в папке dist/CloudClipper/.
Рядом с ним — папка ffmpeg/ с ffmpeg.exe (встроенный).
"""

import subprocess
import sys
import os
import shutil


def build():
    """Запускает PyInstaller для сборки приложения."""

    # --- Проверяем наличие необходимых файлов ---

    icon_path = os.path.join("assets", "icon.ico")
    if not os.path.exists(icon_path):
        print("ОШИБКА: Файл иконки не найден!")
        print(f"Ожидался файл: {icon_path}")
        print("Сначала запустите: python create_icon.py")
        return 1

    ffmpeg_source = os.path.join("ffmpeg", "ffmpeg.exe")
    if not os.path.exists(ffmpeg_source):
        print("ОШИБКА: FFmpeg не найден в папке ffmpeg/!")
        print(f"Ожидался файл: {ffmpeg_source}")
        print()
        print("Скопируйте ffmpeg.exe в папку ffmpeg/ проекта.")
        print("Чтобы узнать, где он установлен: where ffmpeg")
        return 1

    # Параметры PyInstaller:
    #
    # main.py              — точка входа (наш главный файл)
    #
    # --name CloudClipper  — имя выходного .exe файла
    #
    # --windowed           — НЕ показывать чёрное окно консоли при запуске.
    #
    # --onedir             — собрать как папку (в ней .exe + все библиотеки).
    #
    # --noconfirm          — перезаписывать без вопросов.
    #
    # --clean              — очистить временные файлы перед сборкой.
    #
    # --icon               — иконка для .exe файла.
    #
    # --add-data           — дополнительные файлы для включения в сборку.
    #                        Формат: "источник;папка_назначения"
    #
    # --collect-all customtkinter
    #                      — собрать все файлы CustomTkinter (темы, картинки).

    command = [
        sys.executable, "-m", "PyInstaller",
        "main.py",
        "--name", "CloudClipper",
        "--windowed",
        "--onedir",
        "--noconfirm",
        "--clean",
        "--icon", icon_path,
        "--add-data", f"assets{os.pathsep}assets",
        "--collect-all", "customtkinter",
    ]

    print("=" * 60)
    print("  Сборка CloudClipper")
    print("=" * 60)
    print()
    print("Команда:")
    print(" ".join(command))
    print()

    # Запускаем PyInstaller
    result = subprocess.run(command)

    if result.returncode != 0:
        print()
        print("=" * 60)
        print(f"  ОШИБКА сборки (код {result.returncode})")
        print("=" * 60)
        return result.returncode

    # --- Копируем FFmpeg в папку дистрибутива ---
    # PyInstaller создаёт dist/CloudClipper/. Внутри неё лежит .exe
    # и все библиотеки. Мы добавляем папку ffmpeg/ рядом с .exe,
    # чтобы приложение нашло FFmpeg через get_ffmpeg_path().
    dist_ffmpeg_dir = os.path.join("dist", "CloudClipper", "ffmpeg")
    os.makedirs(dist_ffmpeg_dir, exist_ok=True)

    dist_ffmpeg_path = os.path.join(dist_ffmpeg_dir, "ffmpeg.exe")
    print(f"Копируем FFmpeg: {ffmpeg_source} → {dist_ffmpeg_path}")
    shutil.copy2(ffmpeg_source, dist_ffmpeg_path)

    # Проверяем размер FFmpeg
    ffmpeg_size_mb = os.path.getsize(dist_ffmpeg_path) / (1024 * 1024)
    print(f"Размер FFmpeg: {ffmpeg_size_mb:.0f} МБ")

    print()
    print("=" * 60)
    print("  Сборка завершена УСПЕШНО!")
    print(f"  Папка: dist/CloudClipper/")
    print(f"  Запуск: dist/CloudClipper/CloudClipper.exe")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(build())
