from sqlalchemy.orm import Session
from models import ( 
            Company, User, TableMaster, ItemCategory, Item, TablePurchase, Reservation, ReservationPurchase, 
            TableHistory, TableHistoryPurchase, TablePurchaseLog, Notification
        )
from schemas import (
            CompanyCreate, CompanyUpdate, UserCreate, UserUpdate, TableCreate, TableUpdate, ItemCategoryCreate,
            ItemCategoryUpdate,ItemCreate, ItemUpdate, TablePurchaseCreate, TablePurchaseUpdate,ReservationCreate,
            ReservationUpdate, ReservationPurchaseCreate, ReservationPurchaseUpdate, TablePurchaseLogCreate, ReservationInputCreate,
            NotificationCreate, NotificationResponse
        )
from typing import Optional
from datetime import datetime, UTC, date, time, timedelta
from zoneinfo import ZoneInfo
import random
import uuid

KST = ZoneInfo("Asia/Seoul")
BUSINESS_DAY_START = time(18, 0)


def get_business_date(dt: Optional[datetime] = None) -> date:
    target = dt or datetime.now(UTC)
    if target.tzinfo is None:
        target = target.replace(tzinfo=UTC)

    local_dt = target.astimezone(KST)
    local_time = local_dt.time()
    if local_time >= BUSINESS_DAY_START:
        return local_dt.date()
    return local_dt.date() - timedelta(days=1)


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
    db.flush()
    create_tables_for_company(db, db_company.id)
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
    
    update_data = user_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)

    return db_user

def delete_user(db: Session, user_id: str):
    db_user = get_user(db, user_id)
    if db_user is None:
        return False
    db.delete(db_user)
    db.commit()
    return True
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

    update_data = table_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_table, key, value)

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

def create_tables_for_company(
        db: Session,
        company_id: str,
) :
    db_company = get_company(db, company_id) 
    default_tables = []
    sections = db_company.sections
    for section in sections:
        for number in range(10):
            default_tables.append(
                TableMaster(
                    id = str(uuid.uuid4()),
                    tablename = f"{section}-{number+1}",
                    section = section,
                    status = "available",
                    customer = None,
                    phonenumber = None,
                    persons= 0,
                    remark = None,
                    total_price = 0,
                    company_id = company_id,
                    user_id = None,
                    user_name = None,
                    group_id = None,
                )
            )
    db.add_all(default_tables)
    return default_tables

def get_expired_timer_tables(db: Session):
    now = datetime.now(UTC)

    return db.query(TableMaster).filter(
        TableMaster.timer_end_at.isnot(None),
        TableMaster.timer_end_at <= now,
        TableMaster.timer_alert_sent_at.is_(None),
        TableMaster.status == "inuse",
    ).all()

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
    db_table = get_table(db, purchase.table_id)

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
        db_table.purchase_summary = build_purchase_summary(db, db_table.id)
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
    db_table.purchase_summary = build_purchase_summary(db, db_table.id)
    db.commit()
    db.refresh(db_purchase)
    db.refresh(db_table)
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

def delete_purchase(
        db: Session,
        purchase_id: int,
):
    db_purchase = get_purchase(db, purchase_id)
    if db_purchase is None:
        return False
    db.delete(db_purchase)
    db.commit()
    return True 

def build_purchase_summary(db: Session, table_id: str) -> str:
    purchases = db.query(TablePurchase).filter(TablePurchase.table_id == table_id).all()
    return ",".join(
        f"{purchase.item_name} {purchase.quantity}"
        for purchase in purchases
    )

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
    db_table = get_table(db, log.table_id)
    if db_table is None:
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

def get_purchase_log(
        db: Session,
        log_id: int
) :
    return db.query(TablePurchaseLog).filter(TablePurchaseLog.id == log_id).first()

def delete_logs(
        db: Session,
        table_id :str,
):
    db_logs = get_purchase_logs(db, table_id)
    for log in db_logs:
        db.delete(log)
    
    db.commit()
    return True

def delete_log(
        db: Session,
        log_id: int,
):
    db_log = get_purchase_log(db, log_id)
    if db_log is None:
        return False
    db.delete(db_log)
    db.commit()
    return True

