from fastapi import APIRouter,HTTPException, status, Depends
# for exception handling
from sqlalchemy.ext.asyncio import AsyncSession
from schema import user_response, user_create
from typing import Annotated
from schema import Post_response,UserUpdate
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import models
from database import get_db
router=APIRouter()

@router.post("", response_model=user_response, status_code=status.HTTP_201_CREATED,)
async def create_user(user: user_create, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.username == user.username),)
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="username already exists",
        )
    result = await db.execute(select(models.User).where(models.User.email == user.email),)
    existing_email = result.scalars().first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email already exists",
        )
    new_user = models.User(
        username=user.username,
        email=user.email,
        image_file=user.image_file,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.get("", response_model=list[user_response])
async def get_user(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User)
    )
    user = result.scalars().all()
    return user


@router.get("/{user_id}", response_model=user_response)
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
@router.patch("/{user_id}", response_model=user_response)
async def user_update_parital(user_id: int, user_data: UserUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user_data.username is not None and user_data.username != user.username:
        result = await db.execute(
            select(models.User).where(
                models.User.username == user_data.username)
        )
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="username already exists"
            )
    if user_data.email is not None and user_data.email != user.email:
        result = await db.execute(
            select(models.User).where(models.User.email == user_data.email)
        )
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="email already exists"
            )
    if user_data.email is not None:
        user.email = user_data.email
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
