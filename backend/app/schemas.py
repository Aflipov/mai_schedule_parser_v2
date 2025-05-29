from pydantic import BaseModel, Field
from datetime import datetime

class SubjectBase(BaseModel):
    name: str

class SubjectCreate(SubjectBase):
    pass

class Subject(SubjectBase):
    id: int

    class Config:
        from_attributes = True

class TeacherBase(BaseModel):
    name: str

class TeacherCreate(TeacherBase):
    pass

class Teacher(TeacherBase):
    id: int

    class Config:
        from_attributes = True

class ClassroomBase(BaseModel):
    name: str

class ClassroomCreate(ClassroomBase):
    pass

class Classroom(ClassroomBase):
    id: int

    class Config:
        from_attributes = True

class GroupBase(BaseModel):
    name: str

class GroupCreate(GroupBase):
    pass

class Group(GroupBase):
    id: int

    class Config:
        from_attributes = True

class LessonBase(BaseModel):
    start_time: datetime
    end_time: datetime | None = None  # Может быть пустым
    lesson_type: str | None = None

class LessonCreate(LessonBase):
    subject_name: str
    teacher_name: str
    classroom_name: str
    group_name: str

class LessonUpdate(LessonBase):
    subject_name: str | None = None
    teacher_name: str | None = None
    classroom_name: str | None = None
    group_name: str | None = None

class Lesson(LessonBase):
    id: int
    subject: Subject
    teacher: Teacher
    classroom: Classroom
    group: Group

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_admin: bool

    class Config:
        from_attributes = True



class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"  # Значение по умолчанию "bearer"
    expires_in: int | None = None # Добавлено поле времени жизни токена