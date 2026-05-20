from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone, UTC

# SQLAlchemy의 기본 모델 클래스 생성
# ERD를 코드로 만드는 파일
Base = declarative_base()


# Company 테이블
# index: 빠른 검사를 위해 색인 생성하라. pk, unique옵션에 자동으로 쓰임
# unique: 같은 데이터는 불가. ex) 같은 이름을 쓰는 회사명 불가
class Company(Base):
    __tablename__ = "companies" # 실제 DB에 들어갈 이름

    id = Column(String, primary_key=True, index=True) 
    name = Column(String, nullable=False) # 업장명
    addr = Column(String, nullable=False) # 지역별: 홍대, 이태원 등
    created_at = Column(DateTime(timezone=True ), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # 관계 설정 (한 업장은 여러 스태프와 여러 테이블을 가집니다)
    users = relationship("User", back_populates="company")
    tables = relationship("TableMaster", back_populates="company")
    items = relationship("Items", back_populates="company")
    tablegroups = relationship("TableGroup", back_populates="company")
    # back_populates: 양방향 동기화. 양쪽이 서로의 상태 변화를 실시간 반영
    # 코딩할 때 편함. ex) my_company.users 라고 치면 유저 이름 쫙 나열 가능
    # 'User'은 관계를 맺을 클래스의 이름
    # 'company'는 다른 클래스에 선언된 변수


# User (스태프/사용자) 테이블. users collection
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True) # uid
    username = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, default="user", nullable=False) # 'admin' or 'user'
    fcmtoken = Column(String, nullable=True) # 푸시 알림용
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    tablecardfields = Column(JSON, default=["purchases", "persons"])

    # FK
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    #관계 정의
    company = relationship("Company", back_populates="users")
    table = relationship("TableMaster", back_populates="user")

# TableMaster
class TableMaster(Base):
    __tablename__ = "table_master"

    id = Column(String, primary_key=True, index=True)
    tablename = Column(String, nullable=False)
    section = Column(String, nullable=False)
    status = Column(String, default="available") # "available" or "inuse" 
    price = Column(Integer, default=0)
    # 손님 정보
    customer = Column(String, default="")
    phonenumber = Column(String, default="")
    persons = Column(Integer, default=0)
    remark = Column(Text, default="")
    registered_at = Column(DateTime, nullable=True)    
    
    # 합석 처리
    group_id = Column(String, index=True, nullable=True)
    ismaster = Column(Boolean, default=False)
    mastertablenumber = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # FK
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    company = relationship("Company", back_populates="tables")
    user = relationship("User", back_populates="tables")

class TableHistory(Base):
    __tablename__ = "table_histories"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False) # hid
    table_id = Column(String, nullable=False)
    tablename = Column(String, nullable=False) # 기록 당시의 테이블명
    section = Column(String, nullable=False)
    total_price = Column(Integer, default=0)
    customer_name = Column(String, default="")
    customer_phone = Column(String, default="")
    persons = Column(Integer, default=0)
    remark = Column(Text, default="")
    user_id = Column(String, default="")
    user_name = Column(String, default="")
    company_id = Column(String)
    registered_at = Column(DateTime(timezone=True), nullable=True)
    out_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    table_history_purchases = relationship("TableHistoryPurchases", back_populates="history", cascade="all, delete-orphan")


class TableHistoryPurchases(Base):
    __tablename__ = "table_history_purchases"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, nullable=True)
    item_name = Column(String, nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Integer, default=0)
    total_price = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=True)
    history_id = Column(Integer, ForeignKey("table_histories.id"))
    
    history = relationship("TableHistory", back_populates="table_history_purchases")