from fastapi import BackgroundTasks, FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from websocket_manager import manager
from sqlalchemy.orm import Session
from typing import List
import models
import crud
import schemas
from database import engine, get_db, SessionLocal
from typing import Optional
from firebase_push import send_push_to_token
from datetime import datetime, UTC, date
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from contextlib import asynccontextmanager
from zoneinfo import ZoneInfo


models.Base.metadata.create_all(bind=engine)

scheduler = BackgroundScheduler(timezone=ZoneInfo("Asia/Seoul"))


def send_table_out_pushes(
    company_id: str,
    table_id: str,
    tablename: str,
):
    db = SessionLocal()

    try:
        users = crud.get_users_by_company(db, company_id)
        push_targets = [
            {
                "user_id": user.id,
                "fcmtoken": user.fcmtoken
            }
            for user in users
            if user.fcmtoken and user.is_push_on is not False
        ]
    finally:
        db.close()

    invalid_user_ids = []

    for target in push_targets:
        try:
            send_push_to_token(
                token=target['fcmtoken'],
                title="테이블 아웃 알림",
                body=f"{tablename} 테이블이 아웃 처리되었습니다.",
                data={
                    "type": "table_out",
                    "table_id": table_id,
                    "company_id": company_id,
                    "tablename": tablename,
                },
            )
        except Exception as e:
            print(f"푸시 발송 실패 user_id: {target['user_id']}: {e}")

            if is_invalid_fcm_token_error(e):
                invalid_user_ids.append(target['user_id'])

    clear_invalid_fcm_tokens(invalid_user_ids)    

def start_scheduler():
    if scheduler.running:
        return

    scheduler.add_job(
        run_expired_timer_check,
        "interval",
        seconds=30,
        id="expired_timer_check",
        replace_existing=True,
    )
    scheduler.add_job(
        run_daily_reset,
        CronTrigger(hour=14, minute=0, timezone=ZoneInfo("Asia/Seoul")),
        id="daily_reset",
        replace_existing=True,
    )
    scheduler.start()
    print("[Scheduler] expired timer checker started")
    print("[Scheduler] daily reset scheduled at 14:00 KST")


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()

    try:
        yield
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)
            print("[Scheduler] shutdown")


app = FastAPI(lifespan=lifespan)

# =====================
# COMPANY API
# =====================
@app.post("/companies", response_model=schemas.CompanyResponse)
def create_company(
    company: schemas.CompanyCreate, # schema로 검사 진행 (클라이언트에서 데이터가 들어오거나 나갈 때) 입구 문지기 역할임.
    db: Session = Depends(get_db),
    ):
    return crud.create_company(db, company)


@app.get("/companies/{company_id}", response_model=schemas.CompanyResponse)
def read_company(
    company_id: str, 
    db: Session = Depends(get_db)
    ):
    
    db_company = crud.get_company(db, company_id)
        
    if db_company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return db_company

@app.get("/companies", response_model=list[schemas.CompanyResponse])
def read_companies(db: Session = Depends(get_db)):
    return crud.get_companies(db)
    
@app.patch("/companies/{company_id}", response_model=schemas.CompanyResponse)
def update_company(
    company_id: str,
    company_update: schemas.CompanyUpdate, # FASTAPI에서는 이 줄이 검증, 변환까지 해줌.
    db: Session = Depends(get_db)
):
    db_company = crud.update_company(db, company_id, company_update)

    if db_company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return db_company

@app.get("/companies/invite-code/{invite_code}", response_model=schemas.CompanyResponse)
def read_company_by_invite_code(
    invite_code: str,
    db: Session = Depends(get_db)
):
    db_company = crud.get_company_by_invite_code(db, invite_code)
    if db_company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return db_company

