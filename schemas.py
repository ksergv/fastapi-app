# backend/schemas.py
from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class UserOut(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True  # Новый параметр вместо orm_mode

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int  # Ensure this is included

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None  # Add user_id to the class


class PostCreate(BaseModel):
    title: str
    category: str
    content: str
    image: Optional[str] = None

class PostOut(BaseModel):
    id: int
    title: str
    category: str
    content: str
    image: Optional[str] = None



class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    pass

class CommentOut(CommentBase):
    id: int
    owner_id: int
    post_id: int
    content: str
    owner_username: str  # Добавляем имя пользователя


    class Config:
        from_attributes = True  # Новый параметр вместо orm_mode