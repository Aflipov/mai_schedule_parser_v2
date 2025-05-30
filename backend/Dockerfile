FROM python:3.12.1-slim-bookworm

WORKDIR /app

COPY req.txt .

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r req.txt

COPY . .

ENV DATABASE_URL="sqlite:///./schedule.db"
ENV SECRET_KEY="YOUR_SECRET_KEY"
ENV ECHO="True"

# Копируем скрипт создания администратора
# COPY create_admin.py /app/app/create_admin.py

# Передаем данные администратора через переменные окружения
ENV ADMIN_USERNAME="admin"
ENV ADMIN_EMAIL="admin@example.com"
ENV ADMIN_PASSWORD="admin"

# Запускаем скрипт создания администратора
# RUN python ./app/create_admin.py

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]