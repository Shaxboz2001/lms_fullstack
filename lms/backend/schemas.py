from pydantic import BaseModel
from enum import Enum
from typing import List, Optional
from datetime import datetime

# ==============================
# Roles and Student status
# ==============================
class RoleEnum(str, Enum):
    admin = "admin"
    teacher = "teacher"
    manager = "manager"
    student = "student"

class StudentStatus(str, Enum):
    interested = "interested"
    studying = "studying"
    left = "left"
    graduated = "graduated"

# ==============================
# User schemas
# ==============================
class UserBase(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    subject: Optional[str] = None
    fee: Optional[float] = None
    status: Optional[StudentStatus] = None
    group_id: Optional[int] = None
    teacher_id: Optional[int] = None
    role: Optional[RoleEnum] = None
    age: Optional[int] = None

    class Config:
        from_attributes = True  # V2 uchun

class UserCreate(UserBase):
    username: str
    password: str
    role: RoleEnum = RoleEnum.student

class UserResponse(UserBase):
    id: int

# ==============================
# Group schemas
# ==============================
class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    student_ids: Optional[List[int]] = []
    teacher_ids: Optional[List[int]] = []

class GroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    student_ids: List[int] = []
    teacher_ids: List[int] = []

    class Config:
        from_attributes = True

# ==============================
# Payment schemas
# ==============================
class PaymentBase(BaseModel):
    amount: float
    description: Optional[str] = None
    student_id: Optional[int] = None
    teacher_id: Optional[int] = None
    group_id: Optional[int] = None

class PaymentCreate(PaymentBase):
    month: Optional[str] = None

class PaymentResponse(PaymentBase):
    id: int
    created_at: datetime
    month: Optional[str] = None
    student: Optional[UserResponse] = None
    teacher: Optional[UserResponse] = None
    group: Optional[GroupResponse] = None

    class Config:
        from_attributes = True

# ==============================
# Attendance schemas
# ==============================
class AttendanceCreate(BaseModel):
    student_id: int
    is_present: bool

class AttendanceResponse(BaseModel):
    id: int
    student_id: int
    teacher_id: int
    group_id: int
    date: datetime
    status: str

    class Config:
        from_attributes = True
