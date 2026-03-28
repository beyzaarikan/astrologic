from fastapi import FastAPI
from app.api.endpoints import auth, profiles ,chat # Router'larımızı import ediyoruz
from app.db.database import engine, Base, get_db
from app.models import models

# this line will create the tables in the database based on our SQLAlchemy models (User, Profile, Analysis)
models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="AstroLogic API")

app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(chat.router)

@app.get("/")
async def root():
    return {"message": "AstroLogic Modüler API is working!"}

