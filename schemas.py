from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from typing import List

# 플러터 앱과 주고받을 테이블 데이터의 기본 형태
class TableBase(BaseModel):
    tablename: str
    section: str
    status: Optional[str] = "available"
    customer: Optional[str] = ""
    phonenumber: Optional[str] = ""
    staff: Optional[str] = ""
    bottle: Optional[str] = ""
    persons: Optional[int] = 0
    remark: Optional[str] = ""
    reservation_time: Optional[str] = None

# [Create] 관리자가 새 테이블을 만들 때 앱에서 서버로 보내야 하는 필수 데이터
class TableCreate(TableBase):
    tid: str
    company_id: str

# [Response] 서버가 앱으로 데이터를 보낼 때의 규격
class TableResponse(TableBase):
    tid: str
    company_id: str
    group_id: Optional[str] = None
    is_master: Optional[bool] = False
    created_at: datetime
    updated_at: datetime

    # SQLAlchemy 모델(models.py)을 Pydantic 규격으로 자동 변환
    class Config:
        from_attributes = True

# [Register] 스태프가 손님 앉히고 정보 입력
class TableRegister(BaseModel):
    customer: str
    phonenumber: str
    bottle: str
    persons: int
    remark: str
    staff: str
    status: str = "inuse"
    updated_at: datetime

# [Reserve] 예약
class TabelReservation(BaseModel):
    reservation_time: Optional[str] = None

# [Move] 이동
class TableMode(BaseModel):
    from_tid: str
    to_tid: str

# [Join] 합석
class TableJoin(BaseModel):
    master_tid: str
    slave_tids: List[str]

# [Unjoin] 합석 해제
class TableJoin(BaseModel):
    group_id: str
