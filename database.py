import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    raise RuntimeError("DATABASE_URL is required")

# 기본 드라이버 변경의 영향을 받지 않도록 설치된 psycopg2를 명시합니다.
if SQLALCHEMY_DATABASE_URL.startswith(("postgres://", "postgresql://")):
    SQLALCHEMY_DATABASE_URL = (
        "postgresql+psycopg2://" + SQLALCHEMY_DATABASE_URL.split("://", 1)[1]
    )

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
