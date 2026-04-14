"""Провайдер для Яндекс.Диска.

Использует публичный REST API Яндекс.Диска для получения
прямой ссылки на скачивание файла по его публичной ссылке.

Документация API:
https://yandex.com/dev/disk/rest/

Ключевой эндпоинт (адрес API):
GET https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key=...

Этот эндпоинт не требует авторизации для публичных файлов.
Он возвращает JSON с полем 'href' — это и есть прямая ссылка.

Поддерживаемые форматы ссылок:
1. Прямая ссылка на файл:
   https://disk.yandex.ru/i/abc123
   https://yadi.sk/i/abc123

2. Ссылка на файл внутри публичной папки:
   https://disk.yandex.ru/d/abc123/Filename.mp4
   https://disk.yandex.ru/d/abc123/Subfolder/Filename.mp4

   В этом случае API принимает два параметра:
   - public_key: URL папки (https://disk.yandex.ru/d/abc123)
   - path: путь к файлу внутри папки (/Filename.mp4)
"""

import requests
from urllib.parse import urlparse, unquote

from providers.base import CloudProvider


# Адрес API Яндекс.Диска для получения ссылки на скачивание публичного файла.
YADISK_API_URL = "https://cloud-api.yandex.net/v1/disk/public/resources/download"


def _parse_yadisk_url(public_url: str) -> tuple[str, str | None]:
    """
    Разбирает публичную ссылку Яндекс.Диска на две части:
    1. public_key — базовая ссылка (на файл или на папку)
    2. path — относительный путь к файлу внутри папки (или None)

    Примеры:
        "https://disk.yandex.ru/i/abc123"
        → ("https://disk.yandex.ru/i/abc123", None)

        "https://disk.yandex.ru/d/abc123/C0019.MP4"
        → ("https://disk.yandex.ru/d/abc123", "/C0019.MP4")

        "https://disk.yandex.ru/d/abc123/Папка/Файл.mp4"
        → ("https://disk.yandex.ru/d/abc123", "/Папка/Файл.mp4")

    Как это работает:
    - Ссылки вида /i/KEY — это прямые ссылки на файл. Путь не нужен.
    - Ссылки вида /d/KEY — это ссылки на папку. Если после KEY есть
      ещё что-то (имя файла), это нужно передать как параметр path.
    """
    # Разбираем URL на составные части с помощью стандартной библиотеки.
    # Например, для "https://disk.yandex.ru/d/abc123/C0019.MP4":
    #   parsed.scheme = "https"
    #   parsed.netloc = "disk.yandex.ru"
    #   parsed.path   = "/d/abc123/C0019.MP4"
    parsed = urlparse(public_url)

    # Получаем путь и разбиваем его на части по символу "/"
    # "/d/abc123/C0019.MP4" → ["", "d", "abc123", "C0019.MP4"]
    path_parts = parsed.path.split("/")

    # Убираем пустые строки, которые появляются из-за "/" в начале
    # ["", "d", "abc123", "C0019.MP4"] → ["d", "abc123", "C0019.MP4"]
    path_parts = [p for p in path_parts if p]

    # Проверяем формат ссылки:
    # Если это /d/KEY/... и после KEY есть ещё части — это файл в папке
    if len(path_parts) >= 3 and path_parts[0] == "d":
        # Тип ссылки и ключ ресурса — первые два элемента: "d" и "abc123"
        # Всё остальное — путь к файлу внутри папки
        resource_type = path_parts[0]   # "d"
        resource_key = path_parts[1]    # "abc123"
        file_path_parts = path_parts[2:]  # ["C0019.MP4"] или ["Папка", "Файл.mp4"]

        # Собираем базовый URL папки обратно
        base_url = f"{parsed.scheme}://{parsed.netloc}/{resource_type}/{resource_key}"

        # Собираем путь к файлу (с ведущим слешем, как ожидает API)
        # unquote декодирует %20 и подобные символы обратно в нормальный текст
        file_path = "/" + "/".join(unquote(part) for part in file_path_parts)

        return base_url, file_path

    # Во всех остальных случаях (ссылка на файл /i/KEY, или просто /d/KEY без подпути)
    # — передаём всю ссылку как public_key, path не нужен
    return public_url, None


class YandexDiskProvider(CloudProvider):
    """
    Провайдер для Яндекс.Диска.

    Наследует CloudProvider (наш абстрактный шаблон) и реализует
    все его обязательные методы.
    """

    def get_provider_name(self) -> str:
        """Возвращает название провайдера."""
        return "Яндекс.Диск"

    def get_direct_link(self, public_url: str) -> str:
        """
        Получает прямую ссылку на скачивание файла с Яндекс.Диска.

        Как это работает:
        1. Разбираем ссылку пользователя: определяем, ведёт она на файл
           напрямую, или на файл внутри публичной папки.
        2. Отправляем GET-запрос к API Яндекс.Диска с нужными параметрами.
        3. API возвращает JSON вида: {"href": "https://...", "method": "GET", ...}
        4. Поле "href" — это и есть прямая ссылка на скачивание файла.

        Аргументы:
            public_url: Публичная ссылка на файл, например:
                        https://disk.yandex.ru/i/abc123
                        https://disk.yandex.ru/d/abc123/Video.mp4

        Возвращает:
            Строку с прямой ссылкой для скачивания.

        Выбрасывает:
            ValueError: Если ссылка некорректна, файл не найден или ответ API неожиданный.
            ConnectionError: Если не удалось связаться с сервером Яндекса.
        """
        # Проверяем, что ссылка не пустая
        if not public_url or not public_url.strip():
            raise ValueError("Ссылка не может быть пустой.")

        # Разбираем ссылку на public_key и path
        public_key, file_path = _parse_yadisk_url(public_url.strip())

        # Формируем параметры запроса к API
        params = {"public_key": public_key}

        # Если есть путь к файлу внутри папки — добавляем его
        if file_path is not None:
            params["path"] = file_path

        try:
            # Отправляем GET-запрос к API.
            # timeout=15 — ждём ответа не дольше 15 секунд.
            response = requests.get(
                YADISK_API_URL,
                params=params,
                timeout=15
            )

        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                "Не удалось подключиться к серверу Яндекс.Диска. "
                "Проверьте интернет-соединение."
            )
        except requests.exceptions.Timeout:
            raise ConnectionError(
                "Сервер Яндекс.Диска не ответил за 15 секунд. "
                "Попробуйте позже."
            )

        # Проверяем HTTP-код ответа.
        # 200 = всё OK. Другие коды — ошибка.
        if response.status_code == 404:
            raise ValueError(
                "Файл не найден. Проверьте, что ссылка правильная "
                "и файл доступен по публичной ссылке."
            )

        if response.status_code != 200:
            raise ValueError(
                f"Ошибка API Яндекс.Диска (код {response.status_code}). "
                f"Попробуйте позже или проверьте ссылку."
            )

        # Разбираем JSON-ответ
        data = response.json()

        # Извлекаем прямую ссылку из поля 'href'
        direct_link = data.get("href")

        if not direct_link:
            raise ValueError(
                "API Яндекс.Диска не вернул ссылку на скачивание. "
                "Возможно, ссылка ведёт на папку, а не на файл, "
                "или файл больше недоступен."
            )

        return direct_link
