from fastapi import FastAPI
from .database import engine
from .db_models import Base
from .api import schedule, users  # Импортируем роутеры

Base.metadata.create_all(bind=engine)  # Создаем таблицы в БД, если их нет

app = FastAPI(
    title="Schedule Parser API",
    description="API for managing and retrieving schedule data.",
    version="0.1.0",
)

app.include_router(schedule.router)  # Подключаем роутер расписания
app.include_router(users.router)  # Подключаем роутер пользователей

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Schedule Parser API"}
