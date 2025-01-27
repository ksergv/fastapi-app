# backend/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import timedelta, datetime
from jose import JWTError, jwt
from typing import List
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import models, schemas, crud
from database import SessionLocal, engine, Base
from auth import authenticate_user, create_access_token, oauth2_scheme, verify_token, Token, create_refresh_token

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Разрешенные источники
origins = [
    "http://localhost",  
    "https://fastapi-app-b47b.onrender.com"
]

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Разрешенные источники
    allow_credentials=True,  # Если используешь cookies или авторизацию
    allow_methods=["*"],  # Разрешаем все методы (GET, POST, PUT, DELETE и т.д.)
    allow_headers=["*"],  # Разрешаем все заголовки
)


SECRET_KEY = "my_fast_API_Blog"  # Замените на более безопасный ключ в продакшене
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # время действия access_token
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # время действия refresh_token, например, 1 неделя


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class TokenRefreshRequest(BaseModel):
    refresh_token: str


# Dependency для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},  # Ensure user_id is included in the token
        expires_delta=access_token_expires
    )
    print("User ID:", user.id)  # Debugging line
    refresh_token = create_refresh_token(
        data={"sub": user.username}, expires_delta=refresh_token_expires
    )
    # Make sure to return user_id here
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user.id  # Ensure user_id is included in the response
    }

# Эндпоинт для обновления access_token через refresh_token
@app.post("/refresh")
def refresh_access_token(token_request: TokenRefreshRequest):
    try:
        payload = jwt.decode(token_request.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    # Создаём новый access_token
    new_access_token = create_access_token(data={"sub": username})

    return {"access_token": new_access_token}

    return {"access_token": new_access_token}

# Функция для получения текущего пользователя
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = verify_token(token, credentials_exception)
    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

@app.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = crud.get_user_by_username(db, username=user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    created_user = crud.create_user(db=db, user=user)
    return created_user



@app.get("/users/me", response_model=schemas.UserOut)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

# CRUD для постов

@app.get("/posts/", response_model=List[schemas.PostOut])
def read_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    posts = crud.get_posts(db, skip=skip, limit=limit)
    return posts

@app.post("/posts/", response_model=schemas.PostOut)
def create_post(post: schemas.PostCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.create_post(db=db, post=post, user_id=current_user.id)

@app.put("/posts/{post_id}", response_model=schemas.PostOut)
def update_post(post_id: int, post: schemas.PostCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_post = crud.get_post(db, post_id)
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if db_post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this post")
    return crud.update_post(db, post_id, post)

@app.delete("/posts/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_post = crud.get_post(db, post_id)
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if db_post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")
    crud.delete_post(db, post_id)
    return {"detail": "Post deleted"}

@app.post("/posts/{post_id}/comments/", response_model=schemas.CommentOut)
def create_comment_for_post(post_id: int, comment: schemas.CommentCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_post = crud.get_post(db, post_id=post_id)
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")
    return crud.create_comment(db=db, comment=comment, user_id=current_user.id, post_id=post_id)

@app.get("/posts/{post_id}/comments/", response_model=List[schemas.CommentOut])
def read_comments_for_post(post_id: int, db: Session = Depends(get_db)):
    return crud.get_comments_by_post(db, post_id=post_id)


@app.delete("/comments/{comment_id}", status_code=204)
def delete_comment(comment_id: int, db: Session = Depends(get_db),
                   current_user: models.User = Depends(get_current_user)):
    db_comment = crud.get_comment(db, comment_id=comment_id)
    if not db_comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Ensure that only the comment owner or an admin can delete the comment
    if db_comment.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")

    crud.delete_comment(db=db, comment_id=comment_id)
    return


@app.put("/comments/{comment_id}", response_model=schemas.CommentOut)
def update_comment(comment_id: int, comment: schemas.CommentCreate, db: Session = Depends(get_db),
                   current_user: models.User = Depends(get_current_user)):
    db_comment = crud.get_comment(db, comment_id=comment_id)
    if not db_comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Убедитесь, что только владелец комментария или админ может редактировать его
    if db_comment.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to edit this comment")

    updated_comment = crud.update_comment(db=db, comment_id=comment_id, comment_data=comment)
    if not updated_comment:
        raise HTTPException(status_code=404, detail="Failed to update comment")

    return updated_comment

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))  # Используем PORT из переменных окружения
    uvicorn.run(app, host="0.0.0.0", port=port)
