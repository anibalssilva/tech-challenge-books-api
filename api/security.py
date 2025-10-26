from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine, select

from model.create_user import CreateUser
from model.token import Token
from model.refresh_token import RefreshToken
from model.request_token import RequestToken

import config
from db.user import User

# Não criar app aqui, usar o app do main.py
# app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

password_hash = PasswordHash.recommended()


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def register_user(user: CreateUser, session: SessionDep):

    if get_user(user.username, session):
        return {'error': 'Usuário já está cadastrado'}

    create_user = User(username=user.username, password=user.password)

    create_user.password = password_hash.hash(user.password)
    session.add(create_user)
    session.commit()
    session.refresh(create_user)
    return {'message': 'Usuário criado com sucesso'}

def update_admin(user: User, session: SessionDep):
    user_db = get_user(user.username, session)
    if not user_db:
        return {'error': 'Usuário não encontrado'}

    user_db.admin = True
    session.add(user_db)
    session.commit()
    session.refresh(user_db)
    return {'message': 'Usuário alterado com sucesso'}

def update_disable(user: User, session: SessionDep):
    user_db = get_user(user.username, session)
    if not user_db:
        return {'error': 'Usuário não encontrado'}

    user_db.disabled = True
    session.add(user_db)
    session.commit()
    session.refresh(user_db)
    return {'message': 'Usuário desabilitado com sucesso'}

def login_for_access_token(
    user_request: RequestToken, session: SessionDep
):
    user = authenticate_user(user_request, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Usuário ou senha inválida',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    access_token_expires = timedelta(
        minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token = create_access_token(
        data={'sub': user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type='bearer')


def refresh_access_token(token: RefreshToken, session: SessionDep) -> Token:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Invalid refresh token',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    try:
        decoded_payload = jwt.decode(
            token.access_token, config.SECRET_KEY, algorithms=[config.ALGORITHM]
        )
        username: str = decoded_payload.get('sub')

        if username is None:
            raise credentials_exception

        user = get_user(username, session)

        if not user:
            raise credentials_exception

        access_token_expires = timedelta(
            minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        access_token = create_access_token(
            data={'sub': user.username}, expires_delta=access_token_expires
        )
        return Token(access_token=access_token, token_type='bearer')
    except jwt.exceptions.ExpiredSignatureError:
        raise HTTPException(
        status_code=status.HTTP_406_NOT_ACCEPTABLE,
        detail='Assinatura expirada',
        headers={'WWW-Authenticate': 'Bearer'},
    )

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(
        to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM
    )
    return encoded_jwt


def get_password_hash(password):
    return password_hash.hash(password)


def authenticate_user(user: User, session: SessionDep):
    user_db = get_user(user.username, session)
    if not user_db:
        return False
    if not verify_password(user.password, user_db.password):
        return False
    return user


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Credencial não é válida',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = jwt.decode(
            token, config.SECRET_KEY, algorithms=[config.ALGORITHM]
        )
        username = payload.get('sub')
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(username, session)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail='Usuário inativo')
    return current_user


async def get_current_active_user_admin(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    if not current_user.admin:
        raise HTTPException(status_code=400, detail='Usuário logado não tem permissão de administrador')
    return current_user


def get_user(username: str, session: SessionDep):
    return session.get(User, username)


sqlite_file_name = 'database.db'
sqlite_url = f'sqlite:///{sqlite_file_name}'

connect_args = {'check_same_thread': False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Não usar evento startup aqui, será chamado do main.py
# @app.on_event('startup')
# def on_startup():
#     create_db_and_tables()
