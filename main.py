from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models
import schemas
from database import engine, get_db

# 서버 실행 시 DB 테이블 자동 생성 (grid.db에 뼈대 구축)
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# 새 테이블 생성 (POST)
# _repo.createTable 
@app.post("/tables", response_model=schemas.TableResponse)
def create_table(table_data: schemas.TableCreate, db: Session = Depends(get_db)):
    # 전달받은 tid가 이미 존재하는지 안전 검사 (중복 생성 방지)
    existing_table = db.query(models.TableMaster).filter(models.TableMaster.tid == table_data.tid).first()
    if existing_table:
        raise HTTPException(status_code=400, detail="이미 존재하는 테이블 ID입니다.")

    # schemas를 통과한 데이터를 models(DB 모델)로 변환
    # **table_data.model_dump()는 딕셔너리 형태로 쫙 풀어주는 마법의 문법입니다.
    new_table = models.TableMaster(**table_data.model_dump())
    
    # DB에 추가하고 저장(Commit)
    db.add(new_table)
    db.commit()
    db.refresh(new_table) # DB에서 생성시간(created_at) 등을 찍어서 다시 가져옴
    
    return new_table

# 특정 업장 & 섹션의 테이블 목록 조회 (GET)
@app.get("/tables", response_model=List[schemas.TableResponse])
def get_tables(company_id: str, section: str, db: Session = Depends(get_db)):
    # SQL 쿼리: SELECT * FROM table_masters WHERE company_id = ? AND section = ?
    tables = db.query(models.TableMaster).filter(
        models.TableMaster.company_id == company_id,
        models.TableMaster.section == section
    ).all()
    
    return tables

# 테이블 이동 (POST) - 트랜잭션 및 동시성 제어 완벽 적용
@app.post("/tables/move", response_model=schemas.TableResponse)
def move_table(move_data: schemas.TableMove, db: Session = Depends(get_db)):
    
    # 출발지(from)와 도착지(to) 테이블을 DB에서 꺼냄
    # .with_for_update() : 내가 이 데이터를 수정하는 동안 다른 알바생이 절대 건드리지 못하게 DB 잠금
    from_table = db.query(models.TableMaster).filter(models.TableMaster.tid == move_data.from_tid).with_for_update().first()
    to_table = db.query(models.TableMaster).filter(models.TableMaster.tid == move_data.to_tid).with_for_update().first()

    # 출발 테이블이 실제로 존재하는지 검사
    if not from_table or not to_table:
        raise HTTPException(status_code=404, detail="테이블을 찾을 수 없습니다.")

    # 도착지 테이블이 비어있는지 검사
    if to_table.status != "available":
        raise HTTPException(status_code=400, detail="ALREADY_IN_USE")

    # 데이터 이동
    to_table.status = "inuse"
    to_table.customer = from_table.customer
    to_table.phonenumber = from_table.phonenumber
    to_table.staff = from_table.staff
    to_table.bottle = from_table.bottle
    to_table.remark = from_table.remark
    to_table.persons = from_table.persons

    # 출발 테이블 빈 자리로 만들기
    from_table.status = "available"
    from_table.customer = ""
    from_table.phonenumber = ""
    from_table.staff = ""
    from_table.bottle = ""
    from_table.remark = ""
    from_table.persons = 0

    # DB에 확정 (Commit) - 이 순간 두 테이블의 변경사항이 '동시에' 저장되고 잠금 해제
    db.commit()
    db.refresh(to_table)

    return to_table

# 합석 (POST)
@app.post("/tables/join", response_model=List[schemas.TableResponse])
def join_tables(join_data: schemas.TableJoin, db: Session = Depends(get_db)):
    # 마스터 테이블 가져오기
    master = db.query(models.TableMaster).filter(models.TableMaster.tid == join_data.master_tid).first()
    if not master:
        raise HTTPException(status_code=404, detail="마스터 테이블을 찾을 수 없습니다.")

    # 슬레이브 테이블들 가져오기
    slaves = db.query(models.TableMaster).filter(models.TableMaster.tid.in_(join_data.slave_tids)).all()
    
    # 마스터 설정
    master.group_id = master.tid
    master.is_master = True

    # 슬레이브들에게 마스터 정보 상속 (플러터 로직 그대로)
    for slave in slaves:
        slave.group_id = master.tid
        slave.is_master = False
        slave.master_tablenumber = master.tablename
        slave.status = "inuse"
        # 정보 복사
        slave.customer = master.customer
        slave.phonenumber = master.phonenumber
        slave.staff = master.staff
        slave.bottle = master.bottle
        slave.persons = master.persons
        slave.remark = f"{master.tablename}번 합석"

    db.commit()
    return [master] + slaves

#  합석 해제 (POST)
@app.post("/tables/unjoin")
def unjoin_tables(unjoin_data: schemas.TableUnjoin, db: Session = Depends(get_db)):
    # 해당 그룹에 속한 모든 테이블 조회
    group_tables = db.query(models.TableMaster).filter(models.TableMaster.group_id == unjoin_data.group_id).all()

    for table in group_tables:
        table.group_id = None
        table.is_master = False
        table.master_tablenumber = None
    

    db.commit()
    return {"message": "합석이 성공적으로 해제되었습니다."}