def delete_logs_and_purchases(
        db: Session,
        log_id: int,
):
    db_log = get_purchase_log(db, log_id)
    if db_log is None:
        return "Log not found"
    db_item = get_item(db_log.item_id, db)
    if db_item is None:
        return "Item not found"
    db_purchases = get_purchases_by_table(db, db_log.table_id)
    db_table = get_table(db, db_log.table_id)
    if db_table is None:
        return "Table not found"

    flag = False

    for purchase in db_purchases:
        if purchase.item_id == db_log.item_id:
            flag = True
            purchase.quantity = purchase.quantity - db_log.quantity
            if purchase.quantity <= 0:
                db.delete(purchase)
            else:
                purchase.total_price = purchase.unit_price * purchase.quantity
    if flag is False:
        return "Purchase not found"
    
    db.flush()
    remaining_purchases = get_purchases_by_table(db, db_table.id)

    total_price = sum(purchase.total_price for purchase in remaining_purchases)
    db_table.total_price = total_price

    db.delete(db_log)
    db.commit()
    return True
    

def register_purchase(
        db: Session,
        log: TablePurchaseLogCreate
):
    db_item = get_item(log.item_id, db)
    if db_item is None:
        return "ITEM NOT FOUND"
    db_user = get_user(db, log.user_id)
    if db_user is None:
        return "USER NOT FOUND"
    db_table = get_table(db, log.table_id)
    if db_table is None:
        return "TABLE NOT FOUND"

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
    db.flush()

    existing_purchase = (
        db.query(TablePurchase).filter( # 주문한 거 또 주문하는지 확인
            TablePurchase.table_id == log.table_id,
            TablePurchase.item_id == log.item_id).first()
    )

    if existing_purchase is not None:
        existing_purchase.quantity += log.quantity
        # 바뀐 품목당 가격 재계산
        existing_purchase.total_price = existing_purchase.quantity * existing_purchase.unit_price
        recalculate_table_total_price(db, existing_purchase.table_id)
        db_table.purchase_summary = build_purchase_summary(db, db_table.id)
        db.add(existing_purchase)
    else:    
        # 신규면
        unit_price = db_item.item_price
        total_price = unit_price * log.quantity
        item_name = db_item.item_name

        db_purchase = TablePurchase(
            table_id = log.table_id,
            item_id = log.item_id,
            quantity = log.quantity,
            unit_price = unit_price,
            total_price = total_price,
            item_name = item_name
        )
    
        db.add(db_purchase)
        db.flush()
        recalculate_table_total_price(db, db_table.id)
        db_table.purchase_summary = build_purchase_summary(db, db_table.id)
    db.commit()
    return {"message": "register purchase successfully"}
    

# ========================
# Reservation
# ========================
def create_reservation(
        db: Session,
        reservation: ReservationCreate
):  
    db_table = get_table(db, reservation.table_id)
    if db_table is None:
        return None
    db_table.is_reserved = True
    
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
    
    db_table = get_table(db, db_reservation.table_id)
    if db_table is None:
        return False
    
    db_table.is_reserved = False
    
    db.delete(db_reservation)
    db.commit()
    return db_table # 최신화된 테이블 정보 보냄. 그래야 웹소켓에 씀

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
    
def get_res_purchases_by_reservation (
        db: Session,
        reservation_id: int,
):
    return db.query(ReservationPurchase).filter(ReservationPurchase.reservation_id == reservation_id).all()
    

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

