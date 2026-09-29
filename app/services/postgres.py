import os 
import asyncpg

load_dotenv()
sername = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')




