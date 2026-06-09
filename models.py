from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    JSON,
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, UTC


Base = declarative_base()


def utc_now():
    return datetime.now(UTC)


class Company(Base):
    __tablename__ = "companies"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    invite_code = Column(String, unique=True, nullable=True, index=True)
    region = Column(String, nullable=False)
    sections = Column(JSON, nullable=False, default=lambda: ['A', 'B', 'C', 'D', 'E'])

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    users = relationship("User", back_populates="company")
    tables = relationship("TableMaster", back_populates="company")
    items = relationship("Item", back_populates="company")
    table_groups = relationship("TableGroup", back_populates="company")


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, default="user", nullable=False)
    fcmtoken = Column(String, nullable=True)

    tablecardfields = Column(
        JSON,
        default=lambda: ["purchases", "persons"],
        nullable=False,
    )

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    company_id = Column(String, ForeignKey("companies.id"), nullable=False)

    company = relationship("Company", back_populates="users")
    tables = relationship("TableMaster", back_populates="user")


class TableMaster(Base):
    __tablename__ = "table_master"

    id = Column(String, primary_key=True, index=True)

    tablename = Column(String, nullable=False)
    section = Column(String, nullable=False)
    status = Column(String, default="available", nullable=False)

    customer = Column(String, default="", nullable=False)
    phonenumber = Column(String, default="", nullable=False)
    persons = Column(Integer, default=0, nullable=False)
    remark = Column(Text, default="", nullable=False)

    total_price = Column(Integer, default=0, nullable=False)
    registered_at = Column(DateTime(timezone=True), nullable=True)

    ismaster = Column(Boolean, default=False, nullable=False)
    mastertable_id = Column(String, nullable=True)
    
    timer_started_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    user_name = Column(String, nullable=True)
    group_id = Column(String, ForeignKey("table_groups.id"), nullable=True)

    company = relationship("Company", back_populates="tables")
    user = relationship("User", back_populates="tables")

    purchases = relationship(
        "TablePurchase",
        back_populates="table",
        cascade="all, delete-orphan",
    )

    reservations = relationship(
        "Reservation",
        back_populates="table",
        cascade="all, delete-orphan",
    )

    group = relationship(
        "TableGroup",
        foreign_keys=[group_id],
        back_populates="tables",
    )

    mastered_group = relationship(
        "TableGroup",
        foreign_keys="TableGroup.master_table_id",
        back_populates="master_table",
        uselist=False,
    )


class TableGroup(Base):
    __tablename__ = "table_groups"

    id = Column(String, primary_key=True, index=True)

    master_table_id = Column(String, ForeignKey("table_master.id"), nullable=False)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)

    master_table = relationship(
        "TableMaster",
        foreign_keys=[master_table_id],
        back_populates="mastered_group",
    )

    tables = relationship(
        "TableMaster",
        foreign_keys="TableMaster.group_id",
        back_populates="group",
    )

    company = relationship("Company", back_populates="table_groups")


class ItemCategory(Base):
    __tablename__ = "item_categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category_name = Column(String, unique=True, index=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    items = relationship("Item", back_populates="category")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    item_name = Column(String, nullable=False)
    item_price = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("item_categories.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    company = relationship("Company", back_populates="items")
    category = relationship("ItemCategory", back_populates="items")

    table_purchases = relationship("TablePurchase", back_populates="item")
    reservation_purchases = relationship("ReservationPurchase", back_populates="item")


class TablePurchase(Base):
    __tablename__ = "table_purchases"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    table_id = Column(String, ForeignKey("table_master.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)

    item_name = Column(String, nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Integer, default=0, nullable=False)
    total_price = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    table = relationship("TableMaster", back_populates="purchases")
    item = relationship("Item", back_populates="table_purchases")
    
class TablePurchaseLog(Base):
    __tablename__ = "table_purchases_log"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    table_id = Column(String, ForeignKey("table_master.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)

    item_name = Column(String, nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    user_name = Column(String, nullable=True)
    unit_price = Column(Integer, default=0, nullable=False)
    total_price = Column(Integer, default=0, nullable=False)

      

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    table_id = Column(String, ForeignKey("table_master.id"), nullable=False)

    reservation_time = Column(DateTime(timezone=True), nullable=False)

    customer_name = Column(String, default="", nullable=False)
    customer_phone = Column(String, default="", nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    table = relationship("TableMaster", back_populates="reservations")

    reservation_purchases = relationship(
        "ReservationPurchase",
        back_populates="reservation",
        cascade="all, delete-orphan",
    )


class ReservationPurchase(Base):
    __tablename__ = "reservation_purchases"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    reservation_id = Column(Integer, ForeignKey("reservations.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)

    item_name = Column(String, nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Integer, default=0, nullable=False)
    total_price = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    reservation = relationship("Reservation", back_populates="reservation_purchases")
    item = relationship("Item", back_populates="reservation_purchases")


class TableHistory(Base):
    __tablename__ = "table_histories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    table_id = Column(String, nullable=False)
    tablename = Column(String, nullable=False)
    section = Column(String, nullable=False)

    customer_name = Column(String, default="", nullable=False)
    customer_phone = Column(String, default="", nullable=False)
    persons = Column(Integer, default=0, nullable=False)
    remark = Column(Text, default="", nullable=False)

    user_id = Column(String, default="", nullable=False)
    user_name = Column(String, default="", nullable=False)
    company_id = Column(String, nullable=False)

    registered_at = Column(DateTime(timezone=True), nullable=True)
    out_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    table_history_purchases = relationship(
        "TableHistoryPurchase",
        back_populates="history",
        cascade="all, delete-orphan",
    )


class TableHistoryPurchase(Base):
    __tablename__ = "table_history_purchases"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    history_id = Column(Integer, ForeignKey("table_histories.id"), nullable=False)

    item_id = Column(Integer, nullable=False)
    item_name = Column(String, nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Integer, default=0, nullable=False)
    total_price = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    history = relationship("TableHistory", back_populates="table_history_purchases")
