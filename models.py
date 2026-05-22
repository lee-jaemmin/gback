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
    items = relationship("Item", back_populates="company")
    table_groups = relationship("TableGroup", back_populates="company")
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
    tablecardfields = Column(JSON, default=lambda: ["purchases", "persons"])

    # FK
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    #관계 정의
    company = relationship("Company", back_populates="users")
    tables = relationship("TableMaster", back_populates="user")

# TableMaster
class TableMaster(Base):
    __tablename__ = "table_master"

    id = Column(String, primary_key=True, index=True)
    tablename = Column(String, nullable=False)
    section = Column(String, nullable=False)
    status = Column(String, default="available") # "available" or "inuse" 
    total_price = Column(Integer, default=0)
    # 손님 정보
    customer = Column(String, default="")
    phonenumber = Column(String, default="")
    persons = Column(Integer, default=0)
    remark = Column(Text, default="")
    registered_at = Column(DateTime(timezone=True), nullable=True)    
    
    # 합석 처리
    ismaster = Column(Boolean, default=False)
    mastertablenumber = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # FK
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    group_id = Column(String, ForeignKey("table_groups.id"), nullable=True)
    company = relationship("Company", back_populates="tables")
    user = relationship("User", back_populates="tables")
    reservations = relationship("Reservation", back_populates="table")
    ## group과 table은 2개의 관계가 얽혀 있기에 foreign_keys로 명시 필요
    ## foreign_keys : = 연산자 뒤에 있는 거랑 일치하는 애들만 가져옴. 사실 얘 없어도 모든 relationship은 그렇게 동작함.
    ## [group_id]를 기준으로 필터링 = group이 지배자. 테이블은 그룹을 이루는 일원
    ## "TableGroup.master_table_id"를 기준으로 필터링 = 테이블이 지배자. 마스터 테이블을 기준으로 그룹을 찾음.
    group = relationship("TableGroup", foreign_keys=[group_id], back_populates="tables")
    mastered_group = relationship("TableGroup", back_populates="master_table", foreign_keys="TableGroup.master_table_id", uselist=False)
    
    ## mytable.purchases 호출 -> TablePurchase객체 감. -> FK가 tables_id인 거를 보고 이걸 기준 삼음.
    ## 결론적으로 db에서 내 table_id와 일치하는 결과를 가져옴.
    purchases = relationship(
        "TablePurchase",
        back_populates="table",
        cascade="all, delete-orphan",
    )

class TablePurchase(Base):
    __tablename__ = "table_purchases"

    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String, nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Integer, default=0, nullable=False)
    total_price = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    # FK
    table_id = Column(String, ForeignKey("table_master.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)

    table = relationship("TableMaster", back_populates="purchases")
    item = relationship("Item", back_populates="table_purchases")
class TableHistory(Base):
    __tablename__ = "table_histories"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False) # hid
    table_id = Column(String, nullable=False)
    tablename = Column(String, nullable=False) # 기록 당시의 테이블명
    section = Column(String, nullable=False)
    total_price = Column(Integer, default=0, nullable=False)
    customer_name = Column(String, default="")
    customer_phone = Column(String, default="")
    persons = Column(Integer, default=0)
    remark = Column(Text, default="")
    user_id = Column(String, default="", nullable=False)
    user_name = Column(String, default="", nullable=False)
    company_id = Column(String, nullable=False)
    registered_at = Column(DateTime(timezone=True), nullable=False)
    out_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    table_history_purchases = relationship("TableHistoryPurchase", back_populates="history", cascade="all, delete-orphan")


class TableHistoryPurchase(Base):
    __tablename__ = "table_history_purchases"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, nullable=False)
    item_name = Column(String, nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Integer, default=0)
    total_price = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=True)
    history_id = Column(Integer, ForeignKey("table_histories.id"), nullable=False)
    
    history = relationship("TableHistory", back_populates="table_history_purchases")

class ItemCategory(Base):

    __tablename__ = "item_categories"

    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String, index=True, unique=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean,default=True)
    items = relationship("Item", back_populates="category")

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String, nullable=False, index=True)
    item_price = Column(Integer, nullable=False)
    is_active = Column(Boolean,default=True, nullable=False)
    created_at = Column(DateTime(timezone=True ), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True ), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    
    #FK
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("item_categories.id"), nullable=False, index=True)
    company = relationship("Company", back_populates="items")
    category = relationship("ItemCategory", back_populates="items")
    reservation_purchases = relationship("ReservationPurchase", back_populates="item")
    table_purchases = relationship("TablePurchase", back_populates="item")


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    reservation_time = Column(DateTime(timezone=True ), default=lambda: datetime.now(UTC), nullable=False)
    reservation_price = Column(Integer, default=0)
    customer_name = Column(String, default="", nullable=False)
    customer_phone = Column(String, default="")
    created_at = Column(DateTime(timezone=True ), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True ), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    #FK
    table_id = Column(String, ForeignKey("table_master.id"), nullable=False)
    table = relationship("TableMaster", back_populates="reservations")
    reservation_purchases = relationship("ReservationPurchase", back_populates="reservation")


class ReservationPurchase(Base):
    __tablename__ = "reservation_purchases"

    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String, default="", nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Integer, default=0)
    total_price = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True ), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True ), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    #FK
    reservation_id = Column(Integer, ForeignKey("reservations.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    reservation = relationship("Reservation", back_populates="reservation_purchases")
    item = relationship("Item", back_populates="reservation_purchases")


class TableGroup(Base):
    __tablename__ = "table_groups"

    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True ), default=lambda: datetime.now(UTC), nullable=False)
    closed_at = Column(DateTime(timezone=True ), nullable=True)
    #FK
    master_table_id = Column(String, ForeignKey("table_master.id"), nullable=False)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    master_table = relationship("TableMaster", foreign_keys=[master_table_id], back_populates="mastered_group")
    # 어느 외래키를 참조할지 명시
    tables = relationship(
        "TableMaster",
        foreign_keys="TableMaster.group_id",
        back_populates="group",
    )
    company = relationship("Company", back_populates="table_groups")