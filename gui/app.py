"""Главное окно приложения CloudClipper.

Здесь описан графический интерфейс (GUI) на библиотеке CustomTkinter.
CustomTkinter — это надстройка над стандартным tkinter, которая делает
окна более современными и красивыми.

Структура окна:
    ┌─────────────────────────────────────┐
    │  CloudClipper                       │
    │                                     │
    │  Ссылка на видео: [_______________] │
    │                                     │
    │  Начало: [______]  Конец: [______]  │
    │                                     │
    │  Папка: /Users/.../Downloads [...]  │
    │                                     │
    │  [ ★ Скачать фрагмент ]            │
    │                                     │
    │  Статус: Готов к работе             │
    └─────────────────────────────────────┘
"""

import os
import threading
import customtkinter as ctk
from config import DEFAULT_DOWNLOAD_PATH, APP_NAME, APP_VERSION
from providers.yadisk import YandexDiskProvider
from core.downloader import download_fragment


class App(ctk.CTk):
    """
    Главное окно приложения.

    ctk.CTk — это базовый класс для окна в CustomTkinter.
    Мы наследуем от него (создаём свой класс на его основе)
    и добавляем все наши элементы: поля ввода, кнопки и т.д.
    """

    def __init__(self):
        """
        Инициализация окна — вызывается один раз при создании.
        Здесь мы настраиваем размер окна, цвета, и создаём все элементы.
        """
        # Вызываем __init__ родительского класса (ctk.CTk).
        # Это обязательно — без этого окно не создастся.
        super().__init__()

        # --- Настройки окна ---
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("600x420")            # Ширина x Высота в пикселях
        self.minsize(500, 400)              # Минимальный размер окна
        self.resizable(True, True)          # Можно менять размер

        # Тема оформления: "dark" (тёмная), "light" (светлая), "system" (как в системе)
        ctk.set_appearance_mode("system")
        # Цветовая схема: "blue", "green", "dark-blue"
        ctk.set_default_color_theme("blue")

        # Папка для сохранения — по умолчанию «Загрузки»
        # StringVar — это специальная переменная CustomTkinter/tkinter,
        # которая автоматически обновляет текст в привязанном элементе.
        self.download_folder = ctk.StringVar(value=DEFAULT_DOWNLOAD_PATH)

        # Провайдер Яндекс.Диска — создаём один раз, используем многократно
        self.provider = YandexDiskProvider()

        # Создаём все элементы интерфейса
        self._create_widgets()

    def _create_widgets(self):
        """
        Создаёт и размещает все элементы интерфейса.

        Мы используем метод .pack() для размещения элементов.
        pack() ставит элементы друг за другом сверху вниз.
        padx/pady — отступы по горизонтали/вертикали в пикселях.
        """

        # === Заголовок ===
        # CTkLabel — это текстовая надпись.
        self.label_title = ctk.CTkLabel(
            self,                           # Родитель — само окно (self)
            text="CloudClipper",
            font=ctk.CTkFont(size=24, weight="bold")  # Крупный жирный шрифт
        )
        self.label_title.pack(pady=(20, 5))  # Отступ: 20 сверху, 5 снизу

        self.label_subtitle = ctk.CTkLabel(
            self,
            text="Скачивание фрагментов видео из облачных хранилищ",
            font=ctk.CTkFont(size=12),
            text_color="gray"               # Серый цвет — это подзаголовок
        )
        self.label_subtitle.pack(pady=(0, 15))

        # === Поле ввода: ссылка ===
        # CTkEntry — это поле ввода текста (одна строка).
        # placeholder_text — подсказка, которая исчезает при вводе.
        self.entry_url = ctk.CTkEntry(
            self,
            placeholder_text="Вставьте публичную ссылку на видео (Яндекс.Диск)",
            width=500,
            height=38
        )
        self.entry_url.pack(pady=(0, 15))

        # === Блок времени: начало и конец ===
        # CTkFrame — это контейнер (рамка), который группирует элементы.
        # Мы помещаем два поля ввода в одну строку.
        self.frame_time = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_time.pack(pady=(0, 15))

        # Надпись "Начало:"
        self.label_start = ctk.CTkLabel(
            self.frame_time,
            text="Начало:",
            font=ctk.CTkFont(size=13)
        )
        self.label_start.pack(side="left", padx=(0, 5))  # side="left" — в ряд слева

        # Поле ввода времени начала
        self.entry_start = ctk.CTkEntry(
            self.frame_time,
            placeholder_text="0:00",
            width=100,
            height=34
        )
        self.entry_start.pack(side="left", padx=(0, 20))

        # Надпись "Конец:"
        self.label_end = ctk.CTkLabel(
            self.frame_time,
            text="Конец:",
            font=ctk.CTkFont(size=13)
        )
        self.label_end.pack(side="left", padx=(0, 5))

        # Поле ввода времени конца
        self.entry_end = ctk.CTkEntry(
            self.frame_time,
            placeholder_text="1:00",
            width=100,
            height=34
        )
        self.entry_end.pack(side="left")

        # === Блок выбора папки ===
        self.frame_folder = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_folder.pack(pady=(0, 15))

        self.label_folder = ctk.CTkLabel(
            self.frame_folder,
            text="Папка:",
            font=ctk.CTkFont(size=13)
        )
        self.label_folder.pack(side="left", padx=(0, 5))

        # Поле, показывающее выбранную папку.
        # textvariable=self.download_folder — привязка к переменной.
        # Когда переменная изменится, текст в поле обновится автоматически.
        self.entry_folder = ctk.CTkEntry(
            self.frame_folder,
            textvariable=self.download_folder,
            width=350,
            height=34,
            state="readonly"                # Только для чтения — нельзя вписать вручную
        )
        self.entry_folder.pack(side="left", padx=(0, 10))

        # Кнопка "Обзор..." — открывает диалог выбора папки
        self.button_browse = ctk.CTkButton(
            self.frame_folder,
            text="Обзор...",
            width=80,
            height=34,
            command=self._choose_folder     # Какую функцию вызвать при нажатии
        )
        self.button_browse.pack(side="left")

        # === Кнопка «Скачать фрагмент» ===
        self.button_download = ctk.CTkButton(
            self,
            text="Скачать фрагмент",
            width=250,
            height=42,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._on_download_click
        )
        self.button_download.pack(pady=(5, 15))

        # === Статусная строка ===
        self.label_status = ctk.CTkLabel(
            self,
            text="Готов к работе",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.label_status.pack(pady=(0, 10))

    # ──────────────────────────────────────────────
    #  Методы обновления интерфейса
    # ──────────────────────────────────────────────

    def _set_status(self, text: str, color: str = "gray"):
        """
        Обновляет текст и цвет статусной строки.

        Аргументы:
            text:  Текст для отображения.
            color: Цвет текста. Примеры: "gray", "white", "green", "red", "orange".
        """
        self.label_status.configure(text=text, text_color=color)

    def _set_ui_enabled(self, enabled: bool):
        """
        Включает или отключает все поля ввода и кнопки.

        Зачем: во время скачивания нужно заблокировать интерфейс,
        чтобы пользователь не нажал кнопку повторно и не изменил данные.
        Когда скачивание закончится — разблокируем обратно.

        Аргументы:
            enabled: True = всё активно, False = всё заблокировано.
        """
        # В tkinter/customtkinter состояние элемента задаётся параметром state:
        # "normal" — активный (можно нажимать/вводить)
        # "disabled" — неактивный (серый, нельзя нажать)
        state = "normal" if enabled else "disabled"

        self.entry_url.configure(state=state)
        self.entry_start.configure(state=state)
        self.entry_end.configure(state=state)
        self.button_browse.configure(state=state)
        self.button_download.configure(state=state)

    # ──────────────────────────────────────────────
    #  Выбор папки
    # ──────────────────────────────────────────────

    def _choose_folder(self):
        """
        Открывает системный диалог выбора папки.

        filedialog.askdirectory() — стандартная функция tkinter,
        которая показывает окно «Выберите папку».
        Если пользователь выбрал папку — обновляем переменную.
        Если нажал «Отмена» — ничего не делаем.
        """
        from tkinter import filedialog

        folder = filedialog.askdirectory(
            title="Выберите папку для сохранения",
            initialdir=self.download_folder.get()  # Начальная папка в диалоге
        )

        # Если пользователь выбрал папку (не нажал «Отмена»)
        if folder:
            self.download_folder.set(folder)

    # ──────────────────────────────────────────────
    #  Скачивание фрагмента
    # ──────────────────────────────────────────────

    def _on_download_click(self):
        """
        Обработчик нажатия кнопки «Скачать фрагмент».

        Считывает данные из полей ввода, проверяет, что они заполнены,
        и запускает скачивание в отдельном потоке (чтобы окно не зависло).
        """
        # --- 1. Считываем данные из полей ---
        url = self.entry_url.get().strip()
        start_time = self.entry_start.get().strip()
        end_time = self.entry_end.get().strip()
        folder = self.download_folder.get()

        # --- 2. Простая проверка: все поля заполнены? ---
        if not url:
            self._set_status("Ошибка: вставьте ссылку на видео", "red")
            return

        if not start_time:
            self._set_status("Ошибка: укажите время начала", "red")
            return

        if not end_time:
            self._set_status("Ошибка: укажите время конца", "red")
            return

        # --- 3. Блокируем интерфейс и запускаем скачивание ---
        self._set_ui_enabled(False)
        self._set_status("Получаем ссылку на скачивание...", "orange")

        # threading.Thread — это способ запустить функцию параллельно.
        # daemon=True означает: если пользователь закроет окно, поток тоже завершится.
        thread = threading.Thread(
            target=self._download_thread,    # Какую функцию запустить
            args=(url, start_time, end_time, folder),  # Аргументы для неё
            daemon=True
        )
        thread.start()

    def _download_thread(self, url: str, start_time: str, end_time: str, folder: str):
        """
        Выполняет скачивание в отдельном потоке.

        ВАЖНО: Из отдельного потока НЕЛЬЗЯ напрямую менять элементы интерфейса.
        Tkinter работает только в главном потоке. Если мы попробуем изменить
        текст кнопки или статусной строки из другого потока — программа может
        упасть или вести себя непредсказуемо.

        Решение: self.after(0, функция) — это способ попросить главный поток
        выполнить функцию при первой возможности. Это как передать записку
        продавцу: «Когда будет минутка, обнови вывеску».

        Аргументы:
            url:        Публичная ссылка на видео.
            start_time: Время начала фрагмента (строка).
            end_time:   Время конца фрагмента (строка).
            folder:     Папка для сохранения файла.
        """
        try:
            # --- Шаг 1: Получаем прямую ссылку ---
            direct_url = self.provider.get_direct_link(url)
            print(f"[DEBUG] Прямая ссылка получена")

            # Обновляем статус (через главный поток!)
            self.after(0, lambda: self._set_status(
                "Скачиваем фрагмент через FFmpeg...", "orange"
            ))

            # --- Шаг 2: Формируем путь для сохранения ---
            # Имя файла: fragment_НАЧАЛО_КОНЕЦ.mp4
            # Заменяем ":" на "-", чтобы имя было допустимым в Windows
            safe_start = start_time.replace(":", "-")
            safe_end = end_time.replace(":", "-")
            filename = f"fragment_{safe_start}_{safe_end}.mp4"
            output_path = os.path.join(folder, filename)

            # --- Шаг 3: Скачиваем фрагмент ---
            saved_path = download_fragment(direct_url, start_time, end_time, output_path)

            # --- Шаг 4: Успех! ---
            self.after(0, lambda: self._on_download_success(saved_path))

        except (ValueError, ConnectionError, RuntimeError) as e:
            # Если произошла ошибка — показываем её
            error_msg = str(e)
            self.after(0, lambda: self._on_download_error(error_msg))

    def _on_download_success(self, saved_path: str):
        """
        Вызывается в главном потоке после успешного скачивания.
        Показывает сообщение об успехе и разблокирует интерфейс.
        """
        # Показываем только имя файла, а не полный путь (он может быть длинным)
        filename = os.path.basename(saved_path)
        self._set_status(f"Готово! Сохранено: {filename}", "green")
        self._set_ui_enabled(True)
        print(f"[OK] Файл сохранён: {saved_path}")

    def _on_download_error(self, error_msg: str):
        """
        Вызывается в главном потоке при ошибке скачивания.
        Показывает сообщение об ошибке и разблокирует интерфейс.
        """
        self._set_status(f"Ошибка: {error_msg}", "red")
        self._set_ui_enabled(True)
        print(f"[ОШИБКА] {error_msg}")
