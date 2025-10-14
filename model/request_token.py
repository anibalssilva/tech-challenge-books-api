from pydantic import BaseModel

class RequestToken(BaseModel):
    username: str
    password: str