from database import SessionLocal, engine
from models import (
    Base,
    Company,
    User,
    TableMaster,
    ItemCategory,
    Item,
)
from datetime import datetime, UTC, timedelta
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

def utc_now():
    return datetime.now(UTC)

def seed():
    # 테이블 생성
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # -------------------------
        # Company
        # -------------------------
        # Seed uses fixed ids for local test convenience.
        # Real create endpoints generate Company.id and invite_code on the server.
        company = db.query(Company).filter(Company.id == "company_1").first()

        if company is None:
            company = Company(
                id="company_1",
                name="테이블비드1",
                region="이태원",
                address="서울시 용산구 우사단로 10길 9",
                invite_code="GRID01",
                sections = ['A', 'B', 'C', 'D', 'E']
            )
            db.add(company)

        # -------------------------
        # User
        # -------------------------
        user = db.query(User).filter(User.id == "4pB5xej3AdT5sL4koRJhny2jZVo1").first()

        if user is None:
            user = User(
                id="4pB5xej3AdT5sL4koRJhny2jZVo1",
                username="tb1",
                email="tb1@dev.com",
                role="owner",
                fcmtoken="fkcA0tVDxk5GqBS_7Z5iq6:APA91bE29fyBnzrDri2oqhfB1ZRdDpeEN-f1lpBYrBoM0qZuXV0-0Lvjz012c1WGe_nh7uuCc4H-RyWSvR0Uvzq4jHkhm0RqALbEbQ8S0oVgUi60Papo_Q0",
                tablecardfields=["purchases", "persons"],
                company_id="company_1",
            )
            db.add(user)

        # -------------------------
        # Tables
        # -------------------------
        # Seed keeps stable table ids, but real create endpoints generate
        # TableMaster.id as an internal UUID and keep tablename as the visible name.
        table_names = [
            ("A1", "A"),
            ("A2", "A"),
            ("A3", "A"),
            ("A4", "A"),
            ("VIP1", "vip"),
            ("VIP2", "vip"),
        ]

        now = datetime.now(KST)
        bid_end_at = now.replace(hour=22, minute=0, second=0, microsecond=0)
        if bid_end_at <= now:
            bid_end_at += timedelta(days=1)

        for table_id, section in table_names:
            table = db.query(TableMaster).filter(TableMaster.id == table_id).first()

            if table is None:
                table = TableMaster(
                    id=table_id,
                    tablename=table_id,
                    section=section,
                    status="available",
                    customer="",
                    phonenumber="",
                    persons=0,
                    remark="",
                    total_price=0,
                    registered_at=None,
                    timer_started_at=None,
                    company_id="company_1",
                    user_id=None,
                    user_name=None,
                    is_reserved=False,
                    bid_available=True,
                    bid_end_at=bid_end_at,
                )

            table.bid_available = True
            table.bid_end_at = bid_end_at
            db.add(table)

        # -------------------------
        # ItemCategory
        # -------------------------
        categories = [
            ("위스키", 1),
            ("데킬라", 2),
            ("샴페인", 3),
        ]

        for category_name, sort_order in categories:
            existing_category = (
                db.query(ItemCategory)
                .filter(ItemCategory.category_name == category_name)
                .first()
            )

            if existing_category is None:
                category = ItemCategory(
                    category_name=category_name,
                    sort_order=sort_order,
                    is_active=True,
                )
            db.add(category)
            db.flush()

        # -------------------------
        # Items
        # -------------------------
        items = [
            ("호세", 150000, 2),
            ("모엣", 250000, 3),
            ("잭다니엘", 180000, 1),
            ("돔페리뇽", 500000, 3),
        ]

        for item_name, item_price, item_category in items:
            existing_item = (
                db.query(Item)
                .filter(
                    Item.company_id == "company_1",
                    Item.item_name == item_name,
                    Item.category_id == item_category,
                )
                .first()
            )

            if existing_item is None:
                item = Item(
                    item_name=item_name,
                    item_price=item_price,
                    is_active=True,
                    company_id="company_1",
                    category_id=item_category,
                )
                db.add(item)

        db.commit()
        print("✅ Seed data inserted successfully.")

    except Exception as e:
        db.rollback()
        print("❌ Seed failed:", e)

    finally:
        db.close()


if __name__ == "__main__":
    seed()
