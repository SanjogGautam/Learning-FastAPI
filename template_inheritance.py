from fastapi import FastAPI,Request
from fastapi.responses import HTMLResponse  # 1. Must import this for HTML to work
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()
templates=Jinja2Templates(directory="templates")

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

# 2. Separate function for the root URL

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/posts", response_class=HTMLResponse, include_in_schema=False)
def home(request:Request):
    return templates.TemplateResponse(
        request,name="home.html",
        context={
            "posts_list":posts,
            "title":"Home"
        }
    )

# # 3. Separate function for the HTML posts view
# @app.get("/posts", response_class=HTMLResponse, include_in_schema=False)
# def get_html_posts():
#     return f"<h1>Featured Author: {posts[0]['name']}</h1>"

# 4. (This will show up in /docs)
@app.get("/api/posts")
def get_posts():
    return posts