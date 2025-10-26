from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine, select

class User(SQLModel, table=True):
    username: str = Field(default=None, primary_key=True)
    password: str = Field(default=None, index=True)
    disabled: bool = False
    admin: bool = False