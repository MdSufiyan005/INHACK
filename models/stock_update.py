from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.sql import func
from db.database import Base
import enum

class ModeEnum(str, enum.Enum):
    Online = "online"
    Cash = "Cash"

class PurchaseTable(Base):
    '''
    This Table PurchaseTable will be used by the vendor to add the items he/she has bought for running the shop.
    '''
    __tablename__ = 'purchase_table'

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    item_name = Column(String, nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    payment_method = Column(Enum(ModeEnum), nullable=False)
    vendor_id = Column(Integer, ForeignKey('vendors.id'), nullable=False)  # Add vendor_id

class SellingTable(Base):
    '''
    This Table will be storing the details like the item/goods sold by the vendor to the consumer.
    '''
    __tablename__ = 'selling_table'

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime(timezone=True), server_default=func.now())
    item_name = Column(String, nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False)
    payment_method = Column(Enum(ModeEnum), nullable=False)
    vendor_id = Column(Integer, ForeignKey('vendors.id'), nullable=False)  # Add vendor_id


# # Purchase_table
# #     ID 
# #     Item_Name
# #     Quantity
# #     Price
# #     Payment_Method

# # Selling_Table
# #     Item_Name
# #     Quantity
# #     Total_Price
# #     Payment_Method (Online, Cash)

# from sqlalchemy import Column, Integer, String, Float, ForeignKey,DateTime,Enum
# from sqlalchemy.sql import func
# from db.database import Base
# import enum

# class ModeEnum(str,enum.Enum):
#     Online = "online"
#     Cash ="Cash"

# class PurchaseTable(Base):
#     '''
#     This Table PurchaseTable will be used by the vendor to add the items he/she has bought for running the shop.
#     '''
#     __tablename__ = 'purchase_table'

#     id = Column(Integer, primary_key=True, index=True)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     item_name = Column(String, nullable=False,index=True)
#     quantity = Column(Integer, nullable=False)
#     price = Column(Float, nullable=False)
#     payment_method = Column(Enum(ModeEnum), nullable=False)
    

# class SellingTable(Base):
#     '''
#     This Table will be storing the details like the item/goods sold by the vendor to the consumer.
#     '''
#     __tablename__ = 'selling_table'

#     id = Column(Integer, primary_key=True, index=True)
#     date = Column(DateTime(timezone=True), server_default=func.now())
#     item_name = Column(String, nullable=False,index=True)
#     quantity = Column(Integer, nullable=False)
#     total_price = Column(Float, nullable=False)
#     payment_method = Column(Enum(ModeEnum), nullable=False)
    