def register_reservation(
        db: Session,
        reservation_input: ReservationInputCreate,
        table_id: str,
) : 
    db_table = get_table(db, table_id)
    if db_table is None:
        return "Table not found"
    if db_table.is_reserved is True:
        return "Table already reserved"
    db_table.is_reserved = True
    db_reservation = Reservation(
        table_id = table_id,
        reservation_time = reservation_input.reservation_time,
        customer_name = reservation_input.customer_name,
        customer_phone = reservation_input.customer_phone
    )
    db.add(db_reservation)
    db.flush()

    # 예약 하나에 여러 예약 내역이 가능하므로 id도 for문 안에서
    for purchase in reservation_input.purchases:
        db_item = get_item(purchase.item_id, db)
        if db_item is None:
            db.rollback() # 앞에 해둔 게 있기 때문에 롤백
            return "Item not found"
        now = datetime.now(UTC)    
        db_res_purchase = ReservationPurchase (
            reservation_id = db_reservation.id,
            item_id = purchase.item_id,
            item_name = db_item.item_name,
            unit_price = db_item.item_price,
            quantity = purchase.quantity,       
            total_price = db_item.item_price * purchase.quantity,
            created_at = now     
        )
        db.add(db_res_purchase)

    db.commit()
    db.refresh(db_reservation)
    return db_reservation

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
    db_table.is_reserved = False
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
    db.delete(db_reservation)
    db.flush()
    recalculate_table_total_price(db, table_id)
    db.commit()
    db.refresh(db_table)
    return db_table


# ========================
# TableOut, History
# ========================
def table_out(
        db: Session,
        table_id: str,
        closed_reason: str = "manual_out",
): 
    db_table = get_table(db, table_id) # 해당 테이블 가져옴
    if db_table is None:
        return None
    if db_table.status != "inuse":
        return "TABLE_NOT_USING"
    
    db_purchases = get_purchases_by_table(db, table_id)
    # 해당 테이블의 구매 리스트 ex. 호세3, 모엣1, 잭다니엘2 ... 
    # 아웃 시킬 때 db에서 내역을 날린다면, 현재 사용 중인 기록만 남게 됨.    
    
    out_at = datetime.now(UTC)
    business_date_source = db_table.registered_at or out_at

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
        out_at = out_at,
        business_date = get_business_date(business_date_source),
        closed_reason = closed_reason,
    )

    db.add(db_history)
    db.flush()

    db_notification = Notification (
        company_id = db_table.company_id,
        title = f"테이블 아웃",
        body = f"{db_table.tablename}번 테이블이 아웃 처리 되었습니다.",
        type = "OUT"
    )

    db.add(db_notification)
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
    db_table.purchase_summary = ""
    db_table.registered_at = None
    db_table.ismaster = False
    db_table.mastertable_id = None 
    db_table.group_id = None 
    db_table.user_id = None 
    db_table.user_name = None
    db_table.timer_started_at = None
    db_table.timer_end_at = None
    db_table.timer_alert_sent_at = None
    db_table.purchase_summary = None

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

def get_histories_by_company_and_business_date(
        db: Session,
        company_id: str,
        target_business_date: date,
):
    return (
        db.query(TableHistory)
        .filter(
            TableHistory.company_id == company_id,
            TableHistory.business_date == target_business_date,
        )
        .order_by(TableHistory.out_at.desc())
        .all()
    )
    
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

def reregister_table(
        db: Session,
        history_id: int,
        table_id: str,
) : 
    db_history = get_history(db, history_id)
    if db_history is None:
        return "History not found"
    if db_history.re_registered_at is not None:
        return "History already re-registered"
    
    db_history_purchases = get_history_purchases_by_history(db, history_id)
    if not db_history_purchases:
        return "No historypurchase found"   
    
    db_table = get_table(db, table_id)
    if db_table is None:
        return "Table not found"
    
    if db_table.status == "inuse":
        return "Table already in use"
    
    # 일반 정보 옮기기
    db_table.customer = db_history.customer_name
    db_table.persons = db_history.persons
    db_table.phonenumber = db_history.customer_phone
    db_table.remark = f"{db_history.tablename}번 재등록" if not db_history.remark else f"{db_history.remark}, {db_history.tablename}번 재등록" 
    db_table.status = "inuse"
    db_table.registered_at = db_history.registered_at
    # 구매 정보 옮기기
    for hp in db_history_purchases:
        db_purchase = TablePurchase(
            table_id = db_table.id,
            item_id = hp.item_id,
            item_name = hp.item_name,
            quantity = hp.quantity,
            unit_price = hp.unit_price,
            total_price = hp.quantity * hp.unit_price
        )
        db.add(db_purchase)
    total_price = sum(hp.unit_price * hp.quantity for hp in db_history_purchases)
    db_table.total_price = total_price
    db.flush()
    db_table.purchase_summary = build_purchase_summary(db, db_table.id)
    db_history.re_registered_at = datetime.now(UTC)
    db_history.re_registered_table_id = db_table.id
    db.commit()
    return True

