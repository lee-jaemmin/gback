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
    company: schemas.CompanyCreate, 
    db: Session = Depends(get_db),
    ):
    db_company = crud.get_company(db, company.id)

    if db_company is not None:
        raise HTTPException(status_code=400, detail="Company already exists")
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

# =====================
# User API
# =====================

@app.post("/users", response_model=schemas.UserResponse)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    db_user = crud.get_user(db, user.id)

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

# =====================
# Table API
# =====================

@app.post("/tables", response_model=schemas.TableResponse)
def create_table(
    table: schemas.TableCreate,
    db: Session = Depends(get_db)
):
    db_table = crud.get_table(db, table.id)

    if db_table is not None:
        raise HTTPException(status_code=400, detail="Table alreay exists")
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
    if db_table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    return db_table

# =====================
# Category
# =====================
@app.post("/categories", response_model=schemas.ItemCategoryResponse)
def create_category(
    category: schemas.ItemCategoryCreate,
    db: Session = Depends(get_db)
):
    db_category = crud.get_item_category(db)
    if db_category is not None:
        raise HTTPException(status_code=400, detail="Category already exists")
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