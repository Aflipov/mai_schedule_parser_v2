from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_session, dbm
from .. import schemas, auth
from ..scraper import scrape_and_update_all_schedules_async
import httpx
import atexit
import urllib
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/schedule",
    tags=["schedule"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[schemas.Lesson])
async def read_schedules(
    skip: int = Query(0, description="Skip the first N items"),
    limit: int = Query(100, description="Limit the number of items"),
    sort_by: Optional[str] = Query(None, description="Sort by field (e.g., start_time, subject_name)"),
    sort_order: str = Query("asc", description="Sort order (asc or desc)"),
    db: Session = Depends(get_session),
    current_user: schemas.User = Depends(auth.get_current_active_user)
):
    """
    Получает список расписаний, с возможностью сортировки.
    """
    query = db.query(dbm.Lesson)

    # Добавляем сортировку, если указано
    if sort_by:
        if sort_by == "subject_name":
            sort_column = dbm.Lesson.subject.hasattr('name') # Сортировка по имени предмета
        elif hasattr(dbm.Lesson, sort_by):
            sort_column = getattr(dbm.Lesson, sort_by)
        else:
            raise HTTPException(status_code=400, detail="Invalid sort_by parameter")

        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column) # Сортировка по возрастанию

    schedules = query.offset(skip).limit(limit).all()
    return schedules

@router.post("/", response_model=schemas.Lesson, status_code=status.HTTP_201_CREATED)
async def create_schedule(schedule: schemas.LessonCreate, db: Session = Depends(get_session), current_user: schemas.User = Depends(auth.get_current_active_admin_user)):
    """
    Создает новое расписание (только для администраторов).
    """
    # Получаем объекты Subject, Teacher, Classroom, Group по именам
    subject = db.query(dbm.Subject).filter(dbm.Subject.name == schedule.subject_name).first()
    teacher = db.query(dbm.Teacher).filter(dbm.Teacher.name == schedule.teacher_name).first()
    classroom = db.query(dbm.Classroom).filter(dbm.Classroom.name == schedule.classroom_name).first()
    group = db.query(dbm.Group).filter(dbm.Group.name == schedule.group_name).first()

    if not all([subject, teacher, classroom, group]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more related entities not found")

    # Создаем урок
    db_schedule = dbm.Lesson(
        subject=subject,
        teacher=teacher,
        classroom=classroom,
        start_time=schedule.start_time,
        end_time=schedule.end_time,
        lesson_type=schedule.lesson_type,
        group=group
    )
    db.add(db_schedule)
    try:
        db.commit()
        db.refresh(db_schedule)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return db_schedule

@router.put("/{schedule_id}", response_model=schemas.Lesson)
async def update_schedule(schedule_id: int, schedule: schemas.LessonUpdate, db: Session = Depends(get_session), current_user: schemas.User = Depends(auth.get_current_active_admin_user)):
    """
    Обновляет расписание по ID (только для администраторов).
    """
    db_schedule = db.query(dbm.Lesson).filter(dbm.Lesson.id == schedule_id).first()
    if db_schedule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")

    # Обновляем только предоставленные поля
    if schedule.start_time:
        db_schedule.start_time = schedule.start_time
    if schedule.end_time:
        db_schedule.end_time = schedule.end_time
    if schedule.lesson_type:
        db_schedule.lesson_type = schedule.lesson_type

    if schedule.subject_name:
        subject = db.query(dbm.Subject).filter(dbm.Subject.name == schedule.subject_name).first()
        if not subject:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subject not found")
        db_schedule.subject = subject

    if schedule.teacher_name:
        teacher = db.query(dbm.Teacher).filter(dbm.Teacher.name == schedule.teacher_name).first()
        if not teacher:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Teacher not found")
        db_schedule.teacher = teacher

    if schedule.classroom_name:
        classroom = db.query(dbm.Classroom).filter(dbm.Classroom.name == schedule.classroom_name).first()
        if not classroom:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Classroom not found")
        db_schedule.classroom = classroom

    if schedule.group_name:
        group = db.query(dbm.Group).filter(dbm.Group.name == schedule.group_name).first()
        if not group:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Group not found")
        db_schedule.group = group

    try:
        db.commit()
        db.refresh(db_schedule)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return db_schedule

@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(schedule_id: int, db: Session = Depends(get_session), current_user: schemas.User = Depends(auth.get_current_active_admin_user)):
    """
    Удаляет расписание по ID (только для администраторов).
    """
    db_schedule = db.query(dbm.Lesson).filter(dbm.Lesson.id == schedule_id).first()
    if db_schedule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    db.delete(db_schedule)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return None

@router.post("/force_parse", status_code=status.HTTP_200_OK)
async def force_parse(
    background_tasks: BackgroundTasks,
    group_numbers: List[str] = Query(["М8О-102БВ-24"], description="Список номеров групп"),
    week_numbers: List[int] = Query([10], description="Список номеров недель (1-18)"),
    db: Session = Depends(get_session),
    # current_user: schemas.User = Depends(auth.get_current_active_admin_user),
):
    """
    Запускает принудительный парсинг для указанных групп и недель (только для администраторов).
    """

    async def run_scraper(group_numbers: list[str], week_numbers: list[int], db: Session):
        logger.info(f"Запуск скрапера в фоне для групп: {group_numbers}, недели: {week_numbers}")
        async with httpx.AsyncClient(timeout=15.0) as client: # Create httpx Client
            scrape_and_update_all_schedules_async(db, client, group_numbers, week_numbers)  # Pass the client
            client.get(f'https://mai.ru/education/studies/schedule/index.php?group={urllib.parse.quote("М8О-102БВ-24")}&week={10}')

            def close_client() -> None:
                logger.info("Закрываем сессию httpx...")
                client.close()
                logger.info("Сессия httpx закрыта.")

            atexit.register(close_client)
        
        logger.info("Скрапинг завершен.")

    background_tasks.add_task(run_scraper, group_numbers, week_numbers, db)
    return {"message": f"Парсинг расписания для групп {group_numbers}, недели {week_numbers} запущен в фоновом режиме."}