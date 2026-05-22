from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# 플러터 앱과 주고받을 테이블 데이터의 기본 형태
# API 명세서
# Base: 여러 스키마서 공통으로 반복되는 필드. 즉, 일반 속성
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
    ismaster: bool = False
    mastertablenumber: Optional[str] = None

# [Create] 새 Row를 만들 때 클라이언트가 반드시/선택적으로 보내야하는 필드
# 식별값/소속값
class TableCreate(TableBase):
    id: str
    company_id: str
    user_id: Optional[str] = None
    group_id: Optional[str] = None

# [Update] 수정 시.
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
    mastertablenumber: Optional[str] = None 

# [Response] 서버가 앱으로 데이터를 보낼 때의 규격
class TableResponse(TableBase):
    id: str
    company_id: str
    user_id: Optional[str] = None
    group_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # SQLAlchemy 모델(models.py)을 Pydantic 규격으로 자동 변환
    class Config:
        from_attributes = True

class CompanyBase(BaseModel):
    name: str
    addr: str

class CompanyCreate(CompanyBase):
    id: str

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    addr: Optional[str] = None
    id: Optional[str] = None

class CompanyResponse(CompanyBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    username: str
    email: str
    role: str = 'user'
    fcmtoken: str
    tablecardfields : JSON 

class UserCreate(UserBase):
    id: str
    company_id: str

class UserUpdate(BaseModel):
    id: Optional[str] = None
    company_id: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    fcmtoken: Optional[str] = None
    tablecardfields: Optional[JSON] = None

class UserResponse(UserBase):
    id: str
    company_id: str
    created_at: datetime
    class Config:
        from_attributes = True