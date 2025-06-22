from pydantic import BaseModel, Field
from typing import Optional

class AuthUserSchema(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str

    class Config:
        orm_mode = True


class LoginRequest(BaseModel):
    email: str
    password: str


class AdminCreateUser(BaseModel):
    email: str
    password: str
    role: str
    kitchen_id: Optional[str] = None


class AuthUserData(BaseModel):
    email: str
    role: str