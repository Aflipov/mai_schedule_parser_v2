import urllib.parse
import httpx
import os
import cachetools
import logging
from .. import config

logger = logging.getLogger(__name__)

CACHE_DIR = config.CACHE_DIR
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

cache = cachetools.TTLCache(maxsize=config.CACHE_MAX_SIZE, ttl=config.CACHE_TTL)


def url_gen(group_number: str, week_number: int):
    return f'https://mai.ru/education/studies/schedule/index.php?group={urllib.parse.quote(group_number)}&week={week_number}'

def get_html(client: httpx.Client, group_number: str, week_number: int):
    """
    Загружает HTML-контент страницы расписания.

    Args:
        client: httpx.Client session.
        group_number: Номер группы.
        week_number: Номер недели.

    Returns:
        HTML-контент страницы в виде строки или None в случае ошибки.
    """
    url = url_gen(group_number, week_number)
    cache_key = f"{group_number}-{week_number}"  # Add week_number to cache key

    try:
        if cache_key in cache:
            logger.info(f"Загрузка из кэша: {cache_key}")
            return cache[cache_key]

        headers = {"User-Agent": config.USER_AGENT}  # Add User-Agent
        r = client.get(url, headers=headers)
        r.raise_for_status()  # Check HTTP status code

        html = r.text

        logger.info(f"Загрузка с сайта: {cache_key}")
        cache[cache_key] = html
        return html
    except httpx.RequestError as e:  # Catch specific exceptions
        logger.error(f"Ошибка при запросе к {url}: {e}")
        return None
    except httpx.HTTPStatusError as e:
        logger.error(f"Ошибка HTTP {e.response.status_code} при запросе к {url}")
        return None
    except Exception as e:
        logger.error(f"Неизвестная ошибка при загрузке HTML: {e}")
        return None