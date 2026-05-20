from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase,sessionmaker
# 1. Ensure this string starts with EXACTLY three slashes for a local relative file path
URL = "sqlite:///my.db"

# 2. Safety Check: Only inject connect_args if we are actually loading a SQLite cluster instance
if URL.startswith("sqlite"):
    engine = create_engine(URL, connect_args={"check_same_thread": False})
else:
    # If you transition to PostgreSQL or MySQL later, they don't use check_same_threads
    engine = create_engine(URL)
session=sessionmaker(bind=engine,autoflush=False,autocommit=False)
class Base(DeclarativeBase):
    pass
def get_db():
    with session() as db:
        yield db