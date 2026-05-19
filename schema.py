from pydantic import BaseModel, Field, ConfigDict, EmailStr
from datetime import datetime

# 1. The Shared Blueprint (Fields common to both creating and reading data)
class userBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=40)
    content: str = Field(..., min_length=5, max_length=1056)

# 2. The Input Schema (What the server expects when a user registers)
class user_create(userBase):
    pass

# 3. The Output Schema (What the server sends safely back to the browser)
class user_response(userBase):
    id: int # Automatically provided by your database
    date_posted: str
    # Allows Pydantic to read database object attributes directly
    model_config = ConfigDict(from_attributes=True)