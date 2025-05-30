import logging
from sqlalchemy.orm import Session
import asyncio
import httpx
import atexit
from . import database
from .parsers.schedule_parser import parse_schedule, ParsedLesson
from .parsers.schedule_downloader import url_gen, get_html

logger = logging.getLogger(__name__)

async def scrape_schedule_async(session: Session, client: httpx.AsyncClient, group_number: str, week_number: int) -> None:
    """
    Загружает, парсит и сохраняет расписание для заданной группы и недели.
    """
    html = await get_html(client, group_number, week_number)
    if html:
        schedule = parse_schedule(html)
        if schedule:
            schedule_upload(session, schedule)
            logger.info(f"Успешно загружено расписание для группы {group_number}, неделя {week_number}")
        else:
            logger.error(f"Не удалось распарсить расписание для группы {group_number}, неделя {week_number}")
    else:
        logger.error(f"Не удалось загрузить расписание для группы {group_number}, неделя {week_number}")

async def scrape_and_update_all_schedules_async(session: Session, client: httpx.AsyncClient, group_numbers: list[str], week_numbers: list[int]) -> None:
    """
    Загружает, парсит и сохраняет расписание для всех указанных групп и недель.
    """
    tasks = [scrape_schedule_async(session, client, g, w) for g in group_numbers for w in week_numbers]
    await asyncio.gather(*tasks)

def lesson_upload(session: Session, lesson: ParsedLesson) -> None:  # Use ParsedLesson
    subject = database.add_subject(session, lesson.subject)
    teacher = database.add_teacher(session, lesson.teacher)
    classroom = database.add_classroom(session, lesson.classroom)
    start_time = lesson.start_time
    end_time = lesson.end_time
    lesson_type = lesson.lesson_type
    group = database.add_group(session, lesson.group)

    try:
        database.add_lesson(session, subject, teacher, classroom, start_time, end_time, lesson_type, group)
        session.commit()
        logger.info(f"Урок '{subject.name}' добавлен.")
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при добавлении урока: {e}")

def schedule_upload(session: Session, schedule: list[ParsedLesson]) -> None:
    if not schedule:
        logger.warning("Попытка загрузить пустое расписание.")
        return

    # 1. Получаем минимальную и максимальную даты из расписания
    dates = set(lesson.start_time.date() for lesson in schedule)
    start_date = min(dates)
    end_date = max(dates)

    group_number: str = schedule[0].group

    # 2. Удаляем старые записи для группы и диапазона дат
    group = database.add_group(session, group_number)
    database.delete_lessons_by_group_and_date_range(session, group, start_date, end_date)

    for lesson in schedule:
        lesson_upload(session, lesson)