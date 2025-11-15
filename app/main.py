from fastapi import FastAPI, HTTPException, status, Depends, Response
from .database import SessionLocal, engine
from sqlalchemy import select


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