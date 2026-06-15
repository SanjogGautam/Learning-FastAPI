from pydantic import BaseModel, Field, ConfigDict, EmailStr
from datetime import datetime

# 1. The Shared Blueprint (Fields common to both creating and reading data)
class userBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=40)
    email: EmailStr = Field(...,max_length=120)

# 2. The Input Schema (What the server expects when a user registers)
class user_create(userBase):
    image_file: str | None = Field(default=None, max_length=200)
    password:str = Field(..., min_length=6, max_length=128)


# 3. The Output Schema (What the server sends safely back to the browser)
class user_public(BaseModel):
    # Allows Pydantic to read database object attributes directly
    model_config = ConfigDict(from_attributes=True)
    image_file: str | None
    image_path: str
class user_private(userBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: EmailStr
    image_file: str | None
class UserUpdate(BaseModel):
    username: str|None = Field(default=None,min_length=3, max_length=40)
    email: EmailStr|None = Field(default=None,max_length=120)
    image_file: str | None = Field(default=None,min_length=3, max_length=40)
class token(BaseModel):
    access_token: str
    token_type: str 

class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=50)
    content: str = Field(min_length=1)
class PostCreate(PostBase):
    pass

class Post_response(PostBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    date_posted:datetime
    author: user_public 
class PostUpdate(BaseModel):
    title: str|None = Field(default=None,min_length=1, max_length=50)
    content: str|None = Field(default=None,min_length=1)
