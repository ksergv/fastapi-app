# backend/crud.py
from sqlalchemy.orm import Session
from models import User, Post
from schemas import UserCreate, PostCreate
import models, schemas
from security import hash_password

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: UserCreate):
    hashed_password = hash_password(user.password)
    db_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_post(db: Session, post_id: int):
    return db.query(Post).filter(Post.id == post_id).first()

def get_posts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Post).offset(skip).limit(limit).all()

def create_post(db: Session, post: PostCreate, user_id: int):
    db_post = Post(**post.dict(), owner_id=user_id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

def update_post(db: Session, post_id: int, post: PostCreate):
    db_post = get_post(db, post_id)
    if db_post:
        db_post.title = post.title
        db_post.category = post.category
        db_post.content = post.content
        db_post.image = post.image
        db.commit()
        db.refresh(db_post)
    return db_post

def delete_post(db: Session, post_id: int):
    db_post = get_post(db, post_id)
    if db_post:
        db.delete(db_post)
        db.commit()
    return db_post


def create_comment(db: Session, comment: schemas.CommentCreate, user_id: int, post_id: int):
    db_comment = models.Comment(**comment.dict(), owner_id=user_id, post_id=post_id)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)

    # Возвращаем комментарий с именем пользователя
    owner_username = db.query(models.User.username).filter(models.User.id == user_id).first()
    return {
        "id": db_comment.id,
        "owner_id": db_comment.owner_id,
        "post_id": db_comment.post_id,
        "content": db_comment.content,
        "owner_username": owner_username[0],
    }

def get_comments_by_post(db: Session, post_id: int):
    return db.query(
        models.Comment.id,
        models.Comment.owner_id,
        models.Comment.post_id,
        models.Comment.content,
        models.User.username.label('owner_username'),  # Получаем имя пользователя
    ).join(models.User, models.User.id == models.Comment.owner_id)\
     .filter(models.Comment.post_id == post_id)\
     .all()

def get_comment(db: Session, comment_id: int):
    return db.query(models.Comment).filter(models.Comment.id == comment_id).first()


def delete_comment(db: Session, comment_id: int):
    db_comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    db.delete(db_comment)
    db.commit()

def update_comment(db: Session, comment_id: int, comment_data: schemas.CommentCreate):
    db_comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not db_comment:
        return None

    # Обновляем поля комментария
    db_comment.content = comment_data.content

    db.commit()
    db.refresh(db_comment)

    # Добавляем owner_username
    owner_username = db.query(models.User.username).filter(models.User.id == db_comment.owner_id).scalar()

    # Возвращаем объект с полем owner_username
    return {
        "id": db_comment.id,
        "content": db_comment.content,
        "owner_id": db_comment.owner_id,
        "owner_username": owner_username,
        "post_id": db_comment.post_id
    }
