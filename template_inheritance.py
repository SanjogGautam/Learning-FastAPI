from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse 
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles  # 1. Import the static file handler

app = FastAPI()

# 2. Mount the local 'static' directory onto the '/static' web URL path
app.mount("/static", StaticFiles(directory="static"), name="static")

# 3. Configure the templates system configuration
templates = Jinja2Templates(directory="templates")

posts: list[dict] = [
    {
        "id": 1,
        "name": "Sanjog Gautam",
        "content": "Hello my name is sanjog gautam and i am from Parbat!"
    },
    {
        "id": 2,
        "name": "Sarin Pradhan",
        "content": "Hello my name is Sarin Pradhan and i am from Kirtipur!"
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

@app.get("/api/posts")
def get_posts():
    return posts