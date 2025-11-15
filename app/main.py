from fastapi import FastAPI, HTTPException, status, Depends, Response
from .database import SessionLocal, engine
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from .schemas import(
    ConCreate, ConRead
)
from .models import ConsignmentDB, Base

app = FastAPI()

# Uncomment this line to reset DB
#Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

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
def get_con_by_number(id: int, db: Session = Depends(get_db)):
    stmt = select(ConsignmentDB).where(ConsignmentDB.id==id)
    con = db.execute(stmt).scalar_one_or_none()
    if not con:
        raise HTTPException(status_code=404, detail="Consignment not found")
    return con

#Create Consignment
@app.post("/api/consignment", response_model=ConRead, status_code=201)
def create_create(con: ConCreate, db: Session = Depends(get_db)):
    con = ConsignmentDB(**con.model_dump())
    db.add(con)
    commit_or_rollback(db, "Consignment creation failed")
    db.refresh(con)
    return con


    
