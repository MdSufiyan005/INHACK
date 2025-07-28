
from sqlalchemy import Column, Integer, String, DateTime
from db.database import Base
from datetime import datetime

class Vendor(Base):
    '''
    This table stores vendor information.
    '''
    __tablename__ = 'vendors'

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    Name = Column(String, nullable=False)
    PhoneNumber = Column(String, nullable=False)
    Location = Column(String, nullable=False)
    BusinessInfo = Column(String, nullable=False)
    session_id = Column(String, nullable=True, index=True)  # Add session_id for authentication
    
# from sqlalchemy import Column, Integer, String, DateTime
# from db.database import Base
# from datetime import datetime


# class Vendor(Base):
#     '''
#     This Table PurchaseTable will be used by the vendor to add the items he/she has bought for running the shop.
#     '''
#     __tablename__ = 'vendors'

#     id = Column(Integer, primary_key=True, index=True)
#     created_at = Column(DateTime, default=datetime.utcnow)
#     Name = Column(String, nullable=False)
#     PhoneNumber = Column(String, nullable=False)  # <-- Make sure this is String
#     Location = Column(String, nullable=False)
#     BusinessInfo = Column(String, nullable=False)

