from fastapi import FastAPI, Request,HTTPException,status
from fastapi.responses import HTMLResponse 
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles  # 1. Import the static file handler
#for exception handling
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as starletteHTTPException
from schema import user_response,user_create 
app = FastAPI()

# 2. Mount the local 'static' directory onto the '/static' web URL path
app.mount("/static", StaticFiles(directory="static"), name="static")

# 3. Configure the templates system configuration
templates = Jinja2Templates(directory="templates")

posts: list[dict] = [
    {
        "id": 1,
        "name": "Sanjog Gautam",
        "content": "Hello my name is sanjog gautam and i am from Parbat!",
        "date_posted":"sanjog"
    },
    {
        "id": 2,
        "name": "Sarin Pradhan",
        "content": "Hello my name is Sarin Pradhan and i am from Kirtipur!",
        "date_posted":"sanjog"
    }
]

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/posts", response_class=HTMLResponse, include_in_schema=False)
def home(request: Request):
    return templates.TemplateResponse(
        request,name="home.html",
        context={
            "posts_list": posts, 
            "title": "Home"
        }
    )
@app.get("/posts/{post_id}",include_in_schema=False,response_model=user_response)
def post_page(request:Request,post_id:int):
    for post in posts:
        if post.get("id")==post_id:
            return templates.TemplateResponse(
        request,name="post.html",
        context={
            "post": post, 
            "title": post['name']
        } )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post is not found")
#it is way to implement the url path
@app.get("/api/posts/{post_id}")
def get_posts(post_id:int):
    for post in posts:
        if post.get("id")==post_id:
            return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post is not found")

@app.get("/api/posts",response_model=list[user_response])#for validation of the data missing filed pani vetauxa and extra data nee hataidinxa
def get_posts():
    return posts
@app.post("/api/posts",response_model=user_response,status_code=status.HTTP_201_CREATED,)
def create_post(post:user_create):
    new_id=max(p["id"] for p in posts)+1 if posts else 1
    newpost={
        "id":new_id,
        "name":post.name,
        "content":post.content,
        "date_posted":"June 29 2005"
    }
    posts.append(newpost)
    return newpost   
#general http exception handler
@app.exception_handler(starletteHTTPException)
def general_http_excetption_handler(request:Request,exception: starletteHTTPException):
    message=(exception.detail
             if exception.detail
             else "An error Occurred!")
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exception.status_code,
            context={"detail": message}
        )
    return templates.TemplateResponse(request, name="error.html",
                                      context=
                                      {
                                       "status_code":exception.status_code,
                                       "title": exception.status_code,
                                       "message": message  
                                      },
                                      status_code=exception.status_code)
#general request validation error
@app.exception_handler(RequestValidationError)
def general_http_excetption_handler(request:Request,exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            context={"detail": exception.errors()}
        )
    return templates.TemplateResponse(request, name="error.html",
                                      context=
                                      {
                                       "status_code":status.HTTP_422_UNPROCESSABLE_CONTENT,
                                       "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
                                       "message": "invalid Request! check your input and try again"
                                      },
                                      status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)