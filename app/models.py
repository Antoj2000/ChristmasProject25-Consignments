from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey

class Base(DeclarativeBase):
    pass


class ConsignmentDB(Base):
    __tablename__ = "consignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_no: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String(6), unique=False, nullable=False)
    addressline1: Mapped[str] = mapped_column(String(30), nullable=False)
    addressline2: Mapped[str] = mapped_column(String(30), nullable=True)
    addressline3: Mapped[str] = mapped_column(String(30), nullable=False)
    addressline4: Mapped[str] = mapped_column(String(30), nullable=False)
    weight: Mapped[int] = mapped_column(Integer, nullable=False)
    consignment_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    #eircode
    #country
    #deliverydepot