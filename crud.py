from sqlalchemy.orm import Session
from models import (
    Company,
    User,
    TableMaster,
    ItemCategory,
    Item,
    TablePurchase,
    Reservation,
    ReservationPurchase,
    TableHistory,
    TableHistoryPurchase,
    TablePurchaseLog,
    Notification,
    BidList,
    LogHistory,
    SetMenu,
    SetMenuItem,
)
from schemas import (
    CompanyCreate,
    CompanyUpdate,
    UserCreate,
    UserUpdate,
    TableCreate,
    TableUpdate,
    ItemCategoryCreate,
    ItemCategoryUpdate,
    ItemCreate,
    ItemUpdate,
    TablePurchaseCreate,
    TablePurchaseUpdate,
    ReservationCreate,
    ReservationUpdate,
    ReservationPurchaseCreate,
    ReservationPurchaseUpdate,
    TablePurchaseLogCreate,
    ReservationInputCreate,
    BidListCreate,
    BidListUpdate,
    LogHistoryCreate,
    LogHistoryResponse,
    SetMenuCreate,
    SetMenuUpdate,
    SetMenuResponse,
    SetMenuItemCreate,
    SetMenuItemUpdate,
    SetMenuItemResponse,
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

    logs = get_purchase_logs(db, table_id)

    db_table.total_price = sum(log.total_price for log in logs)

    return db_table


def recalculate_res_table_total_price(db: Session, table_id: str):
    db_table = get_table(db, table_id)

    if db_table is None:
        return None

    purchases = get_res_purchases_by_table(db, table_id)

    db_table.total_price = sum(purchase.total_price for purchase in purchases)

    return db_table


# ========================
# COMPANY
# ========================
def create_company(db: Session, company: CompanyCreate):
    invite_code = generate_invitation_code(db)

    db_company = Company(
        id=str(uuid.uuid4()),
        name=company.name,
        region=company.region,
        address=company.address,
        invite_code=invite_code,
    )

    db.add(db_company)
    db.flush()
    create_tables_for_company(db, db_company.id)
    db.commit()
    db.refresh(db_company)  # 여기서 created_at 등 자동 정보 생성

    return db_company


def get_company(db: Session, company_id: str):
    return db.query(Company).filter(Company.id == company_id).first()


def get_companies(db: Session):  # 전체 회사 반환
    return db.query(Company).all()


def update_company(db: Session, company_id: str, company_update: CompanyUpdate):
    db_company = get_company(db, company_id)

    if db_company is None:  # 해당 객체 없으면
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
# USER
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


def update_user(db: Session, user_id: str, user_update: UserUpdate):
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
# TABLE
# ========================
def create_table(db: Session, table: TableCreate):
    db_table = TableMaster(
        id=str(uuid.uuid4()),
        tablename=table.tablename,
        section=table.section,
        status=table.status,
        customer=table.customer,
        phonenumber=table.phonenumber,
        persons=table.persons,
        remark=table.remark,
        total_price=table.total_price,
        company_id=table.company_id,
        user_id=table.user_id,
        user_name=table.user_name,
        bid_end_at=table.bid_end_at,
        bid_available=table.bid_available,
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
):
    db_company = get_company(db, company_id)
    default_tables = []
    sections = db_company.sections
    for section in sections:
        for number in range(10):
            default_tables.append(
                TableMaster(
                    id=str(uuid.uuid4()),
                    tablename=f"{section}-{number+1}",
                    section=section,
                    status="available",
                    customer=None,
                    phonenumber=None,
                    persons=0,
                    remark=None,
                    total_price=0,
                    company_id=company_id,
                    user_id=None,
                    user_name=None,
                )
            )
    db.add_all(default_tables)
    return default_tables


def get_expired_timer_tables(db: Session):
    now = datetime.now(UTC)

    return (
        db.query(TableMaster)
        .filter(
            TableMaster.timer_end_at.isnot(None),
            TableMaster.timer_end_at <= now,
            TableMaster.timer_alert_sent_at.is_(None),
            TableMaster.status == "inuse",
        )
        .all()
    )


# ========================
# BIDLIST
# ========================
def create_bid_list(db: Session, bid: BidListCreate):
    db_bid = BidList(
        company_id=bid.company_id,
        company_name=bid.company_name,
        table_id=bid.table_id,
        user_id=bid.user_id,
        user_name=bid.user_name,
        user_phonenumber=bid.user_phonenumber,
        bid_price=bid.bid_price,
    )

    db.add(db_bid)
    db.commit()
    db.refresh(db_bid)
    return db_bid


def get_bid_list(db: Session, bid_id: int):
    return db.query(BidList).filter(BidList.id == bid_id).first()


def get_bid_list_by_table(db: Session, table_id: str):
    return db.query(BidList).filter(BidList.table_id == table_id).all()


def update_bid_list(db: Session, update_bid: BidListUpdate, bid_id: int):
    db_bid = get_bid_list(db, bid_id)
    if db_bid is None:
        return None
    update_data = update_bid.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_bid, key, value)
    db.commit()
    db.refresh(db_bid)
    return db_bid


