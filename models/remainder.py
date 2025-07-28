# from sqlalchemy import Column, Integer, String, Float,DateTime,Enum
# from sqlalchemy.sql import func
# from db.database import Base
# import enum


# class ModeEnum(str,enum.Enum):
#     Online = "online"
#     Cash ="Cash"

# class Remind_Me(Base):
#     '''
#     This Model is for the vendor ,where he/she wants to get remainded of the payment they want to do to the supplier 
#     and the remainder will be through whatsapp/SMS. the Vendor will add the necessary details like the items name,the amount,
#     the name of the person to whom the payment is to be made and at what time and date the payment is scheduled.
#     '''
#     __tablename__ = 'Remind_me'

#     id = Column(Integer, primary_key=True, index=True)
#     Date_Time = Column(DateTime(timezone=True))
#     item_name = Column(String, nullable=False,index=True)
#     Amount = Column(Float, nullable=False)
#     ToWhom = Column(String,nullable=False,index=True)
#     phone_number = Column(String(15),nullable=False)
#     payment_method = Column(Enum(ModeEnum), nullable=False)
#     pending = Column(String, default="pending")
    
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base
import enum

# models/remainder.py
class ModeEnum(str, enum.Enum):
    Online = "Online"
    Cash = "Cash"
    
class Remind_Me(Base):
    __tablename__ = "remind_me"

    id = Column(Integer, primary_key=True, index=True)
    Date_Time = Column(DateTime(timezone=True), nullable=False)
    item_name = Column(String, nullable=False, index=True)
    Amount = Column(Float, nullable=False)
    ToWhom = Column(String, nullable=False, index=True)
    phone_number = Column(String(15), nullable=False)  # vendor's phone
    supplier_phone_number = Column(String(15), nullable=False)
    payment_method = Column(SAEnum(ModeEnum), nullable=False)
    status = Column(String(10), default="pending", nullable=False)
    vendor_id = Column(Integer, ForeignKey('vendors.id'), nullable=False)  # Add foreign key