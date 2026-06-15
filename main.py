from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models
import crud
import schemas
from database import engine, get_db
from typing import Optional

# 서버 실행 시 DB 테이블 자동 생성 (grid.db에 뼈대 구축)
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# =====================
# Company API
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
# User API
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
    if db_company is None:
        raise HTTPException(status_code=404, detail="Company not found")
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

# =====================
# Table API
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
    
@app.get("/table-groups/{group_id}/tables", response_model=list[schemas.TableResponse])
def read_tables_by_group(
    group_id: str,
    db: Session = Depends(get_db)  
):
    return crud.get_tables_by_group(db, group_id)

@app.patch("/tables/{table_id}", response_model=schemas.TableResponse)
def update_table(
    table_id: str,
    table_update: schemas.TableUpdate,
    db: Session = Depends(get_db)
):
    db_table = crud.update_table(db, table_update, table_id)
    db_user = crud.get_user(db, table_update.user_id)
    # db_group = crud.get
    if db_table is None:
        raise HTTPException(status_code=404, detail="Table not found")
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
# Category API
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
# Item API
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
    db_category = crud.get_item_category(db, item_update.category_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_item

# =====================
# Purchase API
# =====================
@app.post("/purchases", response_model=schemas.TablePurchaseResponse)
def create_purchase(
    purchase: schemas.TablePurchaseCreate,
    db: Session = Depends(get_db)
):
    #FK check
    db_table = crud.get_table(db, purchase.table_id)
    db_item = crud.get_item(purchase.item_id, db)

    if db_table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return crud.create_purchase(db, purchase)

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
# TablePurchaseLog API
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
# Reservation API
# =====================
@app.post("/reservations", response_model=schemas.ReservationResponse)
def create_reservation(
    reservation: schemas.ReservationCreate,
    db: Session = Depends(get_db)
):
    db_table = crud.get_table(db, reservation.table_id)
    if db_table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    return crud.create_reservation(db, reservation)

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
def update_reservation(
    reservation_update: schemas.ReservationUpdate,
    reservation_id: int,
    db: Session = Depends(get_db)
):
    db_reservation = crud.get_reservation(db, reservation_id)
    if db_reservation is None:
        raise HTTPException(status_code=404, detail="Reservaion not found")
    return crud.update_reservation(db, reservation_update, reservation_id)

@app.delete("/reservations/{reservation_id}")
def delete_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
):
    db_reservation = crud.delete_reservation(db, reservation_id)

    if db_reservation is False:
        raise HTTPException(status_code=404, detail="Reservation or Table not found")

    return {"message": "Reservation deleted successfully"}

@app.post("/tables/{table_id}/register-reservation") 
def register_reservation (
    table_id: str,
    register: schemas.ReservationInputCreate,
    db: Session = Depends(get_db)
) : 
    result = crud.register_reservation(db, register, table_id)
    if result == "Table not found":
        raise HTTPException(status_code=404, detail="Table not found")
    if result == "Table already reserved":
        raise HTTPException(status_code=409, detail="Table already reservedßß")
    if result == "Item not found":
        raise HTTPException(status_code=404, detail="Item not found")
    return result
    

# =====================
# ReservationPurchase API
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
def reservation_check_in (
    reservation_id: int,
    db: Session = Depends(get_db)
):
    db_reservation = crud.get_reservation(db, reservation_id)
    if db_reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    result = crud.reservation_check_in(db, reservation_id)
    if result == "TABLE_NOT_AVAILABLE":
        raise HTTPException(status_code=400, detail="Table is not available")
    if result is None:
        raise HTTPException(status_code=404, detail="Table not found")
    return result

# =====================
# History API
# =====================
@app.post("/tables/{table_id}/out", response_model=schemas.TableHistoryResponse)
def table_out(
    table_id: str,
    db: Session = Depends(get_db)
):
    db_table = crud.get_table(db, table_id)
    if db_table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    result = crud.table_out(db, table_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Table not found")
    if result == "TABLE_NOT_USING":
        raise HTTPException(status_code=400, detail="Table is not using")
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
    
# =====================
# HistoryPurchase API
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
def reregister_history(
    table_id: str,
    history_id: int,
    db: Session = Depends(get_db)
) : 
    result = crud.reregister_table(db, history_id, table_id)
    if result == "History not found":
        raise HTTPException(status_code=404, detail="History not found")
    if result == "No historypurchase found":
        raise HTTPException(status_code=404, detail="No historypurchase found")
    if result == "Table not found":
        raise HTTPException(status_code=404, detail="Table not found")
    if result == "Table already in use":
        raise HTTPException(status_code=409, detail="Table already in use")
    if result is True:
        return {"message": "ReRegistered successfully"}
    raise HTTPException(status_code=500, detail=f"Error: {result}")