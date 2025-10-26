from pydantic import BaseModel

class RefreshToken(BaseModel):
    access_token: str