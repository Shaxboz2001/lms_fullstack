from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from .. import models, schemas
from ..dependencies import get_db
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ------------------------------
# Dummy token -> current user
# ------------------------------
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        user_id = int(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token format")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    return user

# ------------------------------
# GET Payments
# ------------------------------
@router.get("/", response_model=List[schemas.PaymentResponse])
def get_payments(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role == models.UserRole.student:
        payments = db.query(models.Payment).filter(
            or_(
                models.Payment.student_id == current_user.id,
                models.Payment.teacher_id == current_user.id
            )
        ).all()
    elif current_user.role == models.UserRole.teacher:
        group_ids = [g.id for g in current_user.groups_as_teacher]
        payments = db.query(models.Payment).filter(
            or_(
                models.Payment.teacher_id == current_user.id,
                models.Payment.group_id.in_(group_ids)
            )
        ).all()
    elif current_user.role in [models.UserRole.manager, models.UserRole.admin]:
        payments = db.query(models.Payment).all()
    else:
        payments = []

    return payments

# ------------------------------
# CREATE Payment
# ------------------------------
@router.post("/", response_model=schemas.PaymentResponse)
def create_payment(
    amount: float = Body(..., gt=0),
    description: Optional[str] = Body(None),
    student_id: Optional[int] = Body(None),
    teacher_id: Optional[int] = Body(None),
    group_id: Optional[int] = Body(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Role-based restrictions
    if current_user.role == models.UserRole.student:
        raise HTTPException(status_code=403, detail="Students cannot create payments")

    if current_user.role == models.UserRole.teacher:
        if teacher_id and teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="Teachers can only add their own salary")
        if group_id:
            group = db.query(models.Group).filter(models.Group.id == group_id).first()
            if not group or current_user not in group.teachers:
                raise HTTPException(status_code=403, detail="You can only add payments for your groups")

    # Create payment
    payment = models.Payment(
        amount=amount,
        description=description,
        student_id=student_id,
        teacher_id=teacher_id,
        group_id=group_id
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment
