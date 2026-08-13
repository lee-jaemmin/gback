from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

# API 명세서
# 요청 데이터는 ~~해야 한다. ex. id는 str이어야한다 등
# 요청 데이터 -> python 객체

# =========================
# COMPANY
# =========================


class CompanyBase(BaseModel):
    name: str
    address: str
    region: str = ""


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    region: Optional[str] = None
    address: Optional[str] = None
    sections: Optional[list[str]] = None


class CompanyResponse(CompanyBase):
    id: str
    created_at: datetime
    sections: list[str]
    updated_at: datetime
    invite_code: Optional[str] = None

    class Config:
        from_attributes = True


# =========================
# USER
# =========================


class UserBase(BaseModel):
    username: str
    email: str
    role: str = "user"
    fcmtoken: Optional[str] = None
    tablecardfields: List[str] = Field(default_factory=lambda: ["purchases", "persons"])
    is_push_on: bool = True


class UserCreate(UserBase):
    # User.id is the Firebase Auth UID, not a server-generated UUID.
    id: str
    company_id: Optional[str] = None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    fcmtoken: Optional[str] = None
    tablecardfields: Optional[List[str]] = None
    company_id: Optional[str] = None
    is_push_on: Optional[bool] = None


class UserResponse(UserBase):
    id: str
    company_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# =========================
# TABLEMASTER
# =========================


class TableBase(BaseModel):
    tablename: str
    section: str
    status: str = "available"

    customer: str = ""
    phonenumber: str = ""
    persons: int = 0
    remark: str = ""

    position_x: float = 0
    position_y: float = 0
    width: int = 0
    height: int = 0

    total_price: int = 0
    registered_at: Optional[datetime] = None
    timer_started_at: Optional[datetime] = None
    timer_end_at: Optional[datetime] = None
    timer_alert_sent_at: Optional[datetime] = None
    reserved_at: Optional[datetime] = None

    bid_end_at: Optional[datetime] = None
    bid_available: Optional[bool] = False
    least_bid_price: int = 0

    is_reserved: bool = False
    purchase_summary: Optional[list[str]] = None


class TableCreate(TableBase):
    company_id: str
    user_id: Optional[str] = None
    user_name: Optional[str] = None


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

    position_x: Optional[float] = None
    position_y: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None

    user_id: Optional[str] = None
    user_name: Optional[str] = None
    timer_started_at: Optional[datetime] = None
    timer_end_at: Optional[datetime] = None
    timer_alert_sent_at: Optional[datetime] = None
    bid_end_at: Optional[datetime] = None
    bid_available: Optional[bool] = None
    least_bid_price: Optional[int] = 0
    is_reserved: Optional[bool] = None
    company_id: Optional[str] = None
    purchase_summary: Optional[list[str]] = None


class TableResponse(TableBase):
    id: str
    company_id: str
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =========================
# BIDLIST
# =========================


class BidListBase(BaseModel):
    company_name: str
    user_name: str
    user_phonenumber: str
    bid_price: int

    company_id: str
    table_id: str
    user_id: str


class BidListCreate(BidListBase):
    pass


class BidListUpdate(BaseModel):
    company_name: Optional[str] = None
    user_name: Optional[str] = None
    user_phonenumber: Optional[str] = None
    bid_price: Optional[int] = None

    company_id: Optional[str] = None
    table_id: Optional[str] = None
    user_id: Optional[str] = None


class BidListResponse(BidListBase):
    id: int

    class Config:
        from_attributes = True


# =========================
# ITEMCATEGORY
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
# ITEM
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
# TABLEPURCHASE
# 현재 테이블에서 실제 주문한 상품
# =========================


class TablePurchaseCreate(BaseModel):
    table_id: str
    item_id: int
    quantity: int = 1


class TablePurchaseUpdate(BaseModel):
    table_id: Optional[str] = None
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
# TABLEPURCHASELOG
# 현재 테이블에서 실제 주문한 상품
# =========================


class TablePurchaseLogCreate(BaseModel):
    table_id: str
    item_id: int
    quantity: int = 1
    user_id: str
    batch_id: str


class TablePurchaseLogUpdate(BaseModel):
    table_id: Optional[str] = None
    item_id: int
    item_name: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[int] = None
    total_price: Optional[int] = None


class TablePurchaseLogResponse(BaseModel):
    id: int
    table_id: str
    item_id: int
    item_name: str
    quantity: int
    unit_price: int
    total_price: int

    user_id: str
    batch_id: str

    created_at: datetime

    class Config:
        from_attributes = True


# =========================
# LOGHISTORY
# =========================


class LogHistoryCreate(BaseModel):
    table_id: str
    item_id: int
    quantity: int = 1
    user_id: str
    batch_id: str
    history_id: int


class LogHistoryResponse(BaseModel):
    id: int
    table_id: str
    item_id: int
    item_name: str
    quantity: int
    unit_price: int
    total_price: int

    user_id: str
    batch_id: str

    created_at: datetime

    class Config:
        from_attributes = True


# =========================
# RESERVATION
# =========================


class ReservationBase(BaseModel):
    reservation_time: Optional[datetime]
    customer_name: str
    customer_phone: str = ""
    bid_price: Optional[int] = 0


class ReservationCreate(ReservationBase):
    table_id: str


class ReservationUpdate(BaseModel):
    reservation_time: Optional[datetime] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    bid_price: Optional[int] = None


class ReservationResponse(ReservationBase):
    id: int
    table_id: str

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =========================
# RESERVATIONPURCHASE
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
# RESERVATIONINPUT
# =========================


class ReservationInputBase(BaseModel):
    item_id: int = 0
    quantity: int = 0


class ReservationInputCreate(ReservationInputBase):
    reservation_time: datetime
    customer_name: str
    customer_phone: str
    bid_price: Optional[int]
    purchases: list[ReservationInputBase] = []


# =========================
# TABLEHISTORY
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
    user_name: str = ""
    company_id: str

    registered_at: Optional[datetime] = None
    out_at: datetime
    business_date: Optional[date] = None
    closed_reason: str = "manual_out"
    re_registered_at: Optional[datetime] = None
    re_registered_table_id: Optional[str] = None
    purchase_summary: Optional[list[str]] = None


class TableHistoryCreate(TableHistoryBase):
    pass


class TableHistoryResponse(TableHistoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# =========================
# TABLEHISTORYPURCHASE
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


# =========================
# NOTIFICATIONS
# =========================
class NotificationCreate(BaseModel):
    company_id: str
    title: str
    body: str
    type: str


class NotificationResponse(BaseModel):
    id: int
    company_id: str
    title: str
    body: str
    type: str
    created_at: datetime

    class Config:
        from_attributes = True


# =========================
# SETMENU
# =========================
class SetMenuBase(BaseModel):
    company_id: str
    set_name: str
    set_price: int
    is_active: bool


class SetMenuCreate(SetMenuBase):
    pass


class SetMenuItemInput(BaseModel):
    # 세트 메뉴 아이템 수정 시 줄 스키마
    item_id: int
    quantity: int


class SetMenuUpdate(BaseModel):
    set_name: Optional[str] = None
    set_price: Optional[int] = None
    is_active: Optional[bool] = None
    items: Optional[list[SetMenuItemInput]] = None


class SetMenuResponse(SetMenuBase):
    id: int

    class Config:
        from_attributes = True


class SetMenuCache(BaseModel):
    id: int
    company_id: str
    set_name: str
    set_price: int
    is_active: bool

    class Config:
        from_attributes = True


# =========================
# SETMENUITEMS
# =========================
class SetMenuItemBase(BaseModel):
    set_menu_id: int
    item_id: int
    quantity: int


class SetMenuItemCreate(SetMenuItemBase):
    items: list[SetMenuItemInput]
    # model에는 없지만 구성품을 보내줘야 하므로 필요함.


class SetMenuItemUpdate(BaseModel):
    item_id: Optional[int] = None
    quantity: Optional[int] = None


class SetMenuItemResponse(SetMenuItemBase):
    id: int

    class Config:
        from_attributes = True


class SetMenuItemCache(BaseModel):
    id: int
    set_menu_id: int
    item_id: int
    quantity: int

    class Config:
        from_attributes = True


# =========================
# MENU CACHE
# Items가 있는데도 스키마를 만드는 이유
# 1. API 형식 고정을 통한 안정성 및 디버깅 강화
# 2. 불필요한 필드를 응답하지 않을 수 있음. (created_at 등)
# =========================
class ItemCache(BaseModel):
    id: int
    item_name: str
    item_price: int
    is_active: bool
    company_id: str
    category_id: int

    class Config:
        from_attributes = True


class CategoryCache(BaseModel):
    id: int
    category_name: str
    sort_order: int
    is_active: bool

    class Config:
        from_attributes = True


class MenuCacheResponse(BaseModel):
    company_id: str
    version: datetime
    categories: list[CategoryCache]
    items: list[ItemCache]
    set_menus: list[SetMenuCache]
    set_menu_items: list[SetMenuItemCache]
