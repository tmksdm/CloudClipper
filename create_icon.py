"""Скрипт для создания иконки приложения CloudClipper.

Генерирует файл assets/icon.ico — иконку с буквами "CC"
на синем фоне. Эта иконка используется:
  1. В заголовке окна приложения
  2. Как иконка .exe файла
  3. На панели задач Windows

Запуск: python create_icon.py
"""

import os
from PIL import Image, ImageDraw, ImageFont


def create_icon():
    """Создаёт иконку приложения и сохраняет как .ico файл."""

    # Создаём папку assets, если её нет
    os.makedirs("assets", exist_ok=True)

    # Размер иконки в пикселях.
    # Создаём большую (256x256), а формат .ico автоматически
    # включит уменьшенные версии (16x16, 32x32, 48x48 и т.д.)
    size = 256

    # Создаём изображение с прозрачным фоном
    # "RGBA" — формат с 4 каналами: Red, Green, Blue, Alpha (прозрачность)
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # ImageDraw — инструмент для рисования на изображении
    draw = ImageDraw.Draw(image)

    # --- Рисуем скруглённый синий фон ---
    # Цвет — как у кнопок в CustomTkinter (приятный синий)
    bg_color = (36, 140, 230, 255)  # RGBA: синий, полностью непрозрачный

    # Рисуем скруглённый прямоугольник (по сути — квадрат со скруглёнными углами)
    # radius — радиус скругления углов
    radius = 50
    draw.rounded_rectangle(
        [0, 0, size - 1, size - 1],  # Координаты: левый верхний и правый нижний угол
        radius=radius,
        fill=bg_color
    )

    # --- Рисуем символ ножниц ✂ (или буквы CC) ---
    # Попробуем использовать системный шрифт. Если не получится — используем встроенный.
    text = "CC"
    text_color = (255, 255, 255, 255)  # Белый

    # Пробуем загрузить шрифт Arial Bold (есть на всех Windows)
    font = None
    font_paths = [
        "C:/Windows/Fonts/arialbd.ttf",   # Arial Bold
        "C:/Windows/Fonts/arial.ttf",      # Arial обычный
        "C:/Windows/Fonts/segoeui.ttf",    # Segoe UI
    ]

    for path in font_paths:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, size=140)
                break
            except Exception:
                continue

    # Если шрифт не найден — используем встроенный (менее красивый, но работает)
    if font is None:
        font = ImageFont.load_default()

    # Вычисляем позицию текста, чтобы он был по центру
    # textbbox возвращает (left, top, right, bottom) — границы текста
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Координаты для центрирования
    x = (size - text_width) // 2 - bbox[0]
    y = (size - text_height) // 2 - bbox[1]

    # Рисуем текст
    draw.text((x, y), text, fill=text_color, font=font)

    # --- Сохраняем как .ico ---
    # Формат .ico может содержать несколько размеров одной иконки.
    # Windows автоматически выбирает нужный размер в зависимости от контекста:
    # - 16x16 для заголовка окна
    # - 32x32 для панели задач
    # - 48x48 и 256x256 для Проводника
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icon_path = os.path.join("assets", "icon.ico")

    image.save(icon_path, format="ICO", sizes=icon_sizes)

    print(f"Иконка создана: {icon_path}")
    print(f"Размер файла: {os.path.getsize(icon_path) / 1024:.0f} КБ")

    # --- Также сохраняем как .png (для заголовка окна) ---
    png_path = os.path.join("assets", "icon.png")
    # Сохраняем версию 32x32 для заголовка окна
    small_image = image.resize((32, 32), Image.Resampling.LANCZOS)
    small_image.save(png_path, format="PNG")
    print(f"PNG версия: {png_path}")


if __name__ == "__main__":
    create_icon()
