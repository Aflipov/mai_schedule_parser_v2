# Используем базовый образ Python
FROM python:3.12.1-slim-bookworm

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
# COPY req.in .
COPY req.txt .

# Устанавливаем системные зависимости (если они нужны)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir -r req.txt

# Копируем исходный код приложения
COPY . .

# Настраиваем переменные окружения
ENV DATABASE_URL="sqlite:///./schedule.db"
ENV SECRET_KEY="YOUR_SECRET_KEY"
ENV ECHO="True"

# Команда для запуска приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]