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
import sys
import threading
import tkinter as tk
import customtkinter as ctk
from config import DEFAULT_DOWNLOAD_PATH, APP_NAME, APP_VERSION
from providers.yadisk import YandexDiskProvider
from core.downloader import download_fragment
from core.utils import validate_url, validate_time_format, validate_time_range


def _get_resource_path(relative_path: str) -> str:
    """
    Возвращает правильный путь к файлу ресурса (иконка, картинка и т.д.).

    Зачем это нужно:
    Когда мы запускаем приложение как обычный Python-скрипт, файлы лежат
    в папке проекта. Но когда PyInstaller собирает .exe, он может
    поместить ресурсы во временную папку. Путь к этой папке хранится
    в специальной переменной sys._MEIPASS.

    Эта функция проверяет: если мы внутри .exe — ищет файл в папке
    PyInstaller. Если нет — ищет в обычной папке проекта.

    Аргументы:
        relative_path: Путь к файлу относительно корня проекта.
                       Например: "assets/icon.ico"

    Возвращает:
        Абсолютный путь к файлу.
    """
    # sys._MEIPASS — специальная переменная, которую создаёт PyInstaller.
    # Она указывает на временную папку, куда распакованы ресурсы.
    # Если этой переменной нет — значит, мы запущены как обычный скрипт.
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        # Обычный запуск из Python — файлы лежат в папке проекта.
        # os.path.dirname(__file__) — папка, где лежит этот файл (gui/).
        # os.path.dirname(...) ещё раз — папка на уровень выше (корень проекта).
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, relative_path)


def _get_inner_entry(ctk_entry):
    """
    Получает настоящий tk.Entry, скрытый внутри CTkEntry.

    CustomTkinter оборачивает стандартные виджеты tkinter в свои классы.
    CTkEntry — это не настоящее поле ввода, а «обёртка» с красивым
    оформлением. Внутри неё спрятан настоящий tk.Entry, который
    и обрабатывает ввод текста и события клавиатуры.

    Чтобы привязать обработчики клавиш, нам нужен именно этот
    внутренний виджет, потому что события клавиатуры приходят в него,
    а не в обёртку.

    Аргументы:
        ctk_entry: Виджет CTkEntry.

    Возвращает:
        Внутренний tk.Entry виджет.
    """
    return ctk_entry._entry


def _setup_hotkeys(ctk_entry):
    """
    Привязывает Ctrl+C/V/A/X так, чтобы они работали В ЛЮБОЙ раскладке.

    Проблема: tkinter привязывает горячие клавиши по «символу» клавиши
    (keysym). В русской раскладке символы другие (М вместо V, С вместо C),
    и tkinter их не распознаёт — keysym приходит как '??'.

    Решение: мы перехватываем ВСЕ нажатия клавиш (<Key>) на ВНУТРЕННЕМ
    виджете (настоящий tk.Entry внутри CTkEntry) и проверяем числовой
    код физической клавиши (keycode). Этот код не зависит от раскладки:
    клавиша V всегда имеет keycode=86, неважно, русская раскладка
    или английская.

    Важный нюанс: мы обрабатываем только случаи, когда keysym == '??'
    (то есть tkinter не распознал символ — значит раскладка не английская).
    Если keysym нормальный ('v', 'c' и т.д.) — значит стандартная
    обработка tkinter справится сама, и мы не вмешиваемся.

    Коды клавиш (Windows):
        keycode 65 = клавиша A (Ф в русской)
        keycode 67 = клавиша C (С в русской)
        keycode 86 = клавиша V (М в русской)
        keycode 88 = клавиша X (Ч в русской)

    Аргументы:
        ctk_entry: Виджет CTkEntry, к которому привязываем горячие клавиши.
    """
    # Получаем внутренний виджет — именно он принимает события клавиатуры
    inner = _get_inner_entry(ctk_entry)

    def on_key(event):
        """
        Обработчик ВСЕХ нажатий клавиш на внутреннем виджете.
        Срабатывает только когда:
          1) Зажат Ctrl
          2) keysym == '??' (tkinter не распознал символ = не английская раскладка)
        В этом случае определяем действие по keycode (физическому коду клавиши).
        """
        # Проверяем, зажат ли Ctrl.
        # event.state — число, в котором каждый бит = модификатор.
        # Бит 2 (значение 4) = Ctrl.
        ctrl_pressed = event.state & 4

        if not ctrl_pressed:
            return  # Ctrl не зажат — обычный ввод, не трогаем

        # Если keysym нормальный (не '??') — tkinter справится сам.
        # Мы вмешиваемся ТОЛЬКО когда tkinter не распознал клавишу.
        if event.keysym != '??':
            return  # Стандартная обработка tkinter, не мешаем

        # tkinter не распознал клавишу — определяем действие по keycode
        if event.keycode == 86:  # Клавиша V (М в русской)
            inner.event_generate("<<Paste>>")
            return "break"  # "break" = не передавать событие дальше

        if event.keycode == 67:  # Клавиша C (С в русской)
            inner.event_generate("<<Copy>>")
            return "break"

        if event.keycode == 65:  # Клавиша A (Ф в русской)
            inner.select_range(0, tk.END)
            return "break"

        if event.keycode == 88:  # Клавиша X (Ч в русской)
            inner.event_generate("<<Cut>>")
            return "break"

    # Привязываем обработчик к ВНУТРЕННЕМУ виджету
    inner.bind("<Key>", on_key)


