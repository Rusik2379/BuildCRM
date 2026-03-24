from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    role: UserRole


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int

    model_config = {"from_attributes": True}