@app.patch("/companies/{company_id}/regenerate-invite-code", response_model=schemas.CompanyResponse)
def regenerate_invite_code (
    company_id: str,
    db: Session = Depends(get_db)
):
    result = crud.regenerate_invite_code(db, company_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return result
    


# =====================
# USER API
# =====================

@app.post("/users", response_model=schemas.UserResponse)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    db_user = crud.get_user(db, user.id)
    db_company = crud.get_company(db, user.company_id)
    if db_user is not None:
        raise HTTPException(status_code=400, detail="User alreay exists")
    return crud.create_user(db, user)

@app.get("/users/{user_id}", response_model=schemas.UserResponse)
def read_user (
        user_id: str,    
        db: Session = Depends(get_db),
):
    db_user = crud.get_user(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail='User not found')
    return db_user

@app.get("/companies/{company_id}/users", response_model=list[schemas.UserResponse])
def get_users_by_company (
        company_id: str,    
        db: Session = Depends(get_db),
):
    return crud.get_users_by_company(db, company_id)

@app.patch("/users/{user_id}", response_model=schemas.UserResponse)
def update_user(
    user_id: str,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db)
):
    db_user = crud.update_user(db, user_id, user_update)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.delete("/users/{user_id}")
def delete_user (
    user_id: str,
    db: Session = Depends(get_db)
):
    result = crud.delete_user(db, user_id)
    if result is False:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

# =====================
# TABLE API
# =====================

@app.post("/tables", response_model=schemas.TableResponse)
def create_table(
    table: schemas.TableCreate,
    db: Session = Depends(get_db)
):
    db_company = crud.get_company(db, table.company_id)
    # db_group = crud.get_gr

    if db_company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return crud.create_table(db, table)

@app.get("/tables/{table_id}", response_model=schemas.TableResponse)
def read_table(
    table_id: str,
    db: Session = Depends(get_db)
):
    db_table = crud.get_table(db, table_id)
    if db_table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    return db_table

@app.get("/companies/{company_id}/tables", response_model=list[schemas.TableResponse])
def read_tables_by_company(
    company_id: str,
    section: Optional[str] = None,
    db: Session = Depends(get_db)
):
    if section is not None:
        return crud.get_tables_by_company_and_section(db, company_id, section)
    return crud.get_tables_by_company(db, company_id)
    
