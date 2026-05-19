from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base,sessionmaker
url="sqlite:///./my.db"
engine=create_engine(url,connect_args={"check_same_threads":False})
session=sessionmaker(bind=engine,autoflush=False,autocommit=False)
class base(declarative_base):
    pass
def get_db():
    with session() as db:
        yield db