import os

from dotenv import load_dotenv

load_dotenv()

# --- Autenticação / JWT ---
SECRET_KEY = os.getenv("SECRET_KEY", "change_me_super_secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# --- APIs externas ---
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")

# --- Banco de dados ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database.db")
