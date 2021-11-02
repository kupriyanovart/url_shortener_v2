from pathlib import Path


SERVER_ADDRESS = (HOST, PORT) = "", 8888
SITE_URL = "http://localhost:8888"
BASE_DIR = Path.cwd()
DB_NAME = "urls_database"


DB = {
    "drivername": "sqlite",
    "database": "db.sqlite",
    }
