from datetime import UTC,datetime,timedelta
import jwt
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from config import settings
passowrd_hash=PasswordHash.recommended()#to hash the password
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="api/users/token")
def hash_password(password:str):
    return passowrd_hash.hash(password)
def verify_password(plain_password:str,hashed_password:str):
    return passowrd_hash.verify(plain_password,hashed_password)
#to create access token
def create_access_token(data:dict,expires_delta:timedelta|None=None):
    to_encode=data.copy()
    if expires_delta:
        expire=datetime.now(tz=UTC)+expires_delta
    else:
        expire=datetime.now(tz=UTC)+timedelta(minutes=15)
    to_encode.update({"exp":expire})
    encoded_jwt=jwt.encode(to_encode,settings.secret_key.get_secret_value(),algorithm=settings.algorithm)
    return encoded_jwt
#to verify the access tokens
def verify_access_token(token:str):
    """Verifies the access tokens and returns the subject(user id) if valid"""
    try: 
        payload=jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
            options={"require":['exp','sub']},
            )
    except jwt.InvalidTokenError:
        return None
    else:
        return payload.get("sub")