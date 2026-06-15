from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles  # 1. Import the static file handler
# for exception handling
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from fastapi.exception_handlers import (
    http_exception_handler, request_validation_exception_handler)
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException as starletteHTTPException
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import models
from database import Base, engine, get_db
from routers import users,posts,authoriztion
from schema import Post_response
# Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # shutdown
    await engine.dispose()
app = FastAPI(lifespan=lifespan)

# 2. Mount the local 'static' directory onto the '/static' web URL path
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")

# 3. Configure the templates system configuration
templates = Jinja2Templates(directory="templates")
app.include_router(authoriztion.router,prefix="/api/auth",tags=["Auth"])
app.include_router(users.router,prefix="/api/users",tags=["users"])
app.include_router(posts.router,prefix="/api/posts",tags=['posts'])
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/posts", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)))
    posts_list = result.scalars().all()
    return templates.TemplateResponse(
        request, name="home.html",
        context={
            "posts_list": posts_list,
            "title": "Home"
        }
    )


# users post page
@app.get("/users/{user_id}/posts", include_in_schema=False, name="user_posts")
async def user_posts_page(
    request: Request,
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user is not found"
        )
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.user_id == user_id))
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request, name="users_post.html",
        context={
            "posts_list": posts,
            "title": f"{user.username}'s Posts"
        }
    )
@app.get("/posts/{post_id}", include_in_schema=False, response_model=Post_response)
async def post_page(request: Request, post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == post_id))
    post = result.scalars().first()
    if post:
        title = post.title
        return templates.TemplateResponse(
            request, name="post.html",
            context={
                "post": post,
                "title": title
            })
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail="Post is not found")

@app.get("/login",include_in_schema=False)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request, 
        name="login.html",
        context={"title": "Login"})
@app.get("/register",include_in_schema=False)
async def register_page(request: Request):
    return templates.TemplateResponse(
        request, 
        name="register.html",
        context={"title": "Register"})


# general http exception handler
@app.exception_handler(starletteHTTPException)
async def general_http_excetption_handler(request: Request, exception: starletteHTTPException):
    message = (exception.detail
               if exception.detail
               else "An error Occurred!")
    if request.url.path.startswith("/api"):
        return await http_exception_handler(request, exception)
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
