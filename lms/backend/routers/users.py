from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..dependencies import get_db
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ------------------------------
# Dummy function: token -> current user
# ------------------------------
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        user_id = int(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token format")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    return user

# ------------------------------
# GET all users
# ------------------------------
@router.get("/", response_model=List[schemas.UserResponse])
def get_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Admin va manager barcha userlarni ko‘ra oladi
    if current_user.role in [models.UserRole.admin, models.UserRole.manager]:
        users = db.query(models.User).all()
    else:
        # Teacher va student faqat o‘zini ko‘rishi mumkin
        users = [current_user]
    return users

# ------------------------------
# Create new user
# ------------------------------
@router.post("/", response_model=schemas.UserResponse)
def create_user(
    username: str = Body(...),
    password: str = Body(...),
    role: schemas.RoleEnum = Body(schemas.RoleEnum.student),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Faqat admin yoki manager user qo‘sha oladi
    if current_user.role not in [models.UserRole.admin, models.UserRole.manager]:
        raise HTTPException(status_code=403, detail="Not allowed to create users")

    # Username unique tekshiruv
    existing_user = db.query(models.User).filter(models.User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = models.User(
        username=username,
        password=password,  # Note: real loyihada hash qilinishi kerak!
        role=models.UserRole(role)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
