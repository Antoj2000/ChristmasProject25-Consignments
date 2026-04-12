
from contextlib import asynccontextmanager
from datetime import date, timedelta
from typing import List, Optional, Tuple


from fastapi import FastAPI, HTTPException, Query ,status, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from .database import SessionLocal, engine
from sqlalchemy import select, and_ as sql_and
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
from .utils.gazzing import resolve_depot_number
from .security import get_current_account_claims


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
    
def compute_status(expected_date: date) -> Tuple[str, str]:
    """Determine a parcel's status based on its expected delivery date.

    * **IN_TRANSIT** – ``expected_date`` is after today.
    * **OUT_FOR_DELIVERY** – ``expected_date`` is today.
    * **DELIVERED** – ``expected_date`` is before today.

    The returned tuple contains the internal status code and a
    human‑friendly label suitable for display on the frontend.
    """
    today = date.today()
    if expected_date > today:
        return ("IN_TRANSIT", "In Transit")
    if expected_date == today:
        return ("OUT_FOR_DELIVERY", "Out for Delivery")
    return ("DELIVERED", "Delivered")

def to_con_read(con: ConsignmentDB) -> ConRead:
    """Serialise a database model into a ``ConRead`` response model.

    In addition to copying the database fields, this helper computes
    status information so that API consumers do not need to derive it
    themselves.
    """
    status_code, status_display = compute_status(con.expected_delivery_date)
    return ConRead(
        id=con.id,
        account_no=con.account_no,
        name=con.name,
        sender_name=con.sender_name,
        addressline1=con.addressline1,
        addressline2=con.addressline2,
        addressline3=con.addressline3,
        addressline4=con.addressline4,
        eircode=con.eircode,
        consignment_number=con.consignment_number,
        delivery_depot=con.delivery_depot,
        weight=con.weight,
        shipped_at=con.shipped_at,
        expected_delivery_date=con.expected_delivery_date,
        status=status_code,
        statusDisplay=status_display,
    )

@app.get("/health")
def health():
    return {"status" : "ok"}

#Get all consignments
@app.get("/api/consignment", response_model=List[ConRead])
def list_cons(db: Session = Depends(get_db)) -> List[ConRead]:
    """Return all consignments with computed status information."""
    stmt = select(ConsignmentDB).order_by(ConsignmentDB.id)
    consignments = db.execute(stmt).scalars().all()
    return [to_con_read(c) for c in consignments]

@app.get("/api/consignment/{consignment_number}", response_model=ConRead)
def get_con_by_number(
    consignment_number: int,
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_account_claims),
) -> ConRead:
    """Retrieve a consignment by its tracking number and compute status."""
    stmt = select(ConsignmentDB).where(
        ConsignmentDB.consignment_number == consignment_number
    )
    con = db.execute(stmt).scalar_one_or_none()
    if not con:
        raise HTTPException(status_code=404, detail="Consignment not found")
    token_account_no = claims.get("account_no")
    if not token_account_no or token_account_no != con.account_no:
        raise HTTPException(
            status_code=403,
            detail="Token not valid for this account",
        )
    return to_con_read(con)


#Get all cons from a particular account 
@app.get("/api/consignment/account/{account_no}", response_model=ConList)
async def list_con_for_account(
    account_no: str,
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_account_claims),
) -> ConList:
    """List consignment numbers for an account (unchanged behaviour)."""
    token_account_no = claims.get("account_no")
    if not token_account_no or token_account_no != account_no:
        raise HTTPException(
            status_code=403,
            detail="Token not valid for this account",
        )
    validate_account_exists(account_no)
    stmt = (
        select(ConsignmentDB.consignment_number)
        .where(ConsignmentDB.account_no == account_no)
        .order_by(ConsignmentDB.consignment_number)
    )
    con_numbers = db.execute(stmt).scalars().all()
    if not con_numbers:
        raise HTTPException(
            status_code=404,
            detail="No Consignments found for this account",
        )
    return ConList(account_no=account_no, consignments=con_numbers)

@app.get("/api/parcels/account/{account_no}", response_model=List[ConRead])
async def list_parcels_for_account(
    account_no: str,
    delivery_date: Optional[date] = Query(
        None,
        description=(
            "Filter parcels expected on this date; if omitted, tomorrow is used"
        ),
    ),
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_account_claims),
) -> List[ConRead]:
    """Return full parcel details for a given account and delivery date.

    This endpoint supports the frontend's status filter.  When
    ``delivery_date`` is omitted, it defaults to tomorrow (i.e. one day
    after today's date).  Only consignments matching the account and
    delivery date are returned; a 404 is raised if none are found.
    """
    token_account_no = claims.get("account_no")
    if not token_account_no or token_account_no != account_no:
        raise HTTPException(
            status_code=403,
            detail="Token not valid for this account",
        )
    validate_account_exists(account_no)
    if delivery_date is None:
        delivery_date = date.today() + timedelta(days=1)
    stmt = (
        select(ConsignmentDB)
        .where(
            sql_and(
                ConsignmentDB.account_no == account_no,
                ConsignmentDB.expected_delivery_date == delivery_date,
            )
        )
        .order_by(ConsignmentDB.consignment_number)
    )
    consignments = db.execute(stmt).scalars().all()
    if not consignments:
        raise HTTPException(
            status_code=404,
            detail="No consignments found for this account on the specified date",
        )
    return [to_con_read(c) for c in consignments]


