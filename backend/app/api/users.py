from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import select
from ..database import get_session, dbm
from .. import schemas, auth
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
import logging
from contextlib import contextmanager
from sqlalchemy import create_engine

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = "sqlite:///./schedule.db"  # Example SQLite database URL
ECHO = False

engine = create_engine(DATABASE_URL, echo=ECHO)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_db() -> None:
    """Creates the database and tables."""
    dbm.Base.metadata.create_all(bind=engine)
    logger.info("Database created successfully.")

create_db()

@contextmanager
def get_session():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Error during db operation {e}")
        raise
    finally:
        db.close()

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_session)):
    """
    Создает нового пользователя (только для администраторов).
    """
    hashed_password = auth.get_password_hash(user.password)
    db_user = dbm.User(username=user.username, email=user.email, hashed_password=hashed_password, is_active=True, is_admin=False) # по умолчанию обычный пользователь
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return db_user

@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(auth.get_current_active_user)):
    """
    Получает информацию о текущем аутентифицированном пользователе.
    """
    return current_user

@router.get("/{user_id}", response_model=schemas.User)
async def read_user(user_id: int, db: Session = Depends(get_session), current_user: schemas.User = Depends(auth.get_current_active_admin_user)):
    """
    Получает пользователя по ID (только для администраторов).
    """
    stmt = select(dbm.User).where(dbm.User.id == user_id)
    with get_session() as db:
        db_user = db.execute(stmt).scalar_one_or_none()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)):
    """
    Получает JWT токен для аутентификации.
    """
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

async def authenticate_user(username: str, password: str, db: Session = Depends(get_session)):
    """
    Проверяет имя пользователя и пароль в базе данных.
    """
    stmt = select(dbm.User).where(dbm.User.username == username)
    with get_session() as db:
        user = db.execute(stmt).scalar_one_or_none()

        if not user:
            logger.warning(f"User not found: {username}")
            return None
        if not auth.verify_password(password, user.hashed_password):
            logger.warning(f"Password verification failed for user: {username}")
            return None
        return user