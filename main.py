from fastapi import FastAPI
from fastapi.responses import HTMLResponse  # 1. Must import this for HTML to work

app = FastAPI()

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
def home():
    return f"<h1>Welcome to first Fast API work done by Sanjog Gautam</h1><p>Navigate to /api/posts to see data.</p>"

# 3. Separate function for the HTML posts view
@app.get("/posts", response_class=HTMLResponse, include_in_schema=False)
def get_html_posts():
    return f"<h1>Featured Author: {posts[0]['name']}</h1>"

# 4. (This will show up in /docs)
@app.get("/api/posts")
def get_posts():
    return posts