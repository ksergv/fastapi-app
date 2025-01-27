# backend/models.py
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    category = Column(String, index=True)
    content = Column(String)
    image = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, default=1)  # Значение по умолчанию
    owner = relationship("User")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")  # Связь с комментариями

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)  # Текст комментария
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    post = relationship("Post", back_populates="comments")  # Связь с постом
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="comments")  # Связь с пользователем

# Добавляем отношение комментариев к пользователю и посту
User.comments = relationship("Comment", back_populates="owner", cascade="all, delete-orphan")

