from sqlalchemy import Column, Integer, String, Enum, Float, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
import enum

# ==============================
# User roles
# ==============================
class UserRole(str, enum.Enum):
    admin = "admin"
    teacher = "teacher"
    manager = "manager"
    student = "student"

# ==============================
# Student status
# ==============================
class StudentStatus(str, enum.Enum):
    interested = "interested"
    studying = "studying"
    left = "left"
    graduated = "graduated"

# ==============================
# User model
# ==============================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=True)
    password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.student)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    age = Column(Integer, nullable=True)

    # Student-specific
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    subject = Column(String, nullable=True)
    fee = Column(Float, nullable=True)
    status = Column(Enum(StudentStatus), default=StudentStatus.interested)

    # Relationships
    payments_as_student = relationship("Payment", foreign_keys="Payment.student_id", back_populates="student")
    payments_as_teacher = relationship("Payment", foreign_keys="Payment.teacher_id", back_populates="teacher")
    groups_as_teacher = relationship("Group", secondary="group_teachers", back_populates="teachers")
    groups_as_student = relationship("Group", secondary="group_students", back_populates="students")
    attendances_as_student = relationship("Attendance", foreign_keys="Attendance.student_id", back_populates="student")
    attendances_as_teacher = relationship("Attendance", foreign_keys="Attendance.teacher_id", back_populates="teacher")

# ==============================
# Many-to-Many relationships
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

    students = relationship("User", secondary=group_students, back_populates="groups_as_student")
    teachers = relationship("User", secondary=group_teachers, back_populates="groups_as_teacher")
    payments = relationship("Payment", back_populates="group")
    attendances = relationship("Attendance", back_populates="group")

# ==============================
# Payment model
# ==============================
class Payment(Base):
    __tablename__ = "payment"

    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    teacher_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    month = Column(String(7), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("User", foreign_keys=[student_id], back_populates="payments_as_student")
    teacher = relationship("User", foreign_keys=[teacher_id], back_populates="payments_as_teacher")
    group = relationship("Group", back_populates="payments")

# ==============================
# Attendance model
# ==============================
class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="present")  # present / absent / late

    student = relationship("User", foreign_keys=[student_id], back_populates="attendances_as_student")
    teacher = relationship("User", foreign_keys=[teacher_id], back_populates="attendances_as_teacher")
    group = relationship("Group", back_populates="attendances")
