from sqlalchemy import create_engine, DateTime, Date, func, select
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.exc import IntegrityError
from contextlib import contextmanager
import datetime
import logging
from . import config
from . import db_models as dbm

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = config.DATABASE_URL
ECHO = config.ECHO

engine = create_engine(DATABASE_URL, echo=ECHO)

Base = declarative_base()

def create_db() -> None:
    """Создает базу данных и таблицы."""
    try:
        dbm.Base.metadata.create_all(engine)
        logger.info("База данных успешно создана.")
    except Exception as e:
        logger.error(f"Ошибка при создании базы данных: {e}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_session():
    """Context manager для управления сессией."""
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при работе с базой данных: {e}")
        raise
    finally:
        db.close()

create_db()

# Функции для добавления данных
def add_subject(session: Session, name: str) -> dbm.Subject:
    """Adds a subject if it doesn't exist."""
    stmt = select(dbm.Subject).filter_by(name=name)
    existing_subject = session.execute(stmt).scalar_one_or_none()
    if existing_subject:
        logger.info(f"Subject '{name}' already exists.")
        return existing_subject
    subject = dbm.Subject(name=name)
    session.add(subject)
    logger.info(f"Subject '{name}' added.")
    return subject

def add_teacher(session: Session, name: str) -> dbm.Teacher:
    """Adds a teacher if it doesn't exist."""
    stmt = select(dbm.Teacher).filter_by(name=name)
    existing_teacher = session.execute(stmt).scalar_one_or_none()
    if existing_teacher:
        logger.info(f"Teacher '{name}' already exists.")
        return existing_teacher
    teacher = dbm.Teacher(name=name)
    session.add(teacher)
    logger.info(f"Teacher '{name}' added.")
    return teacher

def add_classroom(session: Session, name: str) -> dbm.Classroom:
    """Adds a classroom if it doesn't exist."""
    stmt = select(dbm.Classroom).filter_by(name=name)
    existing_classroom = session.execute(stmt).scalar_one_or_none()
    if existing_classroom:
        logger.info(f"Classroom '{name}' already exists.")
        return existing_classroom
    classroom = dbm.Classroom(name=name)
    session.add(classroom)
    logger.info(f"Classroom '{name}' added.")
    return classroom

def add_group(session: Session, name: str) -> dbm.Group:
    """Adds a group if it doesn't exist."""
    stmt = select(dbm.Group).filter_by(name=name)
    existing_group = session.execute(stmt).scalar_one_or_none()
    if existing_group:
        logger.info(f"Group '{name}' already exists.")
        return existing_group
    group = dbm.Group(name=name)
    session.add(group)
    logger.info(f"Group '{name}' added.")
    return group

def add_lesson(session: Session, subject: dbm.Subject, teacher: dbm.Teacher,
               classroom: dbm.Classroom, start_time: DateTime,
               end_time: DateTime, lesson_type: str,
               group: dbm.Group) -> None:
    """Adds a lesson to the database."""
    lesson = dbm.Lesson(subject=subject, teacher=teacher, classroom=classroom, start_time=start_time, end_time=end_time, lesson_type=lesson_type, group=group)
    session.add(lesson)
    try:
        session.commit()
        logger.info(f"Lesson '{subject.name}' added.")
    except IntegrityError as e:
        session.rollback()
        logger.warning(f"Lesson '{subject.name}' already exists: {e}")

def add_or_update_lesson(session: Session, subject: dbm.Subject, teacher: dbm.Teacher,
                       classroom: dbm.Classroom, start_time: DateTime,
                       end_time: DateTime, lesson_type: str,
                       group: dbm.Group) -> dbm.Lesson:
    """Adds a lesson if it doesn't exist, or updates if it does."""
    # Use select to check for existing lesson
    stmt = select(dbm.Lesson).where(
        dbm.Lesson.group_id == group.id,
        dbm.Lesson.start_time == start_time
    )
    existing_lesson = session.execute(stmt).scalar_one_or_none()

    if existing_lesson:
        logger.info(f"Lesson for group '{group.name}' at {start_time} already exists. Updating data.")
        existing_lesson.subject = subject
        existing_lesson.teacher = teacher
        existing_lesson.classroom = classroom
        existing_lesson.end_time = end_time
        existing_lesson.lesson_type = lesson_type
        session.commit()
        return existing_lesson
    else:
        lesson = dbm.Lesson(subject=subject, teacher=teacher, classroom=classroom, start_time=start_time, end_time=end_time, lesson_type=lesson_type, group=group)
        session.add(lesson)
        try:
            session.commit()
            logger.info(f"Lesson '{subject.name}' added.")
            return lesson
        except IntegrityError as e:
            session.rollback()
            logger.error(f"Unexpected error when adding/updating lesson: {e}")
            return None

def delete_lessons_by_group_and_date_range(session: Session, group: dbm.Group, start_date: Date, end_date: Date) -> None:
    """Deletes lessons for a group within a date range."""
    stmt = select(dbm.Lesson).where(
        dbm.Lesson.group_id == group.id,
        func.date(dbm.Lesson.start_time) >= start_date,
        func.date(dbm.Lesson.start_time) <= end_date
    )
    lessons_to_delete = session.execute(stmt).scalars().all()

    for lesson in lessons_to_delete:
        logger.info(f"Deleting lesson: {lesson}")
        session.delete(lesson)
    try:
        session.commit()
        logger.info(f"Lessons for group '{group.name}' in range '{start_date}' to '{end_date}' deleted.")
    except Exception as e:
        session.rollback()
        logger.error(f"Error while deleting lessons: {e}")

def get_lessons_by_subject(session: Session, subject_name: str):
    """Gets lessons by subject name."""
    stmt = select(dbm.Lesson).join(dbm.Subject).where(dbm.Subject.name == subject_name)
    lessons = session.execute(stmt).scalars().all()
    return lessons

def get_classroom_schedule(session: Session, classroom_name: str, date: Date):
    """Gets classroom schedule for a given date."""
    start_of_day = datetime.datetime.combine(date, datetime.time.min)
    end_of_day = datetime.datetime.combine(date, datetime.time.max)
    stmt = select(dbm.Lesson).join(dbm.Classroom).where(
        dbm.Classroom.name == classroom_name,
        dbm.Lesson.start_time.between(start_of_day, end_of_day)
    )
    lessons = session.execute(stmt).scalars().all()
    return lessons

def get_all_lessons(session: Session):
    """Gets all lessons."""
    stmt = select(dbm.Lesson)
    lessons = session.execute(stmt).scalars().all()
    return lessons

def update_lesson(session: Session, lesson_id: int, data: dict) -> None:
    """Updates a lesson by ID."""
    lesson = session.get(dbm.Lesson, lesson_id)
    if lesson:
        for key, value in data.items():
            setattr(lesson, key, value)
        logger.info(f"Lesson with ID '{lesson_id}' updated.")
        session.commit()
    else:
        logger.warning(f"Lesson with ID '{lesson_id}' not found.")

def delete_lesson(session: Session, lesson_id: int) -> None:
    """Deletes a lesson by ID."""
    lesson = session.get(dbm.Lesson, lesson_id)
    if lesson:
        session.delete(lesson)
        logger.info(f"Lesson with ID '{lesson_id}' deleted.")
        session.commit()
    else:
        logger.warning(f"Lesson with ID '{lesson_id}' not found.")