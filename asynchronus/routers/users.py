from fastapi import APIRouter,HTTPException, status, Depends
# for exception handling
from sqlalchemy.ext.asyncio import AsyncSession
from schema import user_public,user_private, user_create,token
from typing import Annotated
from schema import Post_response,UserUpdate
from sqlalchemy import select,func
from sqlalchemy.orm import selectinload
import models
from database import get_db
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from config import settings
from auth import create_access_token,hash_password,oauth2_scheme,verify_access_token,verify_password
router=APIRouter()


@router.post("", response_model=user_private, status_code=status.HTTP_201_CREATED,)
async def create_user(user: user_create, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(func.lower(models.User.username) == user.username.lower()),)
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="username already exists",
        )
    result = await db.execute(select(models.User).where(func.lower(models.User.email) == user.email.lower()),)
    existing_email = result.scalars().first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email already exists",
        )
    new_user = models.User(
        username=user.username,
        email=user.email.lower(),
        image_file=user.image_file,
        password_hash=hash_password(user.password),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.post("/token",response_model=token)
async def login_for_acces_token(form_data: Annotated[OAuth2PasswordRequestForm,Depends()],
                db: Annotated[AsyncSession,Depends(get_db)]):
    #noted: oauth2requestform will send the data in form-data format and the username and password will be in the fields named "username" as email and "password" respectively
    email=form_data.username
    result = await db.execute(select(models.User).where(func.lower(models.User.email)==email.lower()))
    user = result.scalars().first()     
    #verify the password and the user
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    #dreate the access token
    access_token = create_access_token(data={"sub": str(user.id)}, 
                                       expires_delta=timedelta(minutes=settings.access_token_expire_minutes))
    return token(access_token=access_token, token_type="bearer")

#specific user get by id to get the current logged in user details we can use the token and get the user email from the token and then get the user details from the database
@router.get("/me", response_model=user_private)
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Annotated[AsyncSession, Depends(get_db)]):
    user_id = verify_access_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    result = await db.execute(select(models.User).where(models.User.id == int(user_id)))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.get("", response_model=list[user_public])
async def get_user(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User)
    )
    user = result.scalars().all()
    return user


@router.get("/{user_id}", response_model=user_public)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    user = result.scalars().first()
    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found")
# user delete


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await db.delete(user)
    await db.commit()

# user patch update:
@router.patch("/{user_id}", response_model=user_public)
async def user_update_parital(user_id: int, user_data: UserUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user_data.username is not None and user_data.username.lower() != user.username.lower():
        result = await db.execute(
            select(models.User).where(
                func.lower(models.User.username) == user_data.username.lower()
            )
        )
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="username already exists"
            )
    if user_data.email is not None and user_data.email.lower() != user.email.lower():
        result = await db.execute(
            select(models.User).where(func.lower(models.User.email) == user_data.email.lower())
        )
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="email already exists"
            )
    if user_data.email is not None:
        user.email = user_data.email.lower()
    if user_data.username is not None:
        user.username = user_data.username
    if user_data.image_file is not None:
        user.image_file = user_data.image_file
    # or we can also use
    # data=user_data.model_dump(exclude_unset=True)
    # for field,value in data.items():
    #     setattr(user,field,value)
    await db.commit()
    await db.refresh(user)
    return user


# get all the post by a specific user
@router.get("/{user_id}/posts", response_model=list[Post_response])
async def get_user_posts(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not Found",
        )
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.user_id == user_id))
    posts = result.scalars().all()
    return posts