@app.patch("/tables/{table_id}", response_model=schemas.TableResponse)
async def update_table(
    table_id: str,
    table_update: schemas.TableUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_table = crud.update_table(db, table_update, table_id)
    # db_group = crud.get
    if db_table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    payload = schemas.TableResponse.model_validate(db_table).model_dump(mode="json")
    company_id = db_table.company_id
    
    background_tasks.add_task(
        manager.broadcast,
        company_id,
        {
            "type": "table_updated",
            "payload": payload
            # db_table이라는 SQLAlchemy 객체를
            # TableResponse 스키마 형식에 맞게 읽어서
            # Pydantic 객체로 만들어라
            # 그다음에 json
        }
    )
    return db_table

@app.delete("/tables/{table_id}")
def delete_table(
    table_id: str,
    db: Session = Depends(get_db)
):
    db_table = crud.delete_table(db, table_id)
    if db_table is False:
        raise HTTPException(status_code=404, detail="Table not found")
    return {"message": "Table deleted successfully"}


# =====================
# BIDLIST API
# =====================
@app.post("/bid-lists", response_model=schemas.BidListResponse)
def create_bid_list(
    bid: schemas.BidListCreate,
    db: Session = Depends(get_db)
):
    return crud.create_bid_list(db, bid)

@app.get("/bid-lists/{bid_id}", response_model=schemas.BidListResponse)
def read_bid_list (
    bid_id: int,
    db: Session = Depends(get_db)
):
    db_bid = crud.get_bid_list(db, bid_id)
    if db_bid is None:
        raise HTTPException(status_code=404, detail="BID NOT FOUND")
    return db_bid

@app.get("/tables/{table_id}/bid-lists", response_model=list[schemas.BidListResponse])
def read_bid_lists (
    table_id: str,
    db: Session = Depends(get_db)
):
    db_bid = crud.get_bid_list_by_table(db, table_id)
    if db_bid is None:
        raise HTTPException(status_code=404, detail="BID NOT FOUND ON TABLE")
    return db_bid

@app.get("/bid-lists/{bid_id}", response_model=schemas.BidListResponse)
def update_bid_list (
    bid_id: int,
    db: Session = Depends(get_db)
):
    db_bid = crud.update_bid_list(db, bid_id)
    if db_bid is None:
        raise HTTPException(status_code=404, detail="BID NOT FOUND")
    return db_bid

@app.delete("/bid-list/{bid_id}")
def delete_bid (
    bid_id: int,
    db: Session = Depends(get_db)
):
    result = crud.delete_bid_list(db, bid_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Bid not found")
    if result is True:
        return {"message": "Bid deleted successfully"}

# =====================
# CATEGORY API
# =====================
@app.post("/categories", response_model=schemas.ItemCategoryResponse)
def create_category(
    category: schemas.ItemCategoryCreate,
    db: Session = Depends(get_db)
):
    return crud.create_item_category(db, category)

@app.get("/categories/{category_id}", response_model=schemas.ItemCategoryResponse)
def read_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    db_category = crud.get_item_category(db, category_id)

    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category

@app.get("/categories", response_model=list[schemas.ItemCategoryResponse])
def read_categories(
    db: Session = Depends(get_db)
):
    return crud.get_item_categories(db)

@app.patch("/categories/{category_id}", response_model=schemas.ItemCategoryResponse)
def update_categories(
    category_id: int,
    category_update: schemas.ItemCategoryUpdate,
    db: Session = Depends(get_db)
): 
    db_category = crud.update_item_category(db, category_id, category_update)
    
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category

# =====================
# ITEM API
# =====================
@app.post("/items", response_model=schemas.ItemResponse)
def create_item(
    item: schemas.ItemCreate,
    db: Session = Depends(get_db)
):    
    db_company = crud.get_company(db, item.company_id)
    db_category = crud.get_item_category(db, item.category_id)
    if db_company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return crud.create_item(db, item)

@app.get("/items/{item_id}", response_model=schemas.ItemResponse)
def read_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    db_item = crud.get_item(item_id, db)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@app.get("/companies/{company_id}/items", response_model=list[schemas.ItemResponse])
def read_items_by_company(
    company_id: str,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    if category_id is None:
        return crud.get_items_by_company(company_id, db)    
    return crud.get_items_by_company_and_category(company_id, category_id, db)

@app.get("/categories/{category_id}/items", response_model=list[schemas.ItemResponse])
def read_items_by_category(
    category_id: int,
    company_region: Optional[str]=None,
    db: Session = Depends(get_db)
):
    return crud.get_items_by_category(db, category_id, company_region)

@app.patch("/items/{item_id}", response_model=schemas.ItemResponse)
def update_item(
    item_id: int,
    item_update: schemas.ItemUpdate,
    db: Session = Depends(get_db)
):
    db_item = crud.update_item(item_id, item_update, db)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@app.delete("/items/{item_id}")
def delete_item (
    item_id: int,
    db: Session = Depends(get_db)
):
    result = crud.delete_item(db, item_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Item not found")
    if result is True:
        return {"message": "Item deleted successfully"}
    
# =====================
# PURCHASE API
# =====================
@app.post("/purchases", response_model=schemas.TablePurchaseResponse)
async def create_purchase(
    purchase: schemas.TablePurchaseCreate,
    backgroud_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    #FK check
    db_table = crud.get_table(db, purchase.table_id)
    db_item = crud.get_item(purchase.item_id, db)

    if db_table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    db_purchase = crud.create_purchase(db, purchase)
    db.refresh(db_table)

    payload = schemas.TableResponse.model_validate(db_table).model_dump(mode="json")
    company_id = db_table.company_id

    backgroud_tasks.add_task(
        manager.broadcast,
        company_id,
        {
            "type": "table_updated",
            "payload": payload
        }
    )
    
    return db_purchase

@app.post("/register-purchase")
async def register_purchase(
    log: schemas.TablePurchaseLogCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    
    result = crud.register_purchase(db, log)
    db_table = crud.get_table(db, log.table_id)
    if db_table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    if result == "ITEM NOT FOUND":
        raise HTTPException(status_code=404, detail="Item not found")
    if result == "USER NOT FOUND":
        raise HTTPException(status_code=404, detail="User not found")

    payload = schemas.TableResponse.model_validate(db_table).model_dump(mode="json")

    background_tasks.add_task(
        manager.broadcast,
        db_table.company_id,
        {
            "type": "table_updated",
            "payload": payload,
        }
    )
    return result
    


@app.get("/purchases/{purchase_id}", response_model=schemas.TablePurchaseResponse)
def read_purchase(
    purchase_id: int,
    db: Session = Depends(get_db)
):
    db_purchase = crud.get_purchase(db, purchase_id)
    if db_purchase is None:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return db_purchase

@app.get("/tables/{table_id}/purchases", response_model=list[schemas.TablePurchaseResponse])
def read_purchases_by_table (
    table_id: str,
    db: Session = Depends(get_db)
):
    db_table = crud.get_table(db, table_id)
    if db_table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    
    return crud.get_purchases_by_table(db, table_id)
    
@app.patch("/purchases/{purchase_id}", response_model=schemas.TablePurchaseResponse)
def update_purchase(
    purchase_id: int,
    purchase_update: schemas.TablePurchaseUpdate,
    db: Session = Depends(get_db)
):
    db_purchase = crud.get_purchase(db, purchase_id)
    if db_purchase is None:
        raise HTTPException(status_code=404, detail="Purchase not found")

    return crud.update_purchase(db, purchase_id, purchase_update)

@app.delete("/purchases/{purchase_id}")
def delete_purchase (
    purchase_id: int,
    db: Session = Depends(get_db)
) : 
    result = crud.delete_purchase(db, purchase_id)
    if result is True:
        return {"message": "Deleted purchase successfully"}
    else:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
# =====================
# TABLEPURCHASELOG API
# =====================
@app.post("/purchase-log", response_model=schemas.TablePurchaseLogResponse)
def create_purchase_log(
    log: schemas.TablePurchaseLogCreate,
    db: Session = Depends(get_db)
):
    #FK check
    db_table = crud.get_table(db, log.table_id)
    db_item = crud.get_item(log.item_id, db)
    db_user = crud.get_user(db, log.user_id)

    if db_table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return crud.create_purchase_log(db, log)

@app.get("/tables/{table_id}/purchase-logs", response_model=list[schemas.TablePurchaseLogResponse])
def read_purchase_log(
    table_id: str,
    db: Session = Depends(get_db)
):
    db_table = crud.get_table(db, table_id)
    if db_table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    db_log = crud.get_purchase_logs(db, table_id)
    return db_log # 비었으면 []

@app.delete("/tables/{table_id}/purchase-logs")
def delete_logs (
    table_id: str,
    db: Session = Depends(get_db)
):
    db_table = crud.get_table(db, table_id)
    if db_table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    
    db_logs = crud.delete_logs(db, table_id)
    if db_logs is True:
        return {"message": "Delete Logs Successfully"}
    
@app.delete("/purchase-logs/{log_id}")
def delete_log_and_purchase (
    log_id: int,
    db: Session = Depends(get_db)
):  
    result = crud.delete_logs_and_purchases(db, log_id)
    if result == "Log not found":
        raise HTTPException(status_code=404, detail="Log not found")
    if result == "Item not found":
        raise HTTPException(status_code=404, detail="Item not found")
    if result == "Table not found":
        raise HTTPException(status_code=404, detail="Table not found")
    if result == "Purchase not found":
        raise HTTPException(status_code=404, detail="Purchase not found")
    if result is True:
        return {"message": "Deleted log and purchase successfully"}
    raise HTTPException(status_code=500, detail="Failed to delete log and purchase")

# =====================
# RESERVATION API
# =====================
@app.post("/reservations", response_model=schemas.ReservationResponse)
async def create_reservation(
    reservation: schemas.ReservationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_table = crud.get_table(db, reservation.table_id)
    if db_table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    
    db_reservation = crud.create_reservation(db, reservation)
    # 만들어 놔야 밑에서 쓸 수가 있음. reservation은 Create 객체라서 쓸 수 없음. 필요한 필드가 없을 수 있음.
    payload = schemas.TableResponse.model_validate(db_table).model_dump(mode="json")
    background_tasks.add_task
    (
        manager.broadcast,
        db_table.company_id, 
        {
            "type": "table_updated",
            "payload": payload,
        }
    )
    return db_reservation

@app.get("/reservations/{reservation_id}", response_model=schemas.ReservationResponse)
def read_reservation(
    reservation_id: int,
    db: Session = Depends(get_db)
):
    db_reservation = crud.get_reservation(db, reservation_id)
    if db_reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return db_reservation

@app.get("/tables/{table_id}/reservations", response_model=list[schemas.ReservationResponse])
def read_reservations_by_table(
    table_id: str,
    db: Session = Depends(get_db)
):
    db_reservation = crud.get_reservations_by_table(db, table_id)
    return db_reservation

@app.patch("/reservations/{reservation_id}", response_model=schemas.ReservationResponse)
async def update_reservation(
    reservation_update: schemas.ReservationUpdate,
    backgroud_tasks: BackgroundTasks,
    reservation_id: int,
    db: Session = Depends(get_db)
):
    db_reservation = crud.get_reservation(db, reservation_id)
    if db_reservation is None:
        raise HTTPException(status_code=404, detail="Reservaion not found")
    db_table = crud.get_table(db, db_reservation.table_id)
    if db_table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    result =  crud.update_reservation(db, reservation_update, reservation_id)
    payload = schemas.TableResponse.model_validate(db_table).model_dump(mode="json")
    backgroud_tasks.add_task(
        manager.broadcast,
        db_table.company_id,
        {
            "type": "table_updated",
            "payload": payload,
        }
    )
    return result


@app.delete("/reservations/{reservation_id}")
async def delete_reservation(
    reservation_id: int,
    backgroud_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    db_reservation = crud.get_reservation(db, reservation_id)
    if db_reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    company_id = db_reservation.table.company_id

    
    result = crud.delete_reservation(db, reservation_id)

    if result is False:
        raise HTTPException(status_code=404, detail="Reservation or Table not found")

    table = result
    payload = schemas.TableResponse.model_validate(table).model_dump(mode="json")
    backgroud_tasks.add_task(
        manager.broadcast,
        company_id,
        {
            "type": "table_updated",
            "payload": payload,
        }
    )

    return {"message": "Reservation deleted successfully"}

@app.post("/tables/{table_id}/register-reservation") 
async def register_reservation (
    table_id: str,
    register: schemas.ReservationInputCreate,
    backgroud_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) : 
    result = crud.register_reservation(db, register, table_id)
    if result == "Table not found":
        raise HTTPException(status_code=404, detail="Table not found")
    if result == "Table already reserved":
        raise HTTPException(status_code=409, detail="Table already reservedßß")
    if result == "Item not found":
        raise HTTPException(status_code=404, detail="Item not found")
    db_table = crud.get_table(db, table_id)
    if db_table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    payload = schemas.TableResponse.model_validate(db_table).model_dump(mode="json")
    backgroud_tasks.add_task(
        manager.broadcast,
        db_table.company_id,
        {
            "type": "table_updated",
            "payload": payload,
        }
    )
    return result
    

# =====================
# RESERVATIONPURCHASE API
# =====================
@app.post("/res-purchases", response_model=schemas.ReservationPurchaseResponse)
def create_res_purchase(
    res_purchase: schemas.ReservationPurchaseCreate,
    db: Session = Depends(get_db)
):
    db_reservation = crud.get_reservation(db, res_purchase.reservation_id)
    if db_reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    db_item = crud.get_item(res_purchase.item_id, db)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return crud.create_res_purchase(db, res_purchase)

@app.get("/res-purchases/{res_purchase_id}", response_model=schemas.ReservationPurchaseResponse)
def read_res_purchase(
    res_purchase_id: int,
    db: Session = Depends(get_db)
):
    db_res_purchase = crud.get_res_purchase(db, res_purchase_id)
    if db_res_purchase is None:
        raise HTTPException(status_code=404, detail="ReservationPurchase not found")
    return db_res_purchase

@app.get("/tables/{table_id}/res-purchases", response_model=list[schemas.ReservationPurchaseResponse])
def read_res_purchases_by_table(
    table_id: str,
    db: Session = Depends(get_db)
):
    db_table = crud.get_table(db, table_id)
    if db_table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    return crud.get_res_purchases_by_table(db, table_id)

@app.get("/reservations/{reservation_id}/res-purchases", response_model=list[schemas.ReservationPurchaseResponse])
def read_res_purchases_by_reservation(
    reservation_id: int,
    db: Session = Depends(get_db)
):
    db_reservation = crud.get_reservation(db, reservation_id)
    if db_reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return crud.get_res_purchases_by_reservation(db, reservation_id)

 
def update_res_purchase(
    res_purchase_id: int,
    res_purchase_update: schemas.ReservationPurchaseUpdate,
    db: Session = Depends(get_db)
):
    db_res_purchase = crud.get_res_purchase(db, res_purchase_id)
    if db_res_purchase is None:
        raise HTTPException(status_code=404, detail="ReservationPurchase or Item not found")
    
    return crud.update_res_purchase(db, res_purchase_id, res_purchase_update)

@app.delete("/res-purchases/{res_purchase_id}")
def delete_res_purchase(
    res_purchase_id: int,
    db: Session = Depends(get_db),
):
    db_res_purchase = crud.delete_res_purchase(db, res_purchase_id)

    if db_res_purchase is False:
        raise HTTPException(status_code=404, detail="ReservationPurchase not found")

    return {"message": "Reservation Purchase deleted successfully"}

@app.post("/reservations/{reservation_id}/check-in", response_model=schemas.TableResponse)
async def reservation_check_in (
    reservation_id: int,
    backgroud_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_reservation = crud.get_reservation(db, reservation_id)
    db_table = crud.get_table(db, db_reservation.table_id)
    if db_reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    result = crud.reservation_check_in(db, reservation_id)
    if result == "TABLE_NOT_AVAILABLE":
        raise HTTPException(status_code=400, detail="Table is not available")
    if result is None:
        raise HTTPException(status_code=404, detail="Table not found")
    payload = schemas.TableResponse.model_validate(db_table).model_dump(mode="json")
    backgroud_tasks.add_task(
        manager.broadcast,
        db_reservation.table.company_id,
        {
            "type": "table_updated",
            "payload": payload,
        }
    )
    return result

# =====================
# HISTORY API
# =====================
@app.post("/tables/{table_id}/out", response_model=schemas.TableHistoryResponse)
async def table_out(
    table_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_table = crud.get_table(db, table_id)    
    if db_table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    
    company_id = db_table.company_id
    tablename = db_table.tablename

    result = crud.table_out(db, table_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Table not found")
    if result == "TABLE_NOT_USING":
        raise HTTPException(status_code=400, detail="Table is not using")
    payload = schemas.TableResponse.model_validate(db_table).model_dump(mode="json")
    background_tasks.add_task(
        manager.broadcast,
        company_id,
        {
            "type": "table_updated",
            "payload": payload,
        }
    )
    
    background_tasks.add_task(send_table_out_pushes, company_id, table_id, tablename)

    return result

@app.get("/histories/{history_id}", response_model=schemas.TableHistoryResponse)
def read_history(
    history_id: int,
    db: Session = Depends(get_db)
):
    db_history = crud.get_history(db, history_id)
    if db_history is None:
        raise HTTPException(status_code=404, detail="History not found")
    return db_history

@app.get("/tables/{table_id}/histories", response_model=list[schemas.TableHistoryResponse])
def read_histories_by_table(
    table_id: str,
    db: Session = Depends(get_db)
):
    db_table = crud.get_table(db, table_id)
    if db_table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    return crud.get_histories_by_table(db, table_id)

@app.get("/companies/{company_id}/histories", response_model=list[schemas.TableHistoryResponse])
def read_histories_by_company(
    company_id: str,
    business_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    db_company = crud.get_company(db, company_id)
    if db_company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    target_business_date = business_date or crud.get_business_date()
    return crud.get_histories_by_company_and_business_date(
        db,
        company_id,
        target_business_date,
    )
    
# =====================
# HISTORYPURCHASE API
# =====================

@app.get("/history-purchases/{history_purchase_id}", response_model=schemas.TableHistoryPurchaseResponse)
def read_history_purchase(
    history_purchase_id: int,
    db: Session = Depends(get_db)
):
    db_history_purchase = crud.get_history_purchase(db, history_purchase_id)
    if db_history_purchase is None:
        raise HTTPException(status_code=404, detail="HistoryPurchase not found")
    return db_history_purchase

@app.get("/tables/{table_id}/history-purchases", response_model=list[schemas.TableHistoryPurchaseResponse])
def read_history_purchases_by_table(
    table_id: str,
    db: Session = Depends(get_db)
):
    db_table = crud.get_table(db, table_id)
    if db_table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    return crud.get_history_purchases_by_table(db ,table_id)

@app.get("/histories/{history_id}/history-purchases", response_model=list[schemas.TableHistoryPurchaseResponse])
def read_history_purchases_by_history(
    history_id: int,
    db: Session = Depends(get_db)
):
    db_history = crud.get_history(db, history_id)
    if db_history is None:
        raise HTTPException(status_code=404, detail="History not found")
    return crud.get_history_purchases_by_history(db ,history_id)

@app.post("/tables/{table_id}/re-register/histories/{history_id}") 
async def reregister_history(
    table_id: str,
    history_id: int,
    backgroud_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) : 
    db_table = crud.get_table(db, table_id)
    if db_table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    result = crud.reregister_table(db, history_id, table_id)
    if result == "History not found":
        raise HTTPException(status_code=404, detail="History not found")
    if result == "Table not found":
        raise HTTPException(status_code=404, detail="Table not found")
    if result == "Table already in use":
        raise HTTPException(status_code=409, detail="Table already in use")
    if result == "History already re-registered":
        raise HTTPException(status_code=409, detail="History already re-registered")
    if result is True:
        payload = schemas.TableResponse.model_validate(db_table).model_dump(mode="json")
        backgroud_tasks.add_task(
            manager.broadcast,
            db_table.company_id,
            {
                "type": "table_updated",
                "payload": payload,
            }
        )
        return {"message": "ReRegistered successfully"}
    raise HTTPException(status_code=500, detail=f"Error: {result}")

# =====================
# MOVEAPI
# =====================
@app.post("/table-move" )
async def move_table (
    from_table_id: str,
    to_table_id: str,
    backgroud_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_from_table = crud.get_table(db, from_table_id)
    if db_from_table is None: 
        raise HTTPException(status_code=404, detail="FROM TABLE NOT FOUND")
    
    db_to_table = crud.get_table(db, to_table_id)
    if db_to_table is None: 
        raise HTTPException(status_code=404, detail="TO TABLE NOT FOUND")
    
    db_company = crud.get_company(db, db_from_table.company_id)
    if db_company is None: 
        raise HTTPException(status_code=404, detail="COMPANY NOT FOUND")
    
    result = crud.moveTable(db, from_table_id, to_table_id)
    if result == "FROM TABLE NOT USING":
        raise HTTPException(status_code=422, detail="FROM TABLE NOT USING")
    if result == "TO TABLE ALREADY IN USE":
        raise HTTPException(status_code=409, detail="TO TABLE ALREADY IN USE")
    payload = schemas.TableResponse.model_validate(result).model_dump(mode="json")
    backgroud_tasks.add_task(
        manager.broadcast,
        db_company.id,
        {
            "type": "table_updated",
            "payload": payload
        }
    )
    payload = schemas.TableResponse.model_validate(db_from_table).model_dump(mode="json")
    backgroud_tasks.add_task(
        manager.broadcast,
        db_company.id,
        {
            "type": "table_updated",
            "payload": payload
        }
    )
    return {"message": "Table moved successfully"}




# =====================
# NOTIFICATION
# =====================

@app.post("/debug/push")
def debug_push(token: str):
    try:
        message_id = send_push_to_token(
            token=token,
            title="GRID 테스트 알림",
            body="푸시 알림 테스트입니다.",
            data={
                "type": "debug",
            },
        )

        return {
            "message": "Push sent",
            "message_id": message_id,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/debug/check-expired-timers")
def check_expired_timers():
    return run_expired_timer_check()

@app.get("/debug/scheduler")
def debug_scheduler():
    jobs = []

    for job in scheduler.get_jobs():
        next_run_time = job.next_run_time
        jobs.append(
            {
                "id": job.id,
                "next_run_time": next_run_time.isoformat() if next_run_time else None,
            }
        )

    return {
        "running": scheduler.running, # true / false
        "jobs": jobs,
    }

def run_expired_timer_check():
    db = SessionLocal() # 스케줄러: http 요청 아님. 그래서 직접 db 연결을 만든다.

    try:
        expired_tables = crud.get_expired_timer_tables(db)
        push_jobs = []

        for table in expired_tables:
            users = crud.get_users_by_company(db, table.company_id)
            crud.create_timer_notification(db, table)

            for user in users:
                if not user.fcmtoken or user.is_push_on is False:
                    continue

                push_jobs.append(
                    {
                        "user_id": user.id,
                        "fcmtoken": user.fcmtoken,
                        "table_id": table.id,
                        "company_id": table.company_id,
                        "tablename": table.tablename
                    }
                )
            table.timer_alert_sent_at = datetime.now(UTC)
        db.commit()
    except Exception as e:
                db.rollback()
                print(f"[Timer Check Error] {e}")

                return {
                    "expired_table_count": 0,
                    "sent_count": 0,
                    "failed_count": 0,
                    "error": str(e),
                }
    finally:
        db.close()
    
    sent_count = 0
    failed_count = 0
    invalid_user_ids = []

    for job in push_jobs:
        try:
            send_push_to_token(
                token=job['fcmtoken'],
                title="타이머 만료",
                body=f"⏰ {job['tablename']} 테이블 시간이 만료되었습니다.",
                data={
                    "type": "timer_expired",
                    "table_id": job["table_id"],
                    "company_id": job["company_id"],
                    "tablename": job["tablename"]
                },
            )
            sent_count += 1
        except Exception as e:
            failed_count += 1
            print(f"타이머 푸시 실패 user_id={user.id}: {e}")

            if is_invalid_fcm_token_error(e):
                invalid_user_ids.append(job["user_id"])
    
    clear_invalid_fcm_tokens(invalid_user_ids)    

    if expired_tables:
        print(
            f"[Timer Check] expired={len(expired_tables)}, "
            f"sent={sent_count}, failed={failed_count}"
        )

    return {
        "expired_table_count": len(expired_tables),
        "sent_count": sent_count,
        "failed_count": failed_count,
    }

@app.get("/companies/{company_id}/notifications", response_model=list[schemas.NotificationResponse])
def read_notifications_by_company(
    company_id: str,
    db: Session = Depends(get_db)
):
    db_company = crud.get_company(db, company_id)
    if db_company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return crud.get_notification_by_company(db, company_id)

def run_daily_reset():
    db = SessionLocal()
    try:
        crud.reset_daily_state(db)
        print("[Daily Reset] 완료")
    except Exception as e:
        print(f"[Daily Reset Error] {e}")
    finally:
        db.close()

start_scheduler()

# =====================
# WEBSOCKET
# =====================
@app.websocket("/ws/companies/{company_id}")
async def websocket_company(websocket: WebSocket, company_id: str):
    await manager.connect(company_id, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(company_id, websocket)

@app.get("/health")
def health():
    return {"status": "ok", "env": "staging"}


# ========================
# CACHE
# ========================
@app.get("/companies/{company_id}/menu-cache", response_model=schemas.MenuCacheResponse)
def cache_menus(
        company_id: str,
        db: Session = Depends(get_db)
):
    db_categories = crud.get_item_categories(db) # 객체 리스트 반환: itemCategory(id=1, category_name="주류", sort_order=1),
    db_items = crud.get_items_by_company(company_id, db)

    return {
        "company_id": company_id,
        "categories": db_categories,
        "items": db_items,
        "version": datetime.now(UTC)
    }
# ========================
# TOKEN
# ========================
def is_invalid_fcm_token_error(error: Exception) -> bool:
    message = str(error)

    return (
        "NotRegistered" in message
        or "Requested entity was not found" in message
        or "Request contains an invalid argument" in message
    )

def clear_invalid_fcm_tokens(user_ids: list[str]):
    if not user_ids:
        return

    db = SessionLocal()
    try:
        users = db.query(models.User).filter(models.User.id.in_(user_ids)).all()

        for user in users:
            user.fcmtoken = None

        db.commit()
    finally:
        db.close()
