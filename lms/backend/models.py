from sqlalchemy import Column, Integer, String, Enum, Float, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
import enum

# ==============================
# User roles
# ==============================
class UserRole(enum.Enum):
    admin = "admin"
    teacher = "teacher"
    manager = "manager"
    student = "student"

# ==============================
# User model
# ==============================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.student)

# ==============================
# Many-to-Many relationships for Group
# ==============================
group_students = Table(
    "group_students",
    Base.metadata,
    Column("group_id", Integer, ForeignKey("groups.id")),
    Column("student_id", Integer, ForeignKey("users.id"))
)

group_teachers = Table(
    "group_teachers",
    Base.metadata,
    Column("group_id", Integer, ForeignKey("groups.id")),
    Column("teacher_id", Integer, ForeignKey("users.id"))
)

# ==============================
# Group model
# ==============================
class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    students = relationship("User", secondary=group_students, backref="groups_as_student")
    teachers = relationship("User", secondary=group_teachers, backref="groups_as_teacher")

# ==============================
# Payment model
# ==============================
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)

    # Foreign keys explicitly defined to avoid mapper errors
    student = relationship("User", foreign_keys=[student_id], backref="payments_as_student")
    teacher = relationship("User", foreign_keys=[teacher_id], backref="payments_as_teacher")
    group = relationship("Group", foreign_keys=[group_id], backref="payments")