def _setup_context_menu(ctk_entry):
    """
    Добавляет контекстное меню (правая кнопка мыши) к полю ввода.

    CustomTkinter не создаёт контекстное меню автоматически,
    поэтому мы делаем его вручную. Меню содержит стандартные пункты:
    «Вырезать», «Копировать», «Вставить», «Выделить всё».

    Привязываем меню к внутреннему виджету (tk.Entry), потому что
    именно он получает события мыши.

    Аргументы:
        ctk_entry: Виджет CTkEntry, к которому добавляем меню.
    """
    inner = _get_inner_entry(ctk_entry)

    # Создаём всплывающее меню. tearoff=0 убирает пунктирную линию сверху.
    menu = tk.Menu(inner, tearoff=0)
    menu.add_command(label="Вырезать", command=lambda: inner.event_generate("<<Cut>>"))
    menu.add_command(label="Копировать", command=lambda: inner.event_generate("<<Copy>>"))
    menu.add_command(label="Вставить", command=lambda: inner.event_generate("<<Paste>>"))
    menu.add_separator()
    menu.add_command(label="Выделить всё", command=lambda: inner.select_range(0, tk.END))

    def show_menu(event):
        """Показывает меню в позиции курсора мыши."""
        inner.focus_set()
        menu.tk_popup(event.x_root, event.y_root)

    # Привязываем к правой кнопке мыши на внутреннем виджете
    inner.bind("<Button-3>", show_menu)


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

        # --- Устанавливаем иконку окна ---
        self._set_app_icon()

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

        # Флаг: идёт ли сейчас скачивание. Нужен, чтобы не запускать
        # повторное скачивание, если пользователь как-то нажмёт кнопку дважды.
        self._is_downloading = False

        # Создаём все элементы интерфейса
        self._create_widgets()

    def _set_app_icon(self):
        """
        Устанавливает иконку приложения в заголовке окна и на панели задач.

        Иконка загружается из файла assets/icon.ico.
        Если файл не найден — просто пропускаем (окно будет со стандартной иконкой).
        """
        try:
            icon_path = _get_resource_path(os.path.join("assets", "icon.ico"))
            if os.path.exists(icon_path):
                # iconbitmap — метод tkinter для установки иконки окна.
                # Он принимает путь к .ico файлу.
                self.iconbitmap(icon_path)
        except Exception:
            # Если что-то пошло не так — не критично, просто будет стандартная иконка
            pass

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
        # wraplength — максимальная ширина текста в пикселях, после чего
        # текст переносится на следующую строку. Это нужно для длинных
        # сообщений об ошибках — без этого текст может выйти за окно.
        self.label_status = ctk.CTkLabel(
            self,
            text="Готов к работе",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            wraplength=550
        )
        self.label_status.pack(pady=(0, 10))

        # === Настраиваем горячие клавиши и контекстное меню ===
        # Применяем ко всем полям ввода, куда пользователь может вводить текст.
        # Поле папки (entry_folder) пропускаем — оно только для чтения.
        for entry in [self.entry_url, self.entry_start, self.entry_end]:
            _setup_hotkeys(entry)
            _setup_context_menu(entry)

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
    #  Валидация ввода
    # ──────────────────────────────────────────────

    def _validate_inputs(self, url: str, start_time: str, end_time: str) -> str | None:
        """
        Последовательно проверяет все поля ввода.

        Проверки идут в порядке приоритета:
        1. Ссылка — не пустая, похожа на Яндекс.Диск
        2. Время начала — заполнено, правильный формат
        3. Время конца — заполнено, правильный формат
        4. Начало < конца

        Аргументы:
            url:        Текст из поля ссылки.
            start_time: Текст из поля «Начало».
            end_time:   Текст из поля «Конец».

        Возвращает:
            None — если все проверки пройдены (ошибок нет).
            Строку с первой найденной ошибкой — если что-то не так.
        """
        # Проверка ссылки
        url_error = validate_url(url)
        if url_error:
            return url_error

        # Проверка формата времени начала
        start_error = validate_time_format(start_time, "начала")
        if start_error:
            return start_error

        # Проверка формата времени конца
        end_error = validate_time_format(end_time, "конца")
        if end_error:
            return end_error

        # Проверка: начало < конец
        range_error = validate_time_range(start_time, end_time)
        if range_error:
            return range_error

        # Всё в порядке
        return None

    # ──────────────────────────────────────────────
    #  Скачивание фрагмента
    # ──────────────────────────────────────────────

    def _on_download_click(self):
        """
        Обработчик нажатия кнопки «Скачать фрагмент».

        Считывает данные из полей ввода, запускает валидацию,
        и если всё в порядке — запускает скачивание в отдельном потоке.
        """
        # Защита от повторного нажатия
        if self._is_downloading:
            return

        # --- 1. Считываем данные из полей ---
        url = self.entry_url.get().strip()
        start_time = self.entry_start.get().strip()
        end_time = self.entry_end.get().strip()
        folder = self.download_folder.get()

        # --- 2. Валидация всех полей ---
        error = self._validate_inputs(url, start_time, end_time)
        if error:
            self._set_status(f"⚠ {error}", "red")
            return

        # --- 3. Проверяем, что папка для сохранения существует ---
        if not os.path.isdir(folder):
            self._set_status("⚠ Папка для сохранения не найдена. Выберите другую.", "red")
            return

        # --- 4. Блокируем интерфейс и запускаем скачивание ---
        self._is_downloading = True
        self._set_ui_enabled(False)
        self._set_status("⏳ Получаем ссылку на скачивание...", "orange")

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
                "⏳ Скачиваем фрагмент через FFmpeg...", "orange"
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

        except ValueError as e:
            # Ошибки валидации или API (неверная ссылка, файл не найден и т.д.)
            error_msg = str(e)
            self.after(0, lambda: self._on_download_error(error_msg))

        except ConnectionError as e:
            # Ошибки сети (нет интернета, сервер не отвечает)
            error_msg = str(e)
            self.after(0, lambda: self._on_download_error(error_msg))

        except RuntimeError as e:
            # Ошибки FFmpeg (не найден, вернул ошибку)
            error_msg = str(e)
            self.after(0, lambda: self._on_download_error(error_msg))

        except Exception as e:
            # Любая другая непредвиденная ошибка.
            # Это «ловушка на всякий случай» — чтобы приложение не падало молча.
            error_msg = f"Непредвиденная ошибка: {e}"
            self.after(0, lambda: self._on_download_error(error_msg))

    def _on_download_success(self, saved_path: str):
        """
        Вызывается в главном потоке после успешного скачивания.
        Показывает сообщение об успехе и разблокирует интерфейс.
        """
        # Показываем только имя файла, а не полный путь (он может быть длинным)
        filename = os.path.basename(saved_path)
        self._set_status(f"✅ Готово! Сохранено: {filename}", "green")
        self._set_ui_enabled(True)
        self._is_downloading = False
        print(f"[OK] Файл сохранён: {saved_path}")

    def _on_download_error(self, error_msg: str):
        """
        Вызывается в главном потоке при ошибке скачивания.
        Показывает сообщение об ошибке и разблокирует интерфейс.
        """
        self._set_status(f"❌ {error_msg}", "red")
        self._set_ui_enabled(True)
        self._is_downloading = False
        print(f"[ОШИБКА] {error_msg}")
