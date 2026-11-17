import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import DATABASE_URL


def _sqlite_file_path(url: str):
    prefix = "sqlite:///"
    if not url.startswith(prefix):
        return None
    raw = url[len(prefix):]
    if raw in (":memory:", "") or raw.startswith("file:"):
        return None
    return raw


_path = _sqlite_file_path(DATABASE_URL)
if _path:
    parent = os.path.dirname(os.path.abspath(_path))
    if parent:
        os.makedirs(parent, exist_ok=True)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from .models import Base

    Base.metadata.create_all(bind=engine)
