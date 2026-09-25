# importing libraries 

from sqlalchemy.ext.asyncio import create_async_engine 
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import declarative_base 
import os 
from dotenv import load_dotenv

# ---------------------------------------------------------- #

# extracing the .env file 

load_dotenv()
username = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

DATABASE_URL = f"postgresql+asyncpg://{username}:{password}@localhost:5432/{db_name}"

engine = create_async_engine(DATABASE_URL, echo=True)

# session factory
asyncsessionlocal = async_sessionmaker(bind=engine, expire_on_commit=False)

base = declarative_base()


