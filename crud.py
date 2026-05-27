from sqlalchemy.orm import Session
from models import Company, User, TableMaster, ItemCategory, Item
from schemas import (CompanyCreate,
                    CompanyUpdate,
                    UserCreate,
                    UserUpdate,
                    TableCreate, 
                    TableUpdate,
                    ItemCategoryCreate,
                    ItemCategoryUpdate,
                    ItemCreate,
                    ItemUpdate,
                )
from typing import Optional

# ==============
# Company
# ==============
def create_company(db: Session, company: CompanyCreate):
    db_company = Company(
        id=company.id,
        name=company.name,
        region=company.region,
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

    db.commit()
    db.refresh(db_company)

    return db_company

# ==============
# User
# ==============
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

# ==============
# Table
# ==============
def create_table(db: Session, table: TableCreate):
    db_table = TableMaster(
        id = table.id,
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
        db_table.status = table_update.status

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

    if table_update.group_id is not None:
        db_table.group_id = table_update.group_id

    if table_update.ismaster is not None:
        db_table.ismaster = table_update.ismaster

    if table_update.mastertablenumber is not None:
        db_table.mastertablenumber = table_update.mastertablenumber

    db.commit()
    db.refresh(db_table)

    return db_table
    

# ==============
# ItemCategory
# ==============
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

# ==============
# Item
# ==============
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