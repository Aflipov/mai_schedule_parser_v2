# backend/app/parsers/schedule_parser.py
from bs4 import BeautifulSoup
from datetime import datetime
import re
import logging
from pydantic import BaseModel
from typing import List, Optional

logger = logging.getLogger(__name__)

# Define Pydantic model for lesson data
class ParsedLesson(BaseModel):
    subject: str
    teacher: str
    classroom: str
    start_time: datetime
    end_time: datetime
    lesson_type: str
    group: str


def parse_schedule(html_content: str) -> List[ParsedLesson]:
    """
    Parses HTML schedule content and returns a list of ParsedLesson objects.
    """

    eng_months = {
        'января': 1,
        'февраля': 2,
        'марта': 3,
        'апреля': 4,
        'мая': 5,
        'ибня': 6,
        'июля': 7,
        'августа': 8,
        'сентября': 9,
        'октября': 10,
        'ноября': 11,
        'декабря': 12
    }

    soup = BeautifulSoup(html_content, 'html.parser')

    try:
        group = soup.find(itemprop='headline').text
        group = re.sub(r'[\n\t]', '', group)
    except AttributeError as e:  # Specific exception
        logger.error(f"Не удалось извлечь название группы: {e}")
        return []

    days = soup.find(class_='step mb-5').find_all(class_='step-item')

    if not days:
        logger.warning('[parser.py]Тег step mb-5 или step-item не найден')
        return []

    schedule: List[ParsedLesson] = []
    current_year = datetime.datetime.now().year  # Get current year

    for day in days:
        date_element = day.find(class_="step-content").find('span')
        if not date_element:
            logger.warning("Не найден элемент даты для дня")
            continue

        date_text = date_element.text
        date_text = re.sub(r'[\n\t]', '', date_text)
        date_text = re.sub(r'[\xa0]', ' ', date_text)[4:].split()

        for lesson in days.select("div[class='mb-4']"):
            try:
                lesson_title = lesson.find('div').text
                lesson_content = [x.text for x in lesson.find('ul').find_all('li')]
                lesson_content = [re.sub(r'[\n\t]', '', item) for item in lesson_content]

                lesson_title = re.sub(r'[\n\t]', '', lesson_title)
                lesson_subject = lesson_title[:-2]
                lesson_type = lesson_title[-2:]

                # Parse time with current year
                lesson_start_time = datetime.datetime.strptime(
                    f'{current_year} {eng_months[date_text[1]]} {date_text[0]} {lesson_content[0][:5]}',
                    '%Y %m %d %H:%M'
                )
                lesson_end_time = datetime.datetime.strptime(
                    f'{current_year} {eng_months[date_text[1]]} {date_text[0]} {lesson_content[0][8:]}',
                    '%Y %m %d %H:%M'
                )

                lesson_teacher = ' | '.join(lesson_content[1:-1]) if len(lesson_content) > 2 else 'Преподаватель не указан'
                lesson_classroom = lesson_content[-1]

                parsed_lesson = ParsedLesson(
                    subject=lesson_subject,
                    teacher=lesson_teacher,
                    classroom=lesson_classroom,
                    start_time=lesson_start_time,
                    end_time=lesson_end_time,
                    lesson_type=lesson_type,
                    group=group
                )
                schedule.append(parsed_lesson)
            except (AttributeError, ValueError) as e:
                logger.error(f"Ошибка при парсинге урока: {e}") # Log the exception
                continue # skip the problematic lesson

    return schedule