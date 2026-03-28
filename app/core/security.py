import os
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# BURADAKİ import satırını sildik!
SECRET_KEY = os.getenv("SECRET_KEY") 
if not SECRET_KEY:
    # Docker loglarında görmek için hata mesajı
    raise ValueError("SECRET_KEY not set! Check your .env file.")

ALGORITHM = "HS256"
# Şifreleme konfigürasyonu
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    # 1 saat geçerli
    expire = datetime.utcnow() + timedelta(minutes=60) 
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
