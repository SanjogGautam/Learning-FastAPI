from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles  # 1. Import the static file handler
# for exception handling
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as starletteHTTPException
from schema import user_response, user_create
from typing import Annotated
from schema import Post_response, PostCreate
from sqlalchemy import select
from sqlalchemy.orm import Session
import models
from database import Base, engine, get_db

Base.metadata.create_all(bind=engine)
app = FastAPI()

# 2. Mount the local 'static' directory onto the '/static' web URL path
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media",StaticFiles(directory="media"),name="media")

# 3. Configure the templates system configuration
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/posts", response_class=HTMLResponse, include_in_schema=False)
def home(request: Request,db:Annotated[Session,Depends(get_db)]):
    result=db.execute(select(models.Post))
    posts=result.scalars().all()
    return templates.TemplateResponse(
        request, name="home.html",
        context={
            "posts_list": posts,
            "title": "Home"
        }
    )


@app.get("/posts/{post_id}", include_in_schema=False, response_model=list[Post_response])
def post_page(request: Request, post_id: int,db:Annotated[Session,Depends(get_db)]):
    result=db.execute(select(models.Post).where(models.Post.id==post_id))
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
def get_posts(post_id: int,db:Annotated[Session,Depends(get_db)]):
    result=db.execute(select(models.Post).where(models.Post.id==post_id))
    post=result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail="Post is not found")
    return post

@app.post("/api/users", response_model=user_response, status_code=status.HTTP_201_CREATED,)
def create_user(user: user_create,db: Annotated[Session,Depends(get_db)]):
    result= db.execute(select(models.User).where(models.User.username==user.username),)
    existing_user=result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="username already exists",
        )
    result=db.execute(select(models.User).where(models.User.email==user.email),)
    existing_email=result.scalars().first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email already exists",
        )
    new_user=models.User(
        username=user.username,
        email=user.email,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/api/users/{user_id}",response_model=user_response)
def get_user(user_id: int,db : Annotated[Session,Depends(get_db)]):
    result=db.execute(
        select(models.User).where(models.User.id==user_id)
    )
    user=result.scalars().first()
    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")
#get all the post by a specific user
@app.get("/api/users/{user_id}/posts",response_model=list[Post_response])
def get_user_posts(user_id:int,db: Annotated[Session,Depends(get_db)]):
    result=db.execute(select(models.User).where(models.User.id ==user_id))
    user=result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not Found",
        )
    result= db.execute(select(models.Post).where(models.Post.user_id==user_id))
    posts= result.scalars().all()
    return posts

# for validation of the data missing filed pani vetauxa and extra data nee hataidinxa
@app.get("/api/posts", response_model=list[Post_response])
def get_posts(db: Annotated[Session,Depends(get_db)]):
    result=db.execute(select(models.Post))
    posts=result.scalars().all()
    return posts


@app.post("/api/posts", response_model=Post_response,status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate,db: Annotated[Session,Depends(get_db)]):
    result=db.execute(select(models.User).where(models.User.id==post.user_id))
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
    db.commit()
    db.refresh(new_post)
    return new_post


#users post page
@app.get("/users/{user_id}/posts",include_in_schema=False,name="user_posts")
def user_posts_page(
    request: Request,
    user_id:int,
    db:Annotated[Session,Depends(get_db)]
):
    result=db.execute(select(models.User).where(models.User.id==user_id))
    user=result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user is not found"
        )
    result=db.execute(select(models.Post).where(models.Post.user_id==user_id))
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
def general_http_excetption_handler(request: Request, exception: starletteHTTPException):
    message = (exception.detail
               if exception.detail
               else "An error Occurred!")
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exception.status_code,
            content={"detail": message}
        )
    return templates.TemplateResponse(request, name="error.html",
                                      context={
                                          "status_code": exception.status_code,
                                          "title": exception.status_code,
                                          "message": message
                                      },
                                      status_code=exception.status_code)
# general request validation error


@app.exception_handler(RequestValidationError)
def general_http_excetption_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": exception.errors()}
        )
    return templates.TemplateResponse(request, name="error.html",
                                      context={
                                          "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
                                          "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
                                          "message": "invalid Request! check your input and try again"
                                      },
                                      status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)
