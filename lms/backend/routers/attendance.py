from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from .. import models, schemas
from ..dependencies import get_db, get_current_user

router = APIRouter(
    prefix="/attendance",
    tags=["Attendance"]
)

# ------------------------------
# POST: Yo‘qlama qo‘shish
# ------------------------------
@router.post("/", response_model=List[schemas.AttendanceResponse])
def create_attendance(
    group_id: int = Body(...),
    records: List[schemas.AttendanceCreate] = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Faqat o‘qituvchi va admin/manager qo‘shishi mumkin
    if current_user.role not in [models.UserRole.teacher, models.UserRole.admin, models.UserRole.manager]:
        raise HTTPException(status_code=403, detail="Not allowed to create attendance")

    # Guruhni tekshirish
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Agar o‘qituvchi bo‘lsa, faqat o‘z guruhiga ruxsat
    if current_user.role == models.UserRole.teacher and current_user not in group.teachers:
        raise HTTPException(status_code=403, detail="You can only add attendance for your groups")

    attendance_list = []
    for record in records:
        student = db.query(models.User).filter(models.User.id == record.student_id).first()
        if not student:
            continue

        attendance_entry = models.Attendance(
            student_id=record.student_id,
            teacher_id=current_user.id,
            group_id=group_id,
            date=datetime.utcnow(),
            status="present" if record.is_present else "absent"
        )
        db.add(attendance_entry)
        attendance_list.append(attendance_entry)

    db.commit()

    # Refresh va response tayyorlash
    for att in attendance_list:
        db.refresh(att)

    return attendance_list


# ------------------------------
# GET: Guruh bo‘yicha yo‘qlamalar
# ------------------------------
@router.get("/{group_id}", response_model=List[schemas.AttendanceResponse])
def get_group_attendance(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # O‘qituvchi faqat o‘z guruhini ko‘ra oladi
    if current_user.role == models.UserRole.teacher and current_user not in group.teachers:
        raise HTTPException(status_code=403, detail="Not allowed to view this group's attendance")

    attendance_records = db.query(models.Attendance).filter(models.Attendance.group_id == group_id).all()
    return attendance_records

@router.get("/", response_model=List[schemas.AttendanceResponse])
def get_group_attendance(
    group_id: int = Query(..., description="Group ID"),
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # O‘qituvchi faqat o‘z guruhini ko‘ra oladi
    if current_user.role == models.UserRole.teacher and current_user not in group.teachers:
        raise HTTPException(status_code=403, detail="Not allowed to view this group's attendance")

    query = db.query(models.Attendance).filter(models.Attendance.group_id == group_id)

    # Agar date_from va date_to berilgan bo‘lsa
    if date_from:
        query = query.filter(models.Attendance.date >= date_from)
    if date_to:
        query = query.filter(models.Attendance.date <= date_to)

    attendance_records = query.order_by(models.Attendance.date.desc()).all()
    return attendance_records