def delete_bid_list(db: Session, bid_id: int):
    db_bid = get_bid_list(db, bid_id)
    if db_bid is None:
        return None
    db.delete(db_bid)
    return True


# ========================
# ITEMCATEGORY
# ========================
def create_item_category(db: Session, category: ItemCategoryCreate):
    db_category = ItemCategory(
        category_name=category.category_name,
        sort_order=category.sort_order,
        is_active=category.is_active,
    )

    db.add(db_category)
    db.commit()
    db.refresh(db_category)

    return db_category


def get_item_category(db: Session, category_id: int):
    return db.query(ItemCategory).filter(ItemCategory.id == category_id).first()


def get_item_categories(db: Session):
    return db.query(ItemCategory).all()


def update_item_category(
    db: Session, category_id: int, category_update: ItemCategoryUpdate
):
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
# ITEM
# ========================
def create_item(
    db: Session,
    item: ItemCreate,
):
    db_item = Item(
        item_name=item.item_name,
        item_price=item.item_price,
        is_active=item.is_active,
        company_id=item.company_id,
        category_id=item.category_id,
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


def get_items_by_category(
    db: Session, category_id: int, company_region: Optional[str] = None
):
    query = db.query(Item).filter(Item.category_id == category_id)
    if company_region is not None:
        query = query.join(Company).filter(Company.region == company_region)
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


def delete_item(
    db: Session,
    item_id: int,
):
    db_item = get_item(item_id, db)
    if db_item is None:
        return None
    db.delete(db_item)
    db.commit()
    return True


# ========================
# TablePurchase 여기서부터는 db: Session 맨 앞에.
# ========================
# def create_purchase(
#     db: Session,
#     purchase: TablePurchaseCreate
# ):
#     db_item = get_item(purchase.item_id, db) # 이번에 주문한 아이템.
#     db_table = get_table(db, purchase.table_id)

#     existing_purchase = (
#         db.query(TablePurchase).filter( # 주문한 거 또 주문하는지 확인.
#             TablePurchase.table_id == purchase.table_id,
#             TablePurchase.item_id == purchase.item_id).first()
#         )

#     if existing_purchase is not None:
#         existing_purchase.quantity += purchase.quantity
#         # 바뀐 품목당 가격 재계산
#         existing_purchase.total_price = existing_purchase.quantity * existing_purchase.unit_price
#         recalculate_table_total_price(db, existing_purchase.table_id)
#         db_table.purchase_summary = build_purchase_summary(db, db_table.id)
#         db.commit()
#         db.refresh(existing_purchase)
#         return existing_purchase

#     unit_price = db_item.item_price
#     total_price = unit_price * purchase.quantity
#     item_name = db_item.item_name

#     db_purchase = TablePurchase(
#         table_id = purchase.table_id,
#         item_id = purchase.item_id,
#         quantity = purchase.quantity,
#         unit_price = unit_price,
#         total_price = total_price,
#         item_name = item_name
#     )

#     db.add(db_purchase)
#     db.flush()
#     recalculate_table_total_price(db, purchase.table_id)
#     if db_table.purchase_summary is True:
#         new_purchases = build_purchase_summary(db, db_table.id)
#         db_table.purchase_summary.append(p for p in new_purchases)
#     db_table.purchase_summary = build_purchase_summary(db, db_table.id)
#     db.commit()
#     db.refresh(db_purchase)
#     db.refresh(db_table)
#     return db_purchase


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
    db: Session, purchase_id: int, purchase_update: TablePurchaseUpdate
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


def build_purchase_summary(db: Session, table_id: str) -> list[str]:
    purchases = (
        db.query(TablePurchaseLog)
        .filter(TablePurchaseLog.table_id == table_id)
        .order_by(TablePurchaseLog.batch_id)
        .all()
    )

    purchase_dict = {}

    for purchase in purchases:
        item_str = f"{purchase.item_name} {purchase.quantity}"

        if purchase.batch_id not in purchase_dict:
            purchase_dict[purchase.batch_id] = []

        purchase_dict[purchase.batch_id].append(item_str)

    summary = [", ".join(items) for items in purchase_dict.values()]
    return summary


# ========================
# TABLEPURCHASELOG
# ========================
def create_purchase_log(db: Session, log: TablePurchaseLogCreate):
    db_item = get_item(log.item_id, db)
    if db_item is None:
        return None
    db_user = get_user(db, log.user_id)
    if db_user is None:
        return None
    db_table = get_table(db, log.table_id)
    if db_table is None:
        return None

    db_log = TablePurchaseLog(
        table_id=log.table_id,
        item_id=db_item.id,
        item_name=db_item.item_name,
        quantity=log.quantity,
        unit_price=db_item.item_price,
        total_price=db_item.item_price * log.quantity,
        user_id=log.user_id,
        user_name=db_user.username,
        batch_id=log.batch_id,
    )

    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


def get_purchase_logs(db: Session, table_id: str):
    return (
        db.query(TablePurchaseLog).filter(TablePurchaseLog.table_id == table_id).all()
    )


def get_purchase_log(db: Session, log_id: int):
    return db.query(TablePurchaseLog).filter(TablePurchaseLog.id == log_id).first()


def delete_logs(
    db: Session,
    table_id: str,
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
    db_table = get_table(db, db_log.table_id)
    if db_table is None:
        return "Table not found"
    db_purchases = get_purchases_by_table(db, db_log.table_id)

    if db_log.set_menu_id is not None:
        # 세트 메뉴면
        db_set_menu = get_set_menu(db, db_log.set_menu_id, db_table.company_id)
        if db_set_menu is None:
            return "Set Menu not found"
        for item in db_set_menu.set_menu_items:
            db_item = get_item(item.item_id, db)
            if db_item is None:
                # 하나라도 못 찾으면 return
                db.rollback()
                return "Set Menu Item not found"
            flag = False
            for purchase in db_purchases:
                if purchase.item_id == db_item.id:
                    flag = True
                    purchase.quantity -= db_log.quantity * item.quantity
                    if purchase.quantity <= 0:
                        db.delete(purchase)
                    else:
                        purchase.total_price = purchase.unit_price * purchase.quantity
                    break
            if flag is False:
                db.rollback()
                return "Purchase not found"

    else:  # 단품
        flag = False
        db_item = get_item(db_log.item_id, db)
        if db_item is None:
            return "Item not found (single)"
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
    db.delete(db_log)
    db.flush()
    recalculate_table_total_price(db, db_table.id)
    db_table.purchase_summary = build_purchase_summary(db, db_table.id)
    db.commit()
    return db_table


def register_purchase(db: Session, log: TablePurchaseLogCreate):
    db_user = get_user(db, log.user_id)
    if db_user is None:
        return "USER NOT FOUND"
    db_table = get_table(db, log.table_id)
    if db_table is None:
        return "TABLE NOT FOUND"

    if db_table.status == "available":
        db_table.status = "inuse"
        db_table.registered_at = datetime.now(UTC)

    # 단품
    if log.set_menu_id is None:
        item = get_item(log.item_id, db)
        if item is None:
            return "ITEM NOT FOUND"
        db_log = TablePurchaseLog(
            table_id=log.table_id,
            item_id=item.id,
            item_name=item.item_name,
            set_menu_id=None,
            quantity=log.quantity,
            unit_price=item.item_price,
            total_price=item.item_price * log.quantity,
            user_id=log.user_id,
            user_name=db_user.username,
            batch_id=log.batch_id,
            created_at=datetime.now(UTC),
        )
        existing_purchase = (
            db.query(TablePurchase)
            .filter(
                TablePurchase.item_id == item.id, TablePurchase.table_id == db_table.id
            )
            .first()
        )
        if existing_purchase is not None:
            existing_purchase.quantity += log.quantity
            existing_purchase.total_price = existing_purchase.quantity * item.item_price
        else:
            db_purchase = TablePurchase(
                table_id=log.table_id,
                item_id=item.id,
                item_name=item.item_name,
                quantity=log.quantity,
                unit_price=item.item_price,
                total_price=item.item_price * log.quantity,
                created_at=datetime.now(UTC),
            )
            db.add(db_purchase)
    else:  # 세트
        set_menu = get_set_menu(db, log.set_menu_id, db_table.company_id)

        if set_menu is None:
            return "SET MENU NOT FOUND"
        db_log = TablePurchaseLog(
            table_id=log.table_id,
            item_id=None,
            item_name=set_menu.set_name,
            set_menu_id=log.set_menu_id,
            quantity=log.quantity,
            unit_price=set_menu.set_price,
            total_price=set_menu.set_price * log.quantity,
            user_id=log.user_id,
            user_name=db_user.username,
            batch_id=log.batch_id,
            created_at=datetime.now(UTC),
        )
        for component in set_menu.set_menu_items:
            db_item = get_item(component.item_id, db)
            if db_item is None:
                db.rollback()
                return "SET MENU ITEM NOT FOUND"
            existing_purchase = (
                db.query(TablePurchase)
                .filter(
                    TablePurchase.item_id == db_item.id,
                    TablePurchase.table_id == db_table.id,
                )
                .first()
            )
            if existing_purchase is not None:
                added_quantity = log.quantity * component.quantity
                existing_purchase.quantity += added_quantity
                existing_purchase.total_price = (
                    existing_purchase.quantity * db_item.item_price
                )
            else:
                db_purchase = TablePurchase(
                    table_id=log.table_id,
                    item_id=db_item.id,
                    item_name=db_item.item_name,
                    quantity=component.quantity * log.quantity,
                    unit_price=db_item.item_price,
                    total_price=db_item.item_price * component.quantity * log.quantity,
                    created_at=datetime.now(UTC),
                )
                db.add(db_purchase)
    db.add(db_log)
    db.flush()

    recalculate_table_total_price(db, db_table.id)
    db_table.purchase_summary = build_purchase_summary(db, db_table.id)
    db.commit()
    return {"message": "registerd purchase successfully"}


# ========================
# RESERVATION
# ========================
def register_reservation(
    db: Session,
    reservation_input: ReservationInputCreate,
    table_id: str,
):
    db_table = get_table(db, table_id)
    if db_table is None:
        return "Table not found"
    db_table.reserved_at = reservation_input.reservation_time
    db_reservation = Reservation(
        table_id=table_id,
        reservation_time=reservation_input.reservation_time,
        customer_name=reservation_input.customer_name,
        customer_phone=reservation_input.customer_phone,
        bid_price=reservation_input.bid_price,  # 가격만 입력 시
        is_fixed=reservation_input.is_fixed,
    )
    db_table.has_reservations = True
    db.add(db_reservation)
    db.flush()

    # 예약 하나에 여러 예약 내역이 가능하므로 id도 for문 안에서
    for purchase in reservation_input.purchases:
        db_item = get_item(purchase.item_id, db)
        if db_item is None:
            db.rollback()  # 앞에 해둔 게 있기 때문에 롤백
            return "Item not found"
        now = datetime.now(UTC)
        db_res_purchase = ReservationPurchase(
            reservation_id=db_reservation.id,
            item_id=purchase.item_id,
            item_name=db_item.item_name,
            unit_price=db_item.item_price,
            quantity=purchase.quantity,
            total_price=db_item.item_price * purchase.quantity,
            created_at=now,
        )
        db.add(db_res_purchase)

    db.commit()
    db.refresh(db_reservation)
    return db_reservation


def get_reservation(
    db: Session,
    reservation_id: int,
):
    return db.query(Reservation).filter(Reservation.id == reservation_id).first()


def get_reservations_by_table(
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
    # db_table = get_table(db, db_reservation.table_id)
    # 레이스컨디션 방지를 위해 아래와 같이 작성: with_for_update -> commit 까지 db 잠금
    db_table = db.query(TableMaster).filter(
        TableMaster.id == db_reservation.table_id
    ).with_for_update().first()

    if reservation_update.is_fixed is True:
        # 중복 등록 막는 핵심 코드
        existing_fixed = (
            db.query(Reservation)
            .filter(
                Reservation.table_id == db_reservation.table_id,
                Reservation.is_fixed.is_(True), # == true도 되지만 약간의 차이가 있음.
                Reservation.id != reservation_id,
                # 같은 테이블에서 현재 수정 중인 예약을 제외한 다른 확정 예약이 있는가?
            )
            .first()
         )
        if existing_fixed is not None:
            db.rollback()
            return "FIXED RESERVATION ALREADY EXISTS"

    if reservation_update.reservation_time is not None:
        db_reservation.reservation_time = reservation_update.reservation_time
        # db_table.reserved_at = reservation_update.reservation_time
    if reservation_update.customer_name is not None:
        db_reservation.customer_name = reservation_update.customer_name
    if reservation_update.customer_phone is not None:
        db_reservation.customer_phone = reservation_update.customer_phone
    if reservation_update.bid_price is not None:
        db_reservation.bid_price = reservation_update.bid_price
    if reservation_update.is_fixed is not None:
        db_reservation.is_fixed = reservation_update.is_fixed
        db_table.is_reserved = reservation_update.is_fixed
        db_table.bid_available = not reservation_update.is_fixed
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

    db_table.reserved_at = None

    db.delete(db_reservation)
    db.flush()
    db_left_reservations = get_reservations_by_table(db, db_table.id)
    if not db_left_reservations:
        db_table.has_reservations = False
        db_table.is_reserved = False
    db.commit()
    return db_table  # 최신화된 테이블 정보 보냄. 그래야 웹소켓에 씀


# ========================
# ReservationPurchase: table_id 접근 위해서는 Reservation을 거쳐야 함.
# ========================
def create_res_purchase(db: Session, res_purchase: ReservationPurchaseCreate):
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
        reservation_id=res_purchase.reservation_id,
        item_id=res_purchase.item_id,
        quantity=res_purchase.quantity,
        item_name=item_name,
        unit_price=unit_price,
        total_price=unit_price * res_purchase.quantity,
    )
    db.add(db_res_purchase)
    db.flush()

    recalculate_res_table_total_price(db, table_id)

    db.commit()
    db.refresh(db_res_purchase)
    return db_res_purchase


def get_res_purchase(
    db: Session,
    res_purchase_id: int,
):
    return (
        db.query(ReservationPurchase)
        .filter(ReservationPurchase.id == res_purchase_id)
        .first()
    )


def get_res_purchases_by_table(
    db: Session,
    table_id: str,
):
    return (
        db.query(ReservationPurchase)
        .join(Reservation)
        .filter(Reservation.table_id == table_id)
        .all()
    )
    ## 무조건 조인할 때는 이런 식으로


def get_res_purchases_by_reservation(
    db: Session,
    reservation_id: int,
):
    return (
        db.query(ReservationPurchase)
        .filter(ReservationPurchase.reservation_id == reservation_id)
        .all()
    )


def update_res_purchase(
    db: Session, res_purchase_id: int, res_purchase_update: ReservationPurchaseUpdate
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


def reservation_check_in(db: Session, reservation_id: int):
    db_reservation = get_reservation(db, reservation_id)  # 유효성 체크는 메인에서
    db_res_purchases = (
        db.query(ReservationPurchase)
        .filter(ReservationPurchase.reservation_id == reservation_id)
        .all()
    )
    # 없으면 [] -> 아래의 For문은 돌지 않는다.

    table_id = db_reservation.table_id  # String
    db_table = get_table(db, table_id)  # Table 객체
    if db_table is None:
        return None
    if db_table.status != "available":  # 빈 테이블인지 체크
        return "TABLE_NOT_AVAILABLE"

    ##################################
    ##### TablePurchaseLog 생성해야됨
    ##################################

    # res_purchase 개수 (즉 품목 개수) 만큼 tablepurchase생성
    for purchase in db_res_purchases:
        db_purchase = TablePurchase(
            table_id=table_id,
            item_id=purchase.item_id,
            item_name=purchase.item_name,
            quantity=purchase.quantity,
            unit_price=purchase.unit_price,
            total_price=purchase.total_price,
            created_at=datetime.now(UTC),
        )
        db.add(db_purchase)
    db.delete(db_reservation)
    db.flush()
    reservationEmpty = False
    db_reservations = get_reservations_by_table(db, db_table.id)
    if not db_reservations:
        reservationEmpty = True
    # TableMaster 변경: 1회
    db_table.customer = db_reservation.customer_name
    db_table.phonenumber = db_reservation.customer_phone
    db_table.status = "inuse"
    db_table.has_reservations = not reservationEmpty
    db_table.is_reserved = False
    db_table.purchase_summary = [
        ", ".join(
            f"{purchase.item_name} {purchase.quantity}" for purchase in db_res_purchases
        )
    ]
    db_table.registered_at = datetime.now(UTC)
    db_table.reserved_at = (
        min(reservation.reservation_time for reservation in db_reservations)
        if db_reservations
        else None
    )
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
    db_table = get_table(db, table_id)  # 해당 테이블 가져옴
    if db_table is None:
        return None
    if db_table.status != "inuse":
        return "TABLE_NOT_USING"

    db_purchases = get_purchases_by_table(db, table_id)
    # 해당 테이블의 구매 리스트 ex. 호세3, 모엣1, 잭다니엘2 ...
    # 아웃 시킬 때 db에서 내역을 날린다면, 현재 사용 중인 기록만 남게 됨.

    out_at = datetime.now(UTC)
    business_date_source = db_table.registered_at or out_at

    db_history = TableHistory(
        table_id=table_id,
        tablename=db_table.tablename,
        section=db_table.section,
        customer_name=db_table.customer,
        customer_phone=db_table.phonenumber,
        persons=db_table.persons,
        remark=db_table.remark,
        user_id=db_table.user_id,
        user_name=db_table.user_name,
        company_id=db_table.company_id,
        registered_at=db_table.registered_at,
        out_at=out_at,
        business_date=get_business_date(business_date_source),
        closed_reason=closed_reason,
        purchase_summary=db_table.purchase_summary,
    )

    db.add(db_history)
    db.flush()

    db_notification = Notification(
        company_id=db_table.company_id,
        title=f"테이블 아웃",
        body=f"{db_table.tablename}번 테이블이 아웃 처리 되었습니다.",
        type="OUT",
    )

    db.add(db_notification)
    db.flush()

    for purchase in db_purchases:
        db_history_purchase = TableHistoryPurchase(
            history_id=db_history.id,
            item_id=purchase.item_id,
            item_name=purchase.item_name,
            quantity=purchase.quantity,
            unit_price=purchase.unit_price,
            total_price=purchase.total_price,
            created_at=datetime.now(UTC),
        )
        db.add(db_history_purchase)

    # 이제 구매 내역 지우기
    for purchase in db_purchases:
        db.delete(purchase)

    db_logs = get_purchase_logs(db, table_id)
    for log in db_logs:
        db_log_history = LogHistory(
            history_id=db_history.id,
            table_id=log.table_id,
            item_id=log.item_id,
            set_menu_id=log.set_menu_id,
            item_name=log.item_name,
            batch_id=log.batch_id,
            user_id=log.user_id,
            user_name=log.user_name,
            quantity=log.quantity,
            unit_price=log.unit_price,
            total_price=log.quantity * log.unit_price,
        )
        db.delete(log)
        db.add(db_log_history)
        db.flush()

    # 테이블 초기화
    db_table.status = "available"
    db_table.customer = ""
    db_table.phonenumber = ""
    db_table.persons = 0
    db_table.remark = ""
    db_table.total_price = 0
    db_table.purchase_summary = []
    db_table.registered_at = None
    db_table.user_id = None
    db_table.user_name = None
    db_table.timer_started_at = None
    db_table.timer_end_at = None
    db_table.timer_alert_sent_at = None

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
    return (
        db.query(TableHistoryPurchase)
        .filter(TableHistoryPurchase.id == history_purchase_id)
        .first()
    )


def get_history_purchases_by_table(
    db: Session,
    table_id: str,
):
    return (
        db.query(TableHistoryPurchase)
        .join(TableHistory)
        .filter(TableHistory.table_id == table_id)
        .all()
    )
    ## 만약 Model.py에 relationship이 없으면
    ## .join(TableHistory, TableHistoryPurchase.history_id == TableHistory.id)
    ## 이렇게 써야함.


def get_history_purchases_by_history(db: Session, history_id: int):
    return (
        db.query(TableHistoryPurchase)
        .filter(TableHistoryPurchase.history_id == history_id)
        .all()
    )


def reregister_table(
    db: Session,
    history_id: int,
    table_id: str,
):
    db_history = get_history(db, history_id)
    if db_history is None:
        return "History not found"
    if db_history.re_registered_at is not None:
        return "History already re-registered"

    db_history_purchases = get_history_purchases_by_history(db, history_id)

    db_table = get_table(db, table_id)
    if db_table is None:
        return "Table not found"

    if db_table.status == "inuse":
        return "Table already in use"

    db_log_histories = get_log_histories(db, db_history.id)
    if not db_log_histories:
        return "Log not found"

    # 일반 정보 옮기기
    db_table.customer = db_history.customer_name
    db_table.persons = db_history.persons
    db_table.phonenumber = db_history.customer_phone
    db_table.remark = (
        f"{db_history.tablename}번 재등록"
        if not db_history.remark
        else f"{db_history.remark}, {db_history.tablename}번 재등록"
    )
    db_table.status = "inuse"
    db_table.registered_at = db_history.registered_at
    db_table.purchase_summary = db_history.purchase_summary
    # 구매 정보 옮기기
    for hp in db_history_purchases:
        db_purchase = TablePurchase(
            table_id=db_table.id,
            item_id=hp.item_id,
            item_name=hp.item_name,
            quantity=hp.quantity,
            unit_price=hp.unit_price,
            total_price=hp.quantity * hp.unit_price,
        )
        db.add(db_purchase)
    total_price = sum(hp.unit_price * hp.quantity for hp in db_history_purchases)
    db_table.total_price = total_price
    db.flush()

    # 로그 옮기기
    for log in db_log_histories:
        db_log = TablePurchaseLog(
            table_id=db_table.id,
            item_id=log.item_id,
            set_menu_id=log.set_menu_id,
            item_name=log.item_name,
            batch_id=log.batch_id,
            user_id=log.user_id,
            user_name=log.user_name,
            quantity=log.quantity,
            unit_price=log.unit_price,
            total_price=log.quantity * log.unit_price,
        )
        db.add(db_log)
        db.flush()
    # 기존 로그 없애기
    for log in db_log_histories:
        db.delete(log)
    db_table.purchase_summary = db_history.purchase_summary
    db_history.re_registered_at = datetime.now(UTC)
    db_history.re_registered_table_id = db_table.id
    db.delete(db_history)
    db.commit()
    return True


# ========================
# NOTIFICATION
# ========================
def create_timer_notification(
    db: Session,
    table: TableMaster,
):
    db_table = get_table(db, table.id)

    db_notification = Notification(
        company_id=db_table.company_id,
        title=f"타이머 만료",
        body=f"{db_table.tablename}번 테이블 타이머가 만료 되었습니다.",
        type="TIMEOUT",
    )

    db.add(db_notification)
    return db_notification


def get_notification_by_company(db: Session, company_id: str):
    return (
        db.query(Notification)
        .filter(Notification.company_id == company_id)
        .order_by(Notification.created_at.desc())
        .all()
    )


# ========================
# RESET
# ========================


def reset_daily_state(db: Session):
    try:
        # 아직 사용 중인 테이블 아웃 처리(히스토리)
        db_table = db.query(TableMaster).filter(TableMaster.status == "inuse").all()
        for table in db_table:
            try:
                table_out(db, table.id, closed_reason="daily_reset")
            except Exception as e:
                db.rollback()
                print(f"[Daily reset error]: table_id: {table.id}, e: {e}")

        # 재등록용 로그 히스토리 초기화
        db.query(LogHistory).delete(synchronize_session=False)

        # 현재 주문 로그 초기화
        db.query(TablePurchaseLog).delete(synchronize_session=False)

        # 예약 구매 내역 먼저 삭제
        db.query(ReservationPurchase).delete(synchronize_session=False)

        # 예약 삭제
        db.query(Reservation).delete(synchronize_session=False)

        # 현재 테이블 구매 내역 삭제
        db.query(TablePurchase).delete(synchronize_session=False)

        now_kst = datetime.now(KST)
        bid_end_at = now_kst.replace(
            hour=22,
            minute=0,
            second=0,
            microsecond=0,
        )
        if bid_end_at <= now_kst:
            bid_end_at += timedelta(days=1)
        # 테이블 마스터 초기화
        db.query(TableMaster).update(
            {
                TableMaster.status: "available",
                TableMaster.customer: "",
                TableMaster.phonenumber: "",
                TableMaster.persons: 0,
                TableMaster.remark: "",
                TableMaster.total_price: 0,
                TableMaster.purchase_summary: [],
                TableMaster.registered_at: None,
                TableMaster.user_id: None,
                TableMaster.user_name: None,
                TableMaster.is_reserved: False,
                TableMaster.timer_started_at: None,
                TableMaster.timer_end_at: None,
                TableMaster.timer_alert_sent_at: None,
                TableMaster.bid_end_at: bid_end_at,
                TableMaster.has_reservations: False,
                TableMaster.bid_available: True,
                TableMaster.reserved_at: None,
            },
            synchronize_session=False,
        )

        db.commit()
        return True

    except Exception:
        db.rollback()
        raise


# ========================
# MOVE
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
    db_from.purchase_summary = []
    db_from.remark = ""
    db_from.status = "available"
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


# ========================
# LOGHISTORY
# ========================
def create_log_history(
    db: Session,
    log_history: LogHistoryCreate,
):
    db_log_history = LogHistory(
        id=log_history.id,
        history_id=log_history.history_id,
        item_id=log_history.item_id,
        item_name=log_history.item_name,
        quantity=log_history.quantity,
        unit_price=log_history.unit_price,
    )
    db.add(db_log_history)
    db.commit()
    return db_log_history


def get_log_histories(
    db: Session,
    history_id: int,
):
    return db.query(LogHistory).filter(LogHistory.history_id == history_id).all()


# ========================
# SET MENU
# ========================
def create_set_menu(db: Session, set_menu: SetMenuCreate):

    if not set_menu.items:
        return None

    item_ids = [item.item_id for item in set_menu.items]

    db_items = (
        db.query(Item)
        .filter(
            Item.id.in_(item_ids), Item.company_id == set_menu.company_id
        )  # db에서는 in_()
        .all()
    )
    items_by_id = {item.id: item for item in db_items}

    if len(items_by_id) != len(set(item_ids)):
        return "ITEM NOT FOUND"

    db_set_menu = SetMenu(
        company_id=set_menu.company_id,
        set_name=set_menu.set_name,
        set_price=set_menu.set_price,
        is_active=set_menu.is_active,
    )

    db.add(db_set_menu)
    db.flush()

    for item in set_menu.items:
        db.add(
            SetMenuItem(
                set_menu_id=db_set_menu.id,
                item_id=item.item_id,
                quantity=item.quantity,
            )
        )

    db.commit()
    db.refresh(db_set_menu)
    return db_set_menu


def get_set_menu(db: Session, set_menu_id: int, company_id: str):
    return (
        db.query(SetMenu)
        .filter(SetMenu.id == set_menu_id, SetMenu.company_id == company_id)
        .first()
    )


def get_set_menus_by_company(db: Session, company_id: str):
    return db.query(SetMenu).filter(SetMenu.company_id == company_id).all()


def update_set_menu(
    db: Session, set_menu_id: int, company_id: str, set_menu_update: SetMenuUpdate
):

    db_set_menu = get_set_menu(db, set_menu_id, company_id)
    if db_set_menu is None:
        return "SET MENU NOT FOUND"

    # 구성품 비었나 검사
    if set_menu_update.items is not None:
        if not set_menu_update.items:  # []가 오면 오류.
            return "EMPTY UPDATE ITEM"

        item_ids = [item.item_id for item in set_menu_update.items]

        db_items = (
            db.query(Item)
            .filter(
                Item.id.in_(item_ids),
                Item.company_id == company_id,
            )
            .all()
        )

        if len(db_items) != len(set(item_ids)):
            return "ITEM NOT FOUND"

        db_set_menu.set_menu_items.clear()  # 연결된 아이템 다 지우고 (delete-orphan이라서 가능)
        db_set_menu.set_menu_items.extend(
            SetMenuItem(
                item_id=item.item_id,
                quantity=item.quantity,
            )
            for item in set_menu_update.items
        )

    update_data = set_menu_update.model_dump(
        exclude_unset=True, exclude={"items"}
    )  # items라는 거는 models.py에 없으니까.

    for key, value in update_data.items():
        setattr(db_set_menu, key, value)

    db.commit()
    db.refresh(db_set_menu)
    return db_set_menu


# ========================
# SET MENU ITEMS
# ========================
def get_set_menu_items_by_company(
    db: Session,
    company_id: str,
):
    return (
        db.query(SetMenuItem)
        .join(SetMenu, SetMenuItem.set_menu_id == SetMenu.id)
        .filter(SetMenu.company_id == company_id)
        .all()
    )


def create_set_menu_item(
    db: Session,
    set_menu_item: SetMenuItemCreate,
):
    db_set_menu_items = SetMenuItem(
        item_id=set_menu_item.item_id,
        set_menu_id=set_menu_item.set_menu_id,
        quantity=set_menu_item.quantity,
    )
    db.add(db_set_menu_items)
    db.commit()
    db.refresh(db_set_menu_items)
    return db_set_menu_items
