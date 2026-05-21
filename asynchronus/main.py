from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles  # 1. Import the static file handler
# for exception handling
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from fastapi.exception_handlers import(http_exception_handler,request_validation_exception_handler)
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException as starletteHTTPException
from schema import user_response, user_create
from typing import Annotated
from schema import Post_response, PostCreate,PostUpdate,UserUpdate
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload
import models
from database import Base, engine, get_db
# Base.metadata.create_all(bind=engine)
@asynccontextmanager
async def lifespan(app:FastAPI):
    #startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    #shutdown
    await engine.dispose()
app = FastAPI(lifespan=lifespan)

# 2. Mount the local 'static' directory onto the '/static' web URL path
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media",StaticFiles(directory="media"),name="media")

# 3. Configure the templates system configuration
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/posts", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request,db:Annotated[AsyncSession,Depends(get_db)]):
    result=await db.execute(select(models.Post).options(selectinload(models.Post.author)))
    posts=result.scalars().all()
    return templates.TemplateResponse(
        request, name="home.html",
        context={
            "posts_list": posts,
            "title": "Home"
        }
    )


@app.get("/posts/{post_id}", include_in_schema=False, response_model=Post_response)
async def post_page(request: Request, post_id: int,db:Annotated[AsyncSession,Depends(get_db)]):
    result=await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id==post_id))
    post=result.scalars().first()
    if post:
            title=post.title
            return templates.TemplateResponse(
                request, name="post.html",
                context={
                    "post": post,
                    "title": title
                })
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail="Post is not found")
# it is way to implement the url path


@app.get("/api/posts/{post_id}",response_model=Post_response)
async def get_posts(post_id: int,db:Annotated[AsyncSession,Depends(get_db)]):
    result=await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id==post_id))
    post=result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail="Post is not found")
    return post

#update post put
@app.put("/api/posts/{post_id}",response_model=Post_response)
async def update_post_full(post_id: int,post_data:PostCreate,db:Annotated[AsyncSession,Depends(get_db)]):
    result= await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id==post_id))
    post=result.scalars().first()
    if not post:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail="Post is not found")
    if post_data.user_id!=post.user_id:
        result=await db.execute(select(models.User).where(models.User.id ==post_data.user_id))
        user=result.scalars().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not Found",
            )
    post.title= post_data.title
    post.content=post_data.content
    post.user_id=post_data.user_id
    await db.commit()
    await db.refresh(post , attribute_names=['author'])
    return post

#update post patch
@app.patch("/api/posts/{post_id}",response_model=Post_response)
async def update_post_partial(post_id: int,post_data:PostUpdate,db:Annotated[AsyncSession,Depends(get_db)]):
    result= await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id==post_id))
    post=result.scalars().first()
    if not post:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail="Post is not found")
    update_data=post_data.model_dump(exclude_unset=True)#without it will include all field with their default
    for field,value in update_data.items():
        setattr(post,field,value)
    await db.commit()
    await db.refresh(post,attribute_names=["author"])
    return post
#delete a post
@app.delete("/api/posts/{post_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id:int,db:Annotated[AsyncSession,Depends(get_db)]):
    result=await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id==post_id))
    post=result.scalars().first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post Not Found"
        )
    await db.delete(post)
    await db.commit()
