import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/insurelab.db")
JWT_SECRET = os.getenv("JWT_SECRET", "insurelab-secret-change-me")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
CALLBACK_TOKEN = os.getenv("CALLBACK_TOKEN", "callback-secret")
