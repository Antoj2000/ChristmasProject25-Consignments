
import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, Date

class Base(DeclarativeBase):
    pass


class ConsignmentDB(Base):
    __tablename__ = "consignments"

    id: Mapped[int] = mapped_column(primary_key=True)

    account_no: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(unique=False, nullable=False)
    sender_name: Mapped[str] = mapped_column(String(50), nullable=False, default="Amazon")

    addressline1: Mapped[str] = mapped_column(String(30), nullable=False)
    addressline2: Mapped[str] = mapped_column(String(30), nullable=True)
    addressline3: Mapped[str] = mapped_column(String(30), nullable=False)
    addressline4: Mapped[str] = mapped_column(String(30), nullable=False)
    eircode: Mapped[str] = mapped_column(String(8), nullable=False)
    
    weight: Mapped[int] = mapped_column(Integer, nullable=False)
    consignment_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    delivery_depot: Mapped[int] = mapped_column(Integer, nullable=False)

    shipped_at: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    expected_delivery_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    
    