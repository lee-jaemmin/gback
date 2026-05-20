from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# SQLite 파일 기반 데이터베이스 주소 (프로젝트 폴더에 grid.db 파일이 생깁니다)
SQLALCHEMY_DATABASE_URL = "sqlite:///./grid.db"

# 데이터베이스 엔진 생성
# check_same_thread는 SQLite에서만 필요한 특수 설정
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 데이터베이스에 접속해서 데이터를 넣고 뺄 '세션(대화 창구)' 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# DB 연결 세션을 열고 닫는 의존성 주입 함수 (나중에 API 만들 때 사용)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()