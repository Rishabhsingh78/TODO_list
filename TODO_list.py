from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi_users import FastAPIUsers, models
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from pydantic import BaseModel
from typing import Optional, List
from passlib.context import CryptContext
from datetime import datetime

# Define database settings
DATABASE_URL = "mysql+pymysql://<username>:<password>@<hostname>:<port>/<database_name>"
engine = create_engine(DATABASE_URL)

# Define SQLAlchemy database session
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# Define password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Define OAuth2
SECRET_KEY = "<your_secret_key>"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Define ToDo item model
class ToDoItem(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    completed: bool = False
    user_id: int

# Define ToDo item database model
class ToDo(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(50), index=True)
    description = Column(String(255))
    completed = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"))

# Define User database model
class User(Base, models.BaseUser):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    created_at = Column(DateTime, default=datetime.utcnow())
    updated_at = Column(DateTime, default=datetime.utcnow())

# Define User Create/Update schema
class UserCreate(models.BaseUserCreate):
    email: str
    password: str

class UserUpdate(models.BaseUserUpdate):
    password: Optional[str] = None

class UserDB(User, models.BaseUserDB):
    pass

# Initialize FastAPI app
app = FastAPI()

# Initialize User database
user_db = SQLAlchemyUserDatabase(UserDB, SessionLocal())

# Initialize FastAPI Users
fastapi_users = FastAPIUsers(
    user_db,
    [models.UIDBUserCreate, UserCreate],
    [models.UIDBUserUpdate, UserUpdate],
    UserDB,
)

# Define OAuth2 password bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Define helper function to verify password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Define helper function to hash password
def get_password_hash(password):
    return pwd_context.hash(password)

# Define helper function to get database session
def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

# Define endpoint for creating new user
@app.post("/users", response_model=UserDB)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(db_user)
    db.commit()
   
