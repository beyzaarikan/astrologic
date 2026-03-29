from fastapi import Depends, HTTPException, status # FastAPI'den almalısın
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from typing import Annotated
from app.core.security import ALGORITHM, SECRET_KEY
from app.db.database import get_db # Veritabanı bağlantısı için şart
from fastapi.security import OAuth2PasswordBearer
from app.models import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
db_dependency = Annotated[Session, Depends(get_db)]

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: db_dependency
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:  # specific — only catches token errors, not DB errors
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user