#not using select in load in users because user_response doesn't have relationship 
@app.post("/api/users", response_model=user_response, status_code=status.HTTP_201_CREATED,)
async def create_user(user: user_create,db: Annotated[AsyncSession,Depends(get_db)]):
    result= await db.execute(select(models.User).where(models.User.username==user.username),)
    existing_user=result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="username already exists",
        )
    result=await db.execute(select(models.User).where(models.User.email==user.email),)
    existing_email=result.scalars().first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email already exists",
        )
    new_user=models.User(
        username=user.username,
        email=user.email,
        image_file=user.image_file,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@app.get("/api/users",response_model=list[user_response])
async def get_user(db : Annotated[AsyncSession,Depends(get_db)]):
    result=await db.execute(
        select(models.User)
    )
    user=result.scalars().all()
    return user

@app.get("/api/users/{user_id}",response_model=user_response)
async def get_user(user_id: int,db : Annotated[AsyncSession,Depends(get_db)]):
    result=await db.execute(
        select(models.User).where(models.User.id==user_id)
    )
    user=result.scalars().first()
    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")
#user delete
@app.delete("/api/users/{user_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int,db : Annotated[AsyncSession,Depends(get_db)]):
    result=await db.execute(
        select(models.User).where(models.User.id==user_id)
    )
    user=result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")
    await db.delete(user)
    await db.commit()
#user patch update:
@app.patch("/api/users/{user_id}",response_model=user_response)
async def user_update_parital(user_id: int,user_data:UserUpdate,db : Annotated[AsyncSession,Depends(get_db)]):
    result=await db.execute(
        select(models.User).where(models.User.id==user_id)
    )
    user=result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="User not found")
    if user_data.username is not None and user_data.username!= user.username:
        result=await db.execute(
            select(models.User).where(models.User.username == user_data.username)
        )
        existing_user=result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="username already exists"
            )
    if user_data.email is not None and user_data.email!= user.email:
        result=await db.execute(
            select(models.User).where(models.User.email == user_data.email)
        )
        existing_user=result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="email already exists"
            )
    if user_data.email is not None:
        user.email=user_data.email
    if user_data.username is not None:
        user.username=user_data.username
    if user_data.image_file is not None:
        user.image_file=user_data.image_file
    #or we can also use
    # data=user_data.model_dump(exclude_unset=True)
    # for field,value in data.items():
    #     setattr(user,field,value)
    await db.commit()
    await db.refresh(user)
    return user
    

#get all the post by a specific user
@app.get("/api/users/{user_id}/posts",response_model=list[Post_response])
async def get_user_posts(user_id:int,db: Annotated[AsyncSession,Depends(get_db)]):
    result=await db.execute(select(models.User).where(models.User.id ==user_id))
    user=result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not Found",
        )
    result= await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.user_id==user_id))
    posts= result.scalars().all()
    return posts
#user sdsfds sdd
# for validation of the data missing filed pani vetauxa and extra data nee hataidinxa
@app.get("/api/posts", response_model=list[Post_response])
async def get_posts(db: Annotated[AsyncSession,Depends(get_db)]):
    result=await db.execute(select(models.Post).options(selectinload(models.Post.author)))
    posts=result.scalars().all()
    return posts


@app.post("/api/posts", response_model=Post_response,status_code=status.HTTP_201_CREATED)
async def create_post(post: PostCreate,db: Annotated[AsyncSession,Depends(get_db)]):
    result=await db.execute(select(models.User).where(models.User.id==post.user_id))
    user=result.scalars().all()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    new_post=models.Post(
        title=post.title,
        content=post.content,
        user_id=post.user_id,
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post,attribute_names=['author'])
    return new_post


#users post page
@app.get("/users/{user_id}/posts",include_in_schema=False,name="user_posts")
async def user_posts_page(
    request: Request,
    user_id:int,
    db:Annotated[AsyncSession,Depends(get_db)]
):
    result=await db.execute(select(models.User).where(models.User.id==user_id))
    user=result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user is not found"
        )
    result=await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.user_id==user_id))
    posts=result.scalars().all()
    return templates.TemplateResponse(
        request,name="users_post.html",
        context={
            "posts_list":posts,
            "title": f"{user.username}'s Posts"
        }
    )

# general http exception handler


@app.exception_handler(starletteHTTPException)
async def general_http_excetption_handler(request: Request, exception: starletteHTTPException):
    message = (exception.detail
               if exception.detail
               else "An error Occurred!")
    if request.url.path.startswith("/api"):
        return await http_exception_handler(request,exception)
    return templates.TemplateResponse(request, name="error.html",
                                      context={
                                          "status_code": exception.status_code,
                                          "title": exception.status_code,
                                          "message": message
                                      },
                                      status_code=exception.status_code)
# general request validation error


@app.exception_handler(RequestValidationError)
async def general_validation_excetption_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return await request_validation_exception_handler(request, exception)
    return templates.TemplateResponse(request, name="error.html",
                                      context={
                                          "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
                                          "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
                                          "message": "invalid Request! check your input and try again"
                                      },
                                      status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)
