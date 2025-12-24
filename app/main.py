
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from .database import SessionLocal, engine
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from .schemas import(
    ConCreate, ConRead,
    ConEdit, ConList
)
from .models import ConsignmentDB, Base
from .pdf_generator import generate_label_pdf
from .utils.account_validator import validate_account_exists
from .utils.get_next_con import get_next_con_num


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # dev-friendly; tighten in prod
    allow_methods=["*"],
    allow_headers=["*"],
)

# Uncomment this line to reset DB
#Base.metadata.drop_all(bind=engine)
#Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def commit_or_rollback(db: Session, error_msg: str):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

@app.get("/health")
def health():
    return {"status" : "ok"}

#Get all consignments
@app.get("/api/consignment", response_model=list[ConRead])
def list_cons(db: Session = Depends(get_db)):
    stmt = select(ConsignmentDB).order_by(ConsignmentDB.id)
    return db.execute(stmt).scalars().all()


#Get consignments by con number, id for now
@app.get("/api/consignment/{id}", response_model=ConRead)
def get_con_by_id(id: int, db: Session = Depends(get_db)):
    stmt = select(ConsignmentDB).where(ConsignmentDB.id==id)
    con = db.execute(stmt).scalar_one_or_none()
    if not con:
        raise HTTPException(status_code=404, detail="Consignment not found")
    return con

#Get consignments by con number
@app.get("/api/consignment/by-number/{consignment_number}", response_model=ConRead)
def get_con_by_number(consignment_number: int, db: Session = Depends(get_db)):
    stmt = select(ConsignmentDB).where(ConsignmentDB.consignment_number==consignment_number)
    con = db.execute(stmt).scalar_one_or_none()
    if not con:
        raise HTTPException(status_code=404, detail="Consignment not found")
    return con


#Get all cons from a particular account 
@app.get("/api/consignment/account/{account_no}", response_model=ConList)
async def list_con_for_account(account_no: str, db: Session = Depends(get_db)):
    validate_account_exists(account_no)
    stmt = (select(ConsignmentDB.consignment_number)
            .where(ConsignmentDB.account_no == account_no)
            .order_by(ConsignmentDB.consignment_number))
    con = db.execute(stmt).scalars().all()
    if not con: 
         raise HTTPException(status_code=404, detail="No Consignments found for this account")
    return {
        "account_no": account_no,
        "consignments": con
    }


#Create Consignment
@app.post("/api/consignment", response_model=ConRead, status_code=201)
async def create_con(con: ConCreate, db: Session = Depends(get_db)):
    #Check if account exists
    validate_account_exists(con.account_no)

    #get next con number
    next_num = await get_next_con_num(con.account_no)
    
    con_db = ConsignmentDB(
        **con.model_dump(),
        consignment_number=next_num
    )

    db.add(con_db)
    commit_or_rollback(db, "Consignment creation failed")
    db.refresh(con_db)
    # Generate PDF label
    generate_label_pdf(con_db)
    return con_db

#Patch Consignment 
@app.patch("/api/consignment/{id}", response_model=ConRead)
def edit_consignment(id: int, payload: ConEdit, db: Session = Depends(get_db)):
    stmt = select(ConsignmentDB).where(ConsignmentDB.id==id)
    con = db.execute(stmt).scalar_one_or_none()
    if not con:
        raise HTTPException(status_code=404, detail="Consignment not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(con, key, value)
    commit_or_rollback(db, "Invalid Consignment Details")
    db.refresh(con)
    return con

    
#Delete Consignment
@app.delete("/api/consignment/{id}", status_code=204)
def delete_consignment(id: int, db: Session = Depends(get_db)):
    con = db.get(ConsignmentDB, id)
    if not con:
        raise HTTPException(status_code=404, detail="Consignment not found")
    db.delete(con)
    db.commit()