#Create Consignment
@app.post("/api/consignment", response_model=ConRead, status_code=201)
async def create_con(con: ConCreate, db: Session = Depends(get_db)):
    """Create a consignment without authentication (e.g. admin access)."""
    validate_account_exists(con.account_no)
    # Determine next tracking number and delivery depot asynchronously
    next_num = await get_next_con_num(con.account_no)
    depot_number = await resolve_depot_number(con.addressline4)
    # Determine expected delivery date (default tomorrow)
    if con.expected_delivery_date is not None:
        expected = con.expected_delivery_date
    else:
        expected = date.today() + timedelta(days=1)
    # Build the DB object without expected_delivery_date to avoid duplication
    payload = con.model_dump(exclude={"expected_delivery_date"})
    sender_name = payload.pop("sender_name", None) or "Amazon"
    con_db = ConsignmentDB(
        **payload,
        sender_name=sender_name,
        shipped_at=date.today(),
        consignment_number=next_num,
        delivery_depot=depot_number,
        expected_delivery_date=expected,
    )
    db.add(con_db)
    commit_or_rollback(db, "Consignment creation failed")
    db.refresh(con_db)
    generate_label_pdf(con_db)
    return to_con_read(con_db)

#Create Consignment w Auth
@app.post("/api/consignment/auth", response_model=ConRead, status_code=201)
async def create_con(con: ConCreate, db: Session = Depends(get_db), claims: dict = Depends(get_current_account_claims)):
    
    token_account_no = claims.get("account_no")
    if not token_account_no or token_account_no != con.account_no:
        raise HTTPException(
            status_code=403,
            detail="Token not valid for this account",
        )
    
    #Check if account exists
    validate_account_exists(con.account_no)

    #get next con number
    next_num = await get_next_con_num(con.account_no)
    #Get depot number
    depot_number = await resolve_depot_number(con.addressline4)
    if con.expected_delivery_date is not None:
        expected = con.expected_delivery_date
    else:
        expected = date.today() + timedelta(days=1)
    
    payload = con.model_dump(exclude={"expected_delivery_date"})
    sender_name = payload.pop("sender_name", None) or "Amazon"
    con_db = ConsignmentDB(
        **payload,
        sender_name=sender_name,
        shipped_at=date.today(),
        consignment_number=next_num,
        delivery_depot=depot_number,
        expected_delivery_date=expected,
    )
    db.add(con_db)
    commit_or_rollback(db, "Consignment creation failed")
    db.refresh(con_db)
    generate_label_pdf(con_db)
    return to_con_read(con_db)
    

#Patch Consignment 
@app.patch("/api/consignment/{consignment_number}", response_model=ConRead)
async def edit_consignment(
    consignment_number: int,
    payload: ConEdit,
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_account_claims),
) -> ConRead:
    """Edit an existing consignment.

    Any field provided in ``payload`` will be updated.  If the
    ``addressline4`` (county) changes, the delivery depot is
    re‑calculated.  Similarly, the ``expected_delivery_date`` is
    updated when present.  The updated consignment is returned with
    computed status information.
    """
    stmt = select(ConsignmentDB).where(
        ConsignmentDB.consignment_number == consignment_number
    )
    con = db.execute(stmt).scalar_one_or_none()
    if not con:
        raise HTTPException(
            status_code=404,
            detail="Consignment not found",
        )
    token_account_no = claims.get("account_no")
    if not token_account_no or token_account_no != con.account_no:
        raise HTTPException(
            status_code=403,
            detail="Token not valid for this account",
        )
    updates = payload.model_dump(exclude_unset=True)
    # If county/addressline4 is changed, re‑evaluate the delivery depot
    if "addressline4" in updates:
        new_county = updates["addressline4"]
        depot_number = await resolve_depot_number(new_county)
        con.delivery_depot = depot_number
    # Apply simple attribute updates (including expected_delivery_date)
    for key, value in updates.items():
        setattr(con, key, value)
    commit_or_rollback(db, "Invalid Consignment Details")
    db.refresh(con)
    generate_label_pdf(con)
    return to_con_read(con)
    
#Delete Consignment
@app.delete("/api/consignment/{consignment_number}", status_code=204)
def delete_consignment(consignment_number: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_account_claims)):
    stmt = select(ConsignmentDB).where(ConsignmentDB.consignment_number == consignment_number)
    con = db.execute(stmt).scalar_one_or_none()
    if not con:
        raise HTTPException(
            status_code=404, 
            detail="Consignment not found"
            )
    token_account_no = claims.get("account_no")
    if not token_account_no or token_account_no != con.account_no:
        raise HTTPException(
            status_code=403,
            detail="Token not valid for this account",
            )
    db.delete(con)
    db.commit()
    
