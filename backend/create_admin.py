import os
from sqlalchemy.orm import sessionmaker
from app.database import engine, dbm  # Импортируем engine и модели базы данных
from app.auth import get_password_hash  # Импортируем функцию для хэширования пароля

# Создаем сессию
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def create_admin():
    # Получаем данные администратора из переменных окружения
    username = os.getenv('ADMIN_USERNAME')
    email = os.getenv('ADMIN_EMAIL')
    password = os.getenv('ADMIN_PASSWORD')

    if not username or not email or not password:
        print("Admin credentials not provided. Skipping admin creation.")
        return

    # Проверяем, существует ли пользователь с таким email
    existing_user = db.query(dbm.User).filter(dbm.User.email == email).first()

    if existing_user:
        print(f"User with email {email} already exists. Skipping admin creation.")
        return

    # Хэшируем пароль
    hashed_password = get_password_hash(password)

    # Создаем объект пользователя
    admin_user = dbm.User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=True  # Устанавливаем флаг администратора
    )

    # Добавляем пользователя в базу данных
    db.add(admin_user)
    try:
        db.commit()
        db.refresh(admin_user)
        print(f"Admin user {username} created successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error creating admin user: {e}")


if __name__ == "__main__":
    create_admin()