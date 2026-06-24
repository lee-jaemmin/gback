import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 로컬에서는 DATABASE_URL이 없으므로 기존처럼 grid.db를 사용합니다.
# Railway에서는 환경변수 DATABASE_URL에 Supabase Postgres 주소를 넣습니다.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./grid.db") # 얘만 큰 변화점. Railway: 그 url, 로컬: 기존 grid.db

# 일부 플랫폼/DB 서비스는 postgres:// 로 시작하는 URL을 줍니다.
# SQLAlchemy는 postgresql:// 형식을 더 안정적으로 인식하므로 변환합니다.
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1,
    )

# check_same_thread=False 는 SQLite 전용 옵션입니다.
# Postgres에 이 옵션을 넣으면 문제가 될 수 있으므로 SQLite일 때만 넣습니다.
connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
)

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