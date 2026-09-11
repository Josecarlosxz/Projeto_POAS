from fastapi.security import OAuth2PasswordBearer

# --- JWT config ---
SECRET_KEY = "change_me_super_secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

# --- API KEYS ---
API_KEY = "d5c981928b0548918cd5f360ffb63759"
YOUTUBE_API_KEY = "AIzaSyBNSESwTKK4l2qNDGjYtZSB35aGD_DkOEU"
