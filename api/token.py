from typing import Annotated
from datetime import datetime, timedelta, timezone
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

import config
from model.user import User
from pwdlib import PasswordHash
from sqlmodel import Field, Session, SQLModel, create_engine, select
from pydantic import BaseModel

import jwt
from jwt.exceptions import InvalidTokenError

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

password_hash = PasswordHash.recommended()

hashed_password_mock = "$argon2id$v=19$m=65536,t=3,p=4$U85GDgxTz7823LaZXeZo0g$9czdIvFdVpev2lOGzXgdXT9JL15xAgB2wntOE7Pe/SE"

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

@app.post("/users/register")
async def register_user(user: User, session: SessionDep):

    if session.get(User, user.username):
        return {"error": "Usuário já está cadastrado"}

    user.password = password_hash.hash(user.password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"message": "Usuário criado com sucesso"}

class Token(BaseModel):
    access_token: str
    token_type: str

@app.post("/token")
async def login_for_access_token(
    user_request: User, session: SessionDep
) -> Token:
    print(user_request)
    user = authenticate_user(user_request, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt

def get_password_hash(password):
    return password_hash.hash(password)

def authenticate_user(user: User, session: SessionDep):
    user_db = session.get(User, user.username)
    if not user_db:
        return False
    if not verify_password(user.password, user_db.password):
        return False
    return user

def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()