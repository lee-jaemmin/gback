from sqlalchemy.orm import Session
from models import ( 
            Company, User, TableMaster, ItemCategory, Item, TablePurchase, Reservation, ReservationPurchase, 
            TableHistory, TableHistoryPurchase, TablePurchaseLog,
        )
from schemas import (
            CompanyCreate, CompanyUpdate, UserCreate, UserUpdate, TableCreate, TableUpdate, ItemCategoryCreate,
            ItemCategoryUpdate,ItemCreate, ItemUpdate, TablePurchaseCreate, TablePurchaseUpdate,ReservationCreate,
            ReservationUpdate, ReservationPurchaseCreate, ReservationPurchaseUpdate, TablePurchaseLogCreate, TablePurchaseLogUpdate,
        )
from typing import Optional
from datetime import datetime, UTC
import random
import uuid

def recalculate_table_total_price(db: Session, table_id: str):
    db_table = get_table(db, table_id)

    if db_table is None:
        return None

    purchases = get_purchases_by_table(db, table_id)

    db_table.total_price = sum(purchase.total_price for purchase in purchases)

    return db_table

def recalculate_res_table_total_price(db: Session, table_id: str):
    db_table = get_table(db, table_id)

    if db_table is None:
        return None

    purchases = get_res_purchases_by_table(db, table_id)

    db_table.total_price = sum(purchase.total_price for purchase in purchases)

    return db_table

# ========================
# Company
# ========================
def create_company(db: Session, company: CompanyCreate):
    invite_code = generate_invitation_code(db)

    db_company = Company(
        id=str(uuid.uuid4()),
        name=company.name,
        region=company.region,
        invite_code=invite_code,
    )

    db.add(db_company)
    db.commit()
    db.refresh(db_company) # 여기서 created_at 등 자동 정보 생성

    return db_company

def get_company(db: Session, company_id: str):
    return db.query(Company).filter(Company.id == company_id).first()

def get_companies(db: Session): # 전체 회사 반환
    return db.query(Company).all()

def update_company(db: Session, company_id: str, company_update: CompanyUpdate):
    db_company = get_company(db, company_id)

    if db_company is None: # 해당 객체 없으면
        return None

    if company_update.name is not None:
        db_company.name = company_update.name

    if company_update.region is not None:
        db_company.region = company_update.region

    if company_update.sections is not None:
        db_company.sections = company_update.sections

    db.commit()
    db.refresh(db_company)

    return db_company

def get_company_by_invite_code(db: Session, invite_code: str):
    return db.query(Company).filter(Company.invite_code == invite_code).first()

def generate_invitation_code(db: Session):
    invite_code_chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

    for _ in range(20):
        code = "".join(random.choice(invite_code_chars) for _ in range(6))

        existing_company = get_company_by_invite_code(db, code)
        if existing_company is None:
            return code

    raise Exception("Failed to generate invitation code")

def regenerate_invite_code(db: Session, company_id: str):
    db_company = get_company(db, company_id)
    if db_company is None:
        return None

    db_company.invite_code = generate_invitation_code(db)
    db.commit()
    db.refresh(db_company)
    return db_company


    

