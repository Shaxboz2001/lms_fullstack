from pydantic import BaseModel
from enum import Enum
from typing import List, Optional
from datetime import datetime

# ==============================
# Roles
# ==============================
class RoleEnum(str, Enum):
    admin = "admin"
    teacher = "teacher"
    manager = "manager"
    student = "student"

# ==============================
# User schemas
# ==============================
class UserCreate(BaseModel):
    username: str
    password: str
    role: RoleEnum = RoleEnum.student

class UserResponse(BaseModel):
    id: int
    username: str
    role: RoleEnum

    class Config:
        orm_mode = True

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
        orm_mode = True

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
    pass

class PaymentResponse(PaymentBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