# ========================
# Notification
# ========================
def create_timer_notification (
        db: Session,
        table: TableMaster,
) :
    db_table = get_table(db, table.id)

    db_notification = Notification (
        company_id = db_table.company_id,
        title = f"타이머 만료",
        body = f"{db_table.tablename}번 테이블 타이머가 만료 되었습니다.",
        type = "TIMEOUT"
    )

    db.add(db_notification)
    return db_notification

def get_notification_by_company(
        db: Session,
        company_id: str
):
    return db.query(Notification).filter(Notification.company_id == company_id).order_by(Notification.created_at.desc()).all()


# ========================
# Reset
# ========================

def reset_daily_state(db: Session):
    try:
        # 아직 사용 중인 테이블 아웃 처리(히스토리)
        db_table = db.query(TableMaster).filter(TableMaster.status == "inuse").all()
        for table in db_table:
            try:
                table_out(db, table.id, closed_reason="daily_reset")
            except Exception as e:
                print(f"[Daily reset error]: table_id: {table.id}, e: {e}")

        # 예약 구매 내역 먼저 삭제
        db.query(ReservationPurchase).delete(synchronize_session=False)

        # 예약 삭제
        db.query(Reservation).delete(synchronize_session=False)        

        # 현재 테이블 구매 내역 삭제
        db.query(TablePurchase).delete(synchronize_session=False)

        # 테이블 마스터 초기화
        db.query(TableMaster).update(
            {
                TableMaster.status: "available",
                TableMaster.customer: "",
                TableMaster.phonenumber: "",
                TableMaster.persons: 0,
                TableMaster.remark: "",
                TableMaster.total_price: 0,
                TableMaster.purchase_summary: "",
                TableMaster.registered_at: None,
                TableMaster.user_id: None,
                TableMaster.user_name: None,              
                TableMaster.group_id: None,
                TableMaster.ismaster: False,
                TableMaster.mastertable_id: None,
                TableMaster.is_reserved: False,
                TableMaster.timer_started_at: None,
                TableMaster.timer_end_at: None,
                TableMaster.timer_alert_sent_at: None,
            },
            synchronize_session=False,
        )

        db.commit()
        return True

    except Exception:
        db.rollback()
        raise

# ========================
# Move
# ========================
def moveTable(db: Session, from_table_id: str, to_table_id: str):
    db_from = get_table(db, from_table_id)
    db_to = get_table(db, to_table_id)

    if db_from.status == "available":
        return "FROM TABLE NOT USING"
    if db_to.status == "inuse":
        return "TO TABLE ALREADY IN USE"
    
    from_table_purchases = get_purchases_by_table(db, from_table_id)
    
    for purchase in from_table_purchases:
        purchase.table_id = to_table_id
    
    db_to.customer = db_from.customer
    db_to.persons = db_from.persons
    db_to.phonenumber = db_from.phonenumber
    db_to.purchase_summary = db_from.purchase_summary
    db_to.remark = db_from.remark
    db_to.status = db_from.status
    db_to.registered_at = db_from.registered_at
    db_to.total_price = db_from.total_price
    db_to.timer_started_at = db_from.timer_started_at
    db_to.timer_alert_sent_at = db_from.timer_alert_sent_at
    db_to.timer_end_at = db_from.timer_end_at
    db_to.user_id = db_from.user_id
    db_to.user_name = db_from.user_name

    db.add(db_to)
    db.flush()

    db_from.customer = ""
    db_from.is_reserved = False
    db_from.persons = 0
    db_from.phonenumber = ""
    db_from.purchase_summary = ""
    db_from.remark = ""
    db_from.status = 'available'
    db_from.registered_at = None
    db_from.total_price = 0
    db_from.timer_started_at = None
    db_from.timer_alert_sent_at = None
    db_from.timer_end_at = None
    db_from.user_id = None
    db_from.user_name = None

    db.add(db_from)
    db.flush()

    from_table_logs = get_purchase_logs(db, from_table_id)
    for log in from_table_logs:
        log.table_id = to_table_id
    
    db.commit()
    return db_to


    
