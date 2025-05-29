from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<User(username='{self.username}')>"

class Subject(Base):
    __tablename__ = 'subjects'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    lessons = relationship("Lesson", back_populates="subject") # Связь с уроками

    def __repr__(self):
        return f"<Subject(name='{self.name}')>"


class Teacher(Base):
    __tablename__ = 'teachers'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    # department = Column(String, nullable=True)
    lessons = relationship("Lesson", back_populates="teacher") # Связь с уроками

    def __repr__(self):
        return f"<Teacher(name='{self.name}')>"

class Classroom(Base):
    __tablename__ = 'classrooms'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    # capacity = Column(Integer, nullable=True)
    # location = Column(String, nullable=True)
    lessons = relationship("Lesson", back_populates="classroom") # Связь с уроками

    def __repr__(self):
        return f"<Classroom(name='{self.name}')>"


class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    lessons = relationship("Lesson", back_populates="group") # Связь с уроками (одна группа для одного урока)

    def __repr__(self):
        return f"<Group(name='{self.name}')>"


class Lesson(Base):
    __tablename__ = 'lessons'
    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey('subjects.id'), nullable=False)
    teacher_id = Column(Integer, ForeignKey('teachers.id'), nullable=False)
    classroom_id = Column(Integer, ForeignKey('classrooms.id'), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    lesson_type = Column(String, nullable=True)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=True)  # Урок только для одной группы
    # description = Column(String, nullable=True)

    subject = relationship("Subject", back_populates="lessons") # Связь с предметом
    teacher = relationship("Teacher", back_populates="lessons") # Связь с преподавателем
    classroom = relationship("Classroom", back_populates="lessons") # Связь с кабинетом
    group = relationship("Group", back_populates="lessons") # Связь с группой (одна группа для одного урока)

    __table_args__ = (
        UniqueConstraint('group_id', 'start_time', name='unique_lesson'),
    )

    def __repr__(self):
        return f"<Lesson(subject='{self.subject.name}', start_time='{self.start_time}')>"