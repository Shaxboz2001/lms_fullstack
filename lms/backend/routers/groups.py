from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .dependencies import get_db
from .models import Group, Course, User, UserRole
from .schemas import GroupCreate, GroupUpdate, GroupResponse

groups_router = APIRouter(prefix="/groups", tags=["Groups"])

# ------------------------------
# CREATE group
# ------------------------------
@groups_router.post("/", response_model=GroupResponse)
def create_group(group: GroupCreate, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == group.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    new_group = Group(
        name=group.name,
        course_id=group.course_id,
        teacher_id=group.teacher_id,
        student_id=group.student_id
    )
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    return new_group


# ------------------------------
# GET all groups
# ------------------------------
@groups_router.get("/", response_model=list[GroupResponse])
def get_groups(db: Session = Depends(get_db)):
    groups = db.query(Group).all()
    return [
        GroupResponse(
            id=g.id,
            name=g.name,
            course_id=g.course_id,
            course_name=g.course.title if g.course else None,
            teacher_id=g.teacher_id,
            teacher_name=g.teacher.full_name if g.teacher else None,
            student_id=g.student_id,
            student_name=g.student.full_name if g.student else None,
        )
        for g in groups
    ]


# ------------------------------
# UPDATE group
# ------------------------------
@groups_router.put("/{group_id}", response_model=GroupResponse)
def update_group(group_id: int, updated: GroupUpdate, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    group.name = updated.name or group.name
    group.course_id = updated.course_id or group.course_id
    group.teacher_id = updated.teacher_id or group.teacher_id
    group.student_id = updated.student_id or group.student_id

    db.commit()
    db.refresh(group)
    return group


# ------------------------------
# DELETE group
# ------------------------------
@groups_router.delete("/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    db.delete(group)
    db.commit()
    return {"message": "Group deleted successfully"}


# ------------------------------
# GET courses, teachers, students
# ------------------------------
@groups_router.get("/courses")
def get_courses(db: Session = Depends(get_db)):
    return db.query(Course).all()


@groups_router.get("/teachers/{course_id}")
def get_teachers_for_course(course_id: int, db: Session = Depends(get_db)):
    return db.query(User).filter(User.role == UserRole.teacher, User.course_id == course_id).all()


@groups_router.get("/students/{course_id}")
def get_students_for_course(course_id: int, db: Session = Depends(get_db)):
    return db.query(User).filter(User.role == UserRole.student, User.course_id == course_id).all()
