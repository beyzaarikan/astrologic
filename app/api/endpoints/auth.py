from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated # Modern tip belirleme
from app.db.database import get_db
from app.models import models
from app.schemas.user import UserCreate, UserResponse # Şemalarımızı ayırdık
from app.core.security import create_access_token, get_password_hash, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])

# db: Session = Depends(get_db) yerine Annotated kullanımı:
db_dependency = Annotated[Session, Depends(get_db)]

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: db_dependency):
    db_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="this email is already registered")
    
    hashed_pwd = get_password_hash(user_data.password)
    new_user = models.User(email=user_data.email, hashed_password=hashed_pwd)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login")
def login(user_data: UserCreate, db: db_dependency):
    user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="wrong email or password")
    
    token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

