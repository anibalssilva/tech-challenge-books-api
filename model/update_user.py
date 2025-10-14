from pydantic import BaseModel

class UpdateUser(BaseModel):
    username: str