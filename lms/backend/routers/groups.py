from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .dependencies import get_db, get_current_user
from .schemas import GroupCreate, GroupResponse, UserResponse
from .models import Group, User, Course, UserRole

groups_router = APIRouter(prefix="/groups", tags=["Groups"])

# ------------------------------
# CREATE Group
# ------------------------------
@groups_router.post("/", response_model=GroupResponse)
def create_group(
    group: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in [UserRole.admin, UserRole.manager]:
        raise HTTPException(status_code=403, detail="Guruh yaratish uchun ruxsat yo‘q")

    course = db.query(Course).filter(Course.id == group.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Kurs topilmadi")

    new_group = Group(name=group.name, description=group.description, course_id=group.course_id)

    # O‘quvchilar
    students = db.query(User).filter(User.id.in_(group.student_ids), User.role == UserRole.student).all()
    teachers = db.query(User).filter(User.id.in_(group.teacher_ids), User.role == UserRole.teacher).all()

    new_group.students = students
    new_group.teachers = teachers

    db.add(new_group)
    db.commit()
    db.refresh(new_group)

    return GroupResponse.from_orm(new_group)


# ------------------------------
# GET All Groups
# ------------------------------
@groups_router.get("/", response_model=List[GroupResponse])
def get_groups(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role in [UserRole.admin, UserRole.manager]:
        groups = db.query(Group).all()
    elif current_user.role == UserRole.teacher:
        groups = current_user.groups_as_teacher
    else:
        groups = current_user.groups_as_student
    return groups


# ------------------------------
# GET Students in Group
# ------------------------------
@groups_router.get("/{group_id}/students", response_model=List[UserResponse])
def get_group_students(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Guruh topilmadi")

    if current_user.role == UserRole.teacher and current_user not in group.teachers:
        raise HTTPException(status_code=403, detail="Bu guruhga kirish mumkin emas")

    return group.students


# ------------------------------
# DELETE Group
# ------------------------------
@groups_router.delete("/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role not in [UserRole.admin, UserRole.manager]:
        raise HTTPException(status_code=403, detail="O‘chirishga ruxsat yo‘q")

    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Guruh topilmadi")

    db.delete(group)
    db.commit()
    return {"message": f"Guruh '{group.name}' muvaffaqiyatli o‘chirildi"}
