# app/schemas.py
from pydantic import BaseModel, EmailStr, constr, conint, field_validator, StringConstraints, Field
from typing import Annotated, Optional, List
from annotated_types import Ge, Le


# ------- Resuseable Type Aliases -------

#ConInt
AccountStr = Annotated[str, StringConstraints(pattern=r'^A\d{5}$')]
NameStr = Annotated[str, StringConstraints(min_length=3, max_length=30)]
AddLine1Str = Annotated[str, StringConstraints(min_length=2, max_length=30)]
AddLine2Str = Annotated[str, StringConstraints(min_length=2, max_length=30)]
AddLine3Str = Annotated[str, StringConstraints(min_length=2, max_length=30)]
AddLine4Str = Annotated[str, StringConstraints(min_length=2, max_length=30)]
WeightInt = Annotated[int, Ge(1), Le(30)]
#eircode
#country

class ConCreate(BaseModel):
    account_no: AccountStr
    name: NameStr
    addressline1: AddLine1Str
    addressline2: Optional[AddLine2Str] = None
    addressline3: AddLine3Str
    addressline4: AddLine4Str
    #eircode
    weight: WeightInt

class ConRead(BaseModel):
    id: int #con number will be used soon
    account_no: AccountStr
    name: NameStr
    addressline1: AddLine1Str
    addressline2: Optional[AddLine2Str] = None
    addressline3: AddLine3Str
    addressline4: AddLine4Str
    #eircode
    #delivery depot
    weight: WeightInt


class ConEdit(BaseModel):
    name: Optional[NameStr] = None
    addressline1: Optional [AddLine1Str] = None
    addressline2: Optional[AddLine2Str] = None
    addressline3: Optional[AddLine3Str] = None
    addressline4: Optional[AddLine4Str] = None
    #eircode
    weight: Optional[WeightInt] = None