# ========================
# User
# ========================
def create_user(db: Session, user: UserCreate):
    db_user = User(
        id=user.id,
        company_id=user.company_id,
        username=user.username,
        email=user.email,
        role=user.role,
        fcmtoken=user.fcmtoken,
        tablecardfields=user.tablecardfields,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

def get_user(db: Session, user_id: str):
    return db.query(User).filter(User.id == user_id).first()

def get_users_by_company(db: Session, company_id: str):
    return db.query(User).filter(User.company_id == company_id).all()

def update_user(db: Session, user_id:str, user_update: UserUpdate):
    # 만약 수정 사항이 있으면 main.py의 주석 달린 줄로 인해서 이미 UserUpdate형태로 데이터가 들어온다.
    # main.py에서 user_update: UserUpdate로 선언했기 때문에
    # 여기에는 이미 검증이 끝난 UserUpdate 객체가 들어온다.
    db_user = get_user(db, user_id)

    if db_user is None:
        return None
    
    if user_update.username is not None: # 변경 사항이 있으면
        db_user.username = user_update.username
    if user_update.email is not None:
        db_user.email = user_update.email
    if user_update.role is not None:
        db_user.role = user_update.role
    if user_update.fcmtoken is not None:
        db_user.fcmtoken = user_update.fcmtoken
    if user_update.tablecardfields is not None:
        db_user.tablecardfields = user_update.tablecardfields

    db.commit()
    db.refresh(db_user)

    return db_user

# ========================
# Table
# ========================
def create_table(db: Session, table: TableCreate):
    db_table = TableMaster(
        id = str(uuid.uuid4()),
        tablename = table.tablename,
        section = table.section,
        status = table.status,
        customer = table.customer,
        phonenumber = table.phonenumber,
        persons= table.persons,
        remark = table.remark,
        total_price = table.total_price,
        company_id = table.company_id,
        user_id = table.user_id,
        user_name = table.user_name,
        group_id = table.group_id,
    )

    db.add(db_table)
    db.commit()
    db.refresh(db_table)

    return db_table

def get_table(db: Session, table_id: str):
    return db.query(TableMaster).filter(TableMaster.id == table_id).first()

def get_tables_by_company(db: Session, company_id: str):
    return db.query(TableMaster).filter(TableMaster.company_id == company_id).all()

def get_tables_by_company_and_section(
    db: Session,
    company_id: str,
    section: str,
):
    return (
        db.query(TableMaster)
        .filter(
            TableMaster.company_id == company_id,
            TableMaster.section == section,
        )
        .all()
    )

def get_tables_by_group(db: Session, group_id: str):
    return db.query(TableMaster).filter(TableMaster.group_id == group_id).all()

def update_table(db: Session, table_update: TableUpdate, table_id: str):
    db_table = get_table(db, table_id)

    if db_table is None:
        return None
    if table_update.tablename is not None:
        db_table.tablename = table_update.tablename

    if table_update.section is not None:
        db_table.section = table_update.section

    if table_update.status is not None:
        db_table.status = table_update.status # 등록 밖에 없음.
        # if db_table.status == 'inuse':
        #     db_table.registered_at = datetime.now(UTC)

    if table_update.customer is not None:
        db_table.customer = table_update.customer

    if table_update.phonenumber is not None:
        db_table.phonenumber = table_update.phonenumber

    if table_update.persons is not None:
        db_table.persons = table_update.persons

    if table_update.remark is not None:
        db_table.remark = table_update.remark

    if table_update.total_price is not None:
        db_table.total_price = table_update.total_price

    if table_update.registered_at is not None:
        db_table.registered_at = table_update.registered_at

    if table_update.user_id is not None:
        db_table.user_id = table_update.user_id

    if table_update.user_name is not None:
        db_table.user_name = table_update.user_name

    if table_update.group_id is not None:
        db_table.group_id = table_update.group_id

    if table_update.ismaster is not None:
        db_table.ismaster = table_update.ismaster

    if table_update.mastertable_id is not None:
        db_table.mastertable_id = table_update.mastertable_id

    if table_update.timer_started_at is not None:
        db_table.timer_started_at = table_update.timer_started_at    

    db.commit()
    db.refresh(db_table)

    return db_table

def delete_table(
        db: Session,
        table_id: str,
):
    db_table = get_table(db, table_id)
    if db_table is None:
        return False
    
    db.delete(db_table)
    db.commit()
    return True

# ========================
# ItemCategory
# ========================
def create_item_category(db: Session, category: ItemCategoryCreate):
    db_category = ItemCategory (
        category_name = category.category_name,
        sort_order = category.sort_order,
        is_active = category.is_active,
    )

    db.add(db_category)
    db.commit()
    db.refresh(db_category)

    return db_category

def get_item_category(db: Session, category_id: int):
    return db.query(ItemCategory).filter(ItemCategory.id == category_id).first()

def get_item_categories(db: Session):
    return db.query(ItemCategory).all()

def update_item_category(db: Session, category_id: int, category_update: ItemCategoryUpdate):
    db_category = get_item_category(db, category_id)

    if db_category is None:
        return None
    if category_update.category_name is not None:
        db_category.category_name = category_update.category_name

    if category_update.sort_order is not None:
        db_category.sort_order = category_update.sort_order

    if category_update.is_active is not None:
        db_category.is_active = category_update.is_active

    db.commit()
    db.refresh(db_category)
    return db_category

# ========================
# Item
# ========================
def create_item(
        db: Session,
        item: ItemCreate,
):
    db_item = Item (
        item_name = item.item_name,
        item_price = item.item_price,
        is_active = item.is_active,
        company_id = item.company_id,
        category_id = item.category_id,
    )

    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_item(
        item_id: int,
        db: Session,
):
    return db.query(Item).filter(Item.id == item_id).first()

def get_items_by_company(
        company_id: str,
        db: Session,
):
    return db.query(Item).filter(Item.company_id == company_id).all()

def get_items_by_category(db: Session, category_id: int, company_region: Optional[str] = None):
    query = db.query(Item).filter(Item.category_id == category_id)
    if company_region is not None:   
        query = (
            query.join(Company).filter(Company.region == company_region)
        )
    return query.all()
## Item에는 region이 없고 Company에 있음. 그래서 join이 필요
## 조인 할 수도 있고, 안 할 수 있을 때


def get_items_by_company_and_category(
    company_id: str,
    category_id: int,
    db: Session,
):
    return (
        db.query(Item)
        .filter(
            Item.company_id == company_id,
            Item.category_id == category_id,
        )
        .all()
    )

def update_item(
        item_id: int,
        item_update: ItemUpdate,
        db: Session,
):
    db_item = get_item(item_id, db)

    if db_item is None:
        return None
    if item_update.item_name is not None:
        db_item.item_name = item_update.item_name
    if item_update.item_price is not None:
        db_item.item_price = item_update.item_price
    if item_update.is_active is not None:
        db_item.is_active = item_update.is_active

    db.commit()
    db.refresh(db_item)
    return db_item

# ========================
# TablePurchase 여기서부터는 db: Session 맨 앞에.
# ========================
def create_purchase(
    db: Session,
    purchase: TablePurchaseCreate
):
    db_item = get_item(purchase.item_id, db) # 이번에 주문한 아이템.

    existing_purchase = (
        db.query(TablePurchase).filter( # 주문한 거 또 주문하는지 확인.
            TablePurchase.table_id == purchase.table_id,
            TablePurchase.item_id == purchase.item_id).first()
        )
    
    if existing_purchase is not None:
        existing_purchase.quantity += purchase.quantity
        # 바뀐 품목당 가격 재계산
        existing_purchase.total_price = existing_purchase.quantity * existing_purchase.unit_price
        recalculate_table_total_price(db, existing_purchase.table_id)
        db.commit()
        db.refresh(existing_purchase)
        return existing_purchase

    unit_price = db_item.item_price
    total_price = unit_price * purchase.quantity
    item_name = db_item.item_name

    db_purchase = TablePurchase(
        table_id = purchase.table_id,
        item_id = purchase.item_id,
        quantity = purchase.quantity,
        unit_price = unit_price,
        total_price = total_price,
        item_name = item_name
    )

    db.add(db_purchase)
    db.flush()
    recalculate_table_total_price(db, purchase.table_id)
    db.commit()
    db.refresh(db_purchase)
    return db_purchase

def get_purchase(
        db: Session,
        purchase_id: int,
):
    return db.query(TablePurchase).filter(TablePurchase.id == purchase_id).first()

def get_purchases_by_table(
        db: Session,
        table_id: str,
):
    return db.query(TablePurchase).filter(TablePurchase.table_id == table_id).all()

def update_purchase(
        db: Session,
        purchase_id: int,
        purchase_update: TablePurchaseUpdate
):
    db_purchase = get_purchase(db, purchase_id)
    if db_purchase is None:
        return None
    if purchase_update.item_name is not None:
        db_purchase.item_name = purchase_update.item_name
    if purchase_update.quantity is not None:
        db_purchase.quantity = purchase_update.quantity
    if purchase_update.table_id is not None:
        db_purchase.table_id = purchase_update.table_id
    if purchase_update.unit_price is not None:
        db_purchase.unit_price = purchase_update.unit_price
    # 품목별 총 가격 다시 계산
    db_purchase.total_price = db_purchase.unit_price * db_purchase.quantity
    
    recalculate_table_total_price(db, db_purchase.table_id)
    
    db.commit()
    db.refresh(db_purchase)
    return db_purchase

# ========================
# TablePurchaseLog
# ========================

def create_purchase_log(
        db: Session,
        log: TablePurchaseLogCreate
) :
    db_item = get_item(log.item_id, db)
    if db_item is None:
        return None
    db_user = get_user(db, log.user_id)
    if db_user is None:
        return None

    db_log = TablePurchaseLog (
        table_id = log.table_id,
        item_id = db_item.id,
        item_name = db_item.item_name,
        quantity = log.quantity,
        unit_price = db_item.item_price,
        total_price = db_item.item_price * log.quantity,
        user_id = log.user_id,
        user_name = db_user.username,
        batch_id = log.batch_id,
    )

    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_purchase_logs(
        db: Session,
        table_id: str
) :
    return db.query(TablePurchaseLog).filter(TablePurchaseLog.table_id == table_id).all()

# def update_log(
#         db: Session,
#         log_id :int,
#         log_update: TablePurchaseLogUpdate,
# ):
#     db_log = get_purchase_log(db, log_id)

#     if log_update.item_id is not None:
#         db_log.item_id = log_update.item_id
#     if log_update.item_name is not None:
#         db_log.item_name = log_update.item_name
#     if log_update.quantity is not None:
#         db_log.quantity = log_update.quantity
#     if log_update.unit_price is not None:
#         db_log.unit_price = log_update.unit_price
#     if log_update.total_price is not None:
#         db_log.total_price = log_update.total_price
    
#     db.commit()
#     db.refresh(db_log)
#     return db_log

# ========================
# Reservation
# ========================
def create_reservation(
        db: Session,
        reservation: ReservationCreate
): 
    db_reservation = Reservation (
        reservation_time = reservation.reservation_time,
        customer_name = reservation.customer_name,
        customer_phone = reservation.customer_phone,
        table_id = reservation.table_id,
    )

    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation

def get_reservation(
        db: Session,
        reservation_id: int,
):
    return db.query(Reservation).filter(Reservation.id == reservation_id).first()

def get_reservations_by_table (
        db: Session,
        table_id: str,
):
    return db.query(Reservation).filter(Reservation.table_id == table_id).all()

def update_reservation(
        db: Session,
        reservation_update: ReservationUpdate,
        reservation_id: int,
):
    db_reservation = get_reservation(db, reservation_id)
    
    if db_reservation is None:
        return None
    
    if reservation_update.reservation_time is not None:
        db_reservation.reservation_time = reservation_update.reservation_time
    if reservation_update.customer_name is not None:

        db_reservation.customer_name = reservation_update.customer_name
    if reservation_update.customer_phone is not None:
        db_reservation.customer_phone = reservation_update.customer_phone
    
    db.commit()
    db.refresh(db_reservation)
    return db_reservation

def delete_reservation(
        db: Session,
        reservation_id: int,
):
    db_reservation = get_reservation(db, reservation_id)
    if db_reservation is None:
        return False
    
    db.delete(db_reservation)
    db.commit()
    return True # 방금 삭제된 객체 반환

# ========================
# ReservationPurchase: table_id 접근 위해서는 Reservation을 거쳐야 함.
# ========================
def create_res_purchase(
        db: Session,
        res_purchase: ReservationPurchaseCreate
):
    db_reservation = get_reservation(db, res_purchase.reservation_id)
    if db_reservation is None:
        return None
    
    db_item = get_item(res_purchase.item_id, db)
    if db_item is None:
        return None
    item_name = db_item.item_name
    unit_price = db_item.item_price
    table_id = db_reservation.table_id
    
    db_res_purchase = ReservationPurchase(
        reservation_id = res_purchase.reservation_id,
        item_id = res_purchase.item_id,
        quantity = res_purchase.quantity,
        item_name = item_name,
        unit_price = unit_price,
        total_price = unit_price * res_purchase.quantity,
    )
    db.add(db_res_purchase)
    db.flush()

    recalculate_res_table_total_price(db, table_id)

    db.commit()
    db.refresh(db_res_purchase)
    return db_res_purchase

def get_res_purchase (
        db: Session,
        res_purchase_id: int,
):
    return db.query(ReservationPurchase).filter(ReservationPurchase.id == res_purchase_id).first()

def get_res_purchases_by_table (
        db: Session,
        table_id: str,
):
    return db.query(ReservationPurchase).join(Reservation).filter(Reservation.table_id == table_id).all()
    ## 무조건 조인할 때는 이런 식으로

def update_res_purchase(
        db: Session,
        res_purchase_id: int,
        res_purchase_update: ReservationPurchaseUpdate
):
    db_res_purchase = get_res_purchase(db, res_purchase_id)
    if db_res_purchase is None:
        return None
    
    if res_purchase_update.item_id is not None:
        new_item = get_item(res_purchase_update.item_id, db)
        if new_item is None:
            return None
        db_res_purchase.item_id = new_item.id
        db_res_purchase.item_name = new_item.item_name
        db_res_purchase.unit_price = new_item.item_price

    if res_purchase_update.quantity is not None:
        db_res_purchase.quantity = res_purchase_update.quantity
    
    # 품목별 총 가격 다시 계산
    db_res_purchase.total_price = db_res_purchase.unit_price * db_res_purchase.quantity
    
    db_reservation = get_reservation(db, db_res_purchase.reservation_id)
    table_id = db_reservation.table_id
    ## Relation 이용하면
    ## table_id = db_res_purchase.reservation.table_id
    ## 이렇게 됨.

    recalculate_res_table_total_price(db, table_id)
    
    db.commit()
    db.refresh(db_res_purchase)
    return db_res_purchase

def delete_res_purchase(
        db: Session,
        res_purchase_id: int,
):
    db_res_purchase = get_res_purchase(db, res_purchase_id)
    if db_res_purchase is None:
        return None
    
    db_reservation = get_reservation(db, db_res_purchase.reservation_id)
    table_id = db_reservation.table_id if db_reservation is not None else None

    db.delete(db_res_purchase)
    db.flush()
    if table_id is not None:
        recalculate_res_table_total_price(db, table_id)
    else:
        return False
    db.commit()
    return True

def reservation_check_in(
        db: Session,
        reservation_id: int
):
    db_reservation = get_reservation(db, reservation_id) # 유효성 체크는 메인에서
    db_res_purchases = db.query(ReservationPurchase).filter(ReservationPurchase.reservation_id == reservation_id).all()
    # 없으면 [] -> 아래의 For문은 돌지 않는다.

    table_id = db_reservation.table_id # String
    db_table = get_table(db, table_id) # Table 객체
    if db_table is None:
        return None
    if db_table.status != "available": # 빈 테이블인지 체크
        return "TABLE_NOT_AVAILABLE"

    # TableMaster 변경: 1회
    db_table.customer = db_reservation.customer_name
    db_table.phonenumber = db_reservation.customer_phone
    db_table.status = "inuse"
    db_table.registered_at = datetime.now(UTC)
    
    # res_purchase 개수 (즉 품목 개수) 만큼 tablepurchase생성
    for purchase in db_res_purchases:
        db_purchase = TablePurchase(
            table_id = table_id,
            item_id = purchase.item_id,
            item_name = purchase.item_name,
            quantity = purchase.quantity,
            unit_price = purchase.unit_price,
            total_price = purchase.total_price,
            created_at = datetime.now(UTC)
        )
        db.add(db_purchase)
    db.flush()
    recalculate_table_total_price(db, table_id)
    db.commit()
    db.refresh(db_table)
    return db_table


# ========================
# TableOut
# ========================
def table_out(
        db: Session,
        table_id: str,     
): 
    db_table = get_table(db, table_id) # 해당 테이블 가져옴
    if db_table is None:
        return None
    if db_table.status != "inuse":
        return "TABLE_NOT_USING"
    
    db_purchases = get_purchases_by_table(db, table_id)
    # 해당 테이블의 구매 리스트 ex. 호세3, 모엣1, 잭다니엘2 ... 
    # 아웃 시킬 때 db에서 내역을 날린다면, 현재 사용 중인 기록만 남게 됨.    
    
    db_history = TableHistory (
        table_id = table_id,
        tablename = db_table.tablename,
        section = db_table.section,
        customer_name = db_table.customer,
        customer_phone = db_table.phonenumber,
        persons = db_table.persons,
        remark = db_table.remark,
        user_id = db_table.user_id,
        user_name = db_table.user_name,
        company_id = db_table.company_id,
        registered_at = db_table.registered_at,
        out_at = datetime.now(UTC)
    )

    db.add(db_history)
    db.flush()

    for purchase in db_purchases:
        db_history_purchase = TableHistoryPurchase (
            history_id = db_history.id,
            item_id = purchase.item_id,
            item_name = purchase.item_name,
            quantity = purchase.quantity,
            unit_price = purchase.unit_price,
            total_price = purchase.total_price,
            created_at = datetime.now(UTC)
        )
        db.add(db_history_purchase)

    # 이제 구매 내역 지우기
    for purchase in db_purchases:
        db.delete(purchase)

    # 만약 아웃된 애가 마스터라면
    ## 테이블 그룹 crud를 만들기 ## 

    db_log = get_purchase_logs(db, table_id)
    for log in db_log:
        db.delete(log)

    # 테이블 초기화
    db_table.status = 'available'
    db_table.customer = ""
    db_table.phonenumber = ""
    db_table.persons = 0
    db_table.remark = ""
    db_table.total_price = 0
    db_table.registered_at = None
    db_table.ismaster = False
    db_table.mastertable_id = None 
    db_table.group_id = None 
    db_table.user_id = None 
    db_table.user_name = None
    db_table.timer_started_at = None

    db.commit()
    return db_history

def get_history(
        db: Session,
        history_id: int,
):
    return db.query(TableHistory).filter(TableHistory.id == history_id).first()

def get_histories_by_table(
        db: Session,
        table_id: str,
):
    return db.query(TableHistory).filter(TableHistory.table_id == table_id).all()
    
def get_history_purchase(
        db: Session,
        history_purchase_id: int,
):
    return db.query(TableHistoryPurchase).filter(TableHistoryPurchase.id == history_purchase_id).first()

def get_history_purchases_by_table (
        db: Session,
        table_id: str,
):
    return db.query(TableHistoryPurchase).join(TableHistory).filter(TableHistory.table_id == table_id).all()
    ## 만약 Model.py에 relationship이 없으면
    ## .join(TableHistory, TableHistoryPurchase.history_id == TableHistory.id)
    ## 이렇게 써야함.

def get_history_purchases_by_history(
        db: Session,
        history_id: int
):
    return db.query(TableHistoryPurchase).filter(TableHistoryPurchase.history_id == history_id).all()
