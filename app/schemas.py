# app/schemas.py
from datetime import date
from pydantic import BaseModel, EmailStr, constr, conint, field_validator, StringConstraints, Field
from typing import Annotated, Optional, List
from annotated_types import Ge, Le


# ------- Resuseable Type Aliases -------

#ConInt
AccountStr = Annotated[str, StringConstraints(pattern=r'^A\d{5}$')]
NameStr = Annotated[str, StringConstraints(min_length=3, max_length=30)]
SenderStr = Annotated[str, StringConstraints(min_length=2, max_length=50)]
AddLine1Str = Annotated[str, StringConstraints(min_length=2, max_length=30)]
AddLine2Str = Annotated[str, StringConstraints(min_length=2, max_length=30)]
AddLine3Str = Annotated[str, StringConstraints(min_length=2, max_length=30)]
AddLine4Str = Annotated[str, StringConstraints(min_length=2, max_length=30)]
WeightInt = Annotated[int, Ge(1), Le(30)]
# Irish Eircode in standard format such as "D02 XY76".
EircodeStr = Annotated[
    str,
    StringConstraints(
        pattern=r"^[AC-FHKNPRTV-Y][0-9]{2}\s?[AC-FHKNPRTV-Y0-9]{4}$",
        min_length=7,
        max_length=8,
    ),
]
#country

class ConCreate(BaseModel):
    account_no: AccountStr
    name: NameStr
    sender_name: Optional[SenderStr] = Field(
    "Amazon",
    description="Sender name. Defaults to Amazon if omitted.",
)
    

    addressline1: AddLine1Str
    addressline2: Optional[AddLine2Str] = None
    addressline3: AddLine3Str
    addressline4: AddLine4Str


    eircode: EircodeStr
    weight: WeightInt
    expected_delivery_date: Optional[date] = Field(
        None,
        description="Expected delivery date in YYYY‑MM‑DD format.  If omitted, defaults to tomorrow.",
    )

class ConRead(BaseModel):
    id: int #con number will be used soon
    account_no: AccountStr
    name: NameStr
    sender_name: SenderStr
    addressline1: AddLine1Str
    addressline2: Optional[AddLine2Str] = None
    addressline3: AddLine3Str
    addressline4: AddLine4Str
    consignment_number: int
    eircode: EircodeStr
    delivery_depot: int
    weight: WeightInt
    shipped_at: date
    expected_delivery_date: date
    status: str
    statusDisplay: str


class ConEdit(BaseModel):
    account_no: AccountStr
    name: Optional[NameStr] = None
    addressline1: Optional [AddLine1Str] = None
    addressline2: Optional[AddLine2Str] = None
    addressline3: Optional[AddLine3Str] = None
    addressline4: Optional[AddLine4Str] = None
    eircode: Optional[EircodeStr] = None
    weight: Optional[WeightInt] = None
    expected_delivery_date: Optional[date] = None


class ConList(BaseModel):
    account_no: AccountStr
    consignments: List[int]

