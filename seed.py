from database import SessionLocal, engine
from models import (
    Base,
    Company,
    User,
    TableMaster,
    ItemCategory,
    Item,
)
from datetime import datetime, UTC

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
        company = db.query(Company).filter(Company.id == "company_1").first()

        if company is None:
            company = Company(
                id="company_1",
                name="테스트매장",
                region="이태원",
                invite_code = "GRID01"
            )
            db.add(company)

        # -------------------------
        # User
        # -------------------------
        user = db.query(User).filter(User.id == "or0VV3Fx9pO4pvaygGKrgR36rpq1").first()

        if user is None:
            user = User(
                id="or0VV3Fx9pO4pvaygGKrgR36rpq1",
                username="DEVACC",
                email="devacc@naver.com",
                role="owner",
                fcmtoken=None,
                tablecardfields=["purchases", "persons"],
                company_id="company_1",
            )
            db.add(user)

        # -------------------------
        # Tables
        # -------------------------
        table_names = [
            ("A1", "A"),
            ("A2", "A"),
            ("A3", "A"),
            ("A4", "A"),
            ("VIP1", "vip"),
            ("VIP2", "vip"),
        ]

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
                    ismaster=False,
                    mastertable_id=None,
                    timer_started_at=None,
                    company_id="company_1",
                    user_id=None,
                    user_name=None,
                    group_id=None,
                )
                db.add(table)

        # -------------------------
        # ItemCategory
        # -------------------------
        category = (
            db.query(ItemCategory)
            .filter(ItemCategory.category_name == "위스키")
            .first()
        )

        if category is None:
            category = ItemCategory(
                category_name="위스키",
                sort_order=1,
                is_active=True,
            )
            category = ItemCategory(
                category_name="데킬라",
                sort_order=2,
                is_active=True,
            )
            category = ItemCategory(
                category_name="샴페인",
                sort_order=3,
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
                    category_id=category.id,
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