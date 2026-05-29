from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# API 명세서


# =========================
# Company
# =========================

class CompanyBase(BaseModel):
    name: str
    region: str


class CompanyCreate(CompanyBase):
    id: str


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    region: Optional[str] = None


class CompanyResponse(CompanyBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =========================
# User
# =========================

class UserBase(BaseModel):
    username: str
    email: str
    role: str = "user"
    fcmtoken: Optional[str] = None
    tablecardfields: List[str] = Field(default_factory=lambda: ["purchases", "persons"])


class UserCreate(UserBase):
    id: str
    company_id: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    fcmtoken: Optional[str] = None
    tablecardfields: Optional[List[str]] = None


class UserResponse(UserBase):
    id: str
    company_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# =========================
# TableMaster
# =========================

class TableBase(BaseModel):
    tablename: str
    section: str
    status: str = "available"

    customer: str = ""
    phonenumber: str = ""
    persons: int = 0
    remark: str = ""

    total_price: int = 0
    registered_at: Optional[datetime] = None
    timer_started_at = Optional[datetime] = None

    ismaster: bool = False
    mastertable_id: Optional[str] = None


class TableCreate(TableBase):
    id: str
    company_id: str
    user_id: Optional[str] = None
    group_id: Optional[str] = None


class TableUpdate(BaseModel):
    tablename: Optional[str] = None
    section: Optional[str] = None
    status: Optional[str] = None

    customer: Optional[str] = None
    phonenumber: Optional[str] = None
    persons: Optional[int] = None
    remark: Optional[str] = None

    total_price: Optional[int] = None
    registered_at: Optional[datetime] = None

    user_id: Optional[str] = None
    group_id: Optional[str] = None

    ismaster: Optional[bool] = None
    mastertable_id: Optional[str] = None


class TableResponse(TableBase):
    id: str
    company_id: str
    user_id: Optional[str] = None
    group_id: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =========================
# ItemCategory
# =========================

class ItemCategoryCreate(BaseModel):
    category_name: str
    sort_order: int = 0
    is_active: bool = True


class ItemCategoryUpdate(BaseModel):
    category_name: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class ItemCategoryResponse(BaseModel):
    id: int
    category_name: str
    sort_order: int
    is_active: bool

    class Config:
        from_attributes = True


# =========================
# Item
# =========================

class ItemBase(BaseModel):
    item_name: str
    item_price: int
    category_id: int


class ItemCreate(ItemBase):
    company_id: str
    is_active: bool = True


class ItemUpdate(BaseModel):
    item_name: Optional[str] = None
    item_price: Optional[int] = None
    is_active: Optional[bool] = None
    category_id: Optional[int] = None


class ItemResponse(ItemBase):
    id: int
    company_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =========================
# TablePurchase
# 현재 테이블에서 실제 주문한 상품
# =========================

class TablePurchaseCreate(BaseModel):
    table_id: str
    item_id: int
    quantity: int = 1


class TablePurchaseUpdate(BaseModel):
    item_name: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[int] = None
    total_price: Optional[int] = None


class TablePurchaseResponse(BaseModel):
    id: int
    table_id: str
    item_id: int

    item_name: str
    quantity: int
    unit_price: int
    total_price: int

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =========================
# Reservation
# =========================

class ReservationBase(BaseModel):
    reservation_time: datetime

    customer_name: str
    customer_phone: str = ""


class ReservationCreate(ReservationBase):
    table_id: str


class ReservationUpdate(BaseModel):
    reservation_time: Optional[datetime] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None


class ReservationResponse(ReservationBase):
    id: int
    table_id: str

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =========================
# ReservationPurchase
# =========================

class ReservationPurchaseCreate(BaseModel):
    reservation_id: int
    item_id: int
    quantity: int = 1


class ReservationPurchaseUpdate(BaseModel):
    item_id: Optional[int] = None
    item_name: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[int] = None
    total_price: Optional[int] = None


class ReservationPurchaseResponse(BaseModel):
    id: int
    reservation_id: int
    item_id: int

    item_name: str
    quantity: int
    unit_price: int
    total_price: int

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =========================
# TableGroup
# 합석 그룹
# =========================

class TableGroupCreate(BaseModel):
    id: str
    master_table_id: str
    tables_ids: list[str]
    company_id: str


class TableGroupUpdate(BaseModel):
    master_table_id: Optional[str] = None
    tables_ids: Optional[list[str]] = None
    closed_at: Optional[datetime] = None


class TableGroupResponse(BaseModel):
    id: str
    master_table_id: str
    company_id: str

    created_at: datetime
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =========================
# TableHistory
# 테이블 아웃 당시 스냅샷
# =========================

class TableHistoryBase(BaseModel):
    table_id: str
    tablename: str
    section: str
    customer_name: str = ""
    customer_phone: str = ""
    persons: int = 0
    remark: str = ""

    user_id: str = ""
    company_id: str

    registered_at: Optional[datetime] = None
    out_at: datetime


class TableHistoryCreate(TableHistoryBase):
    pass


class TableHistoryResponse(BaseModel):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# =========================
# TableHistoryPurchase
# =========================
class TableHistoryPurchaseBase(BaseModel):
    history_id: int
    item_id: int
    item_name: str
    quantity: int = 1
    unit_price: int = 0
    total_price: int = 0
class TableHistoryPurchaseCreate(TableHistoryPurchaseBase):
    pass
class TableHistoryPurchaseResponse(TableHistoryPurchaseBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True