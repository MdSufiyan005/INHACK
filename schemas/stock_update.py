from pydantic import BaseModel
from datetime import datetime
import enum

class ModeEnum(str, enum.Enum):
    Online = "online"
    Cash = "Cash"

# -------------------- Purchase Schemas --------------------

class PurchaseBase(BaseModel):
    item_name: str
    quantity: int
    price: float
    payment_method: ModeEnum

class PurchaseCreate(PurchaseBase):
    pass

class PurchaseResponse(PurchaseBase):
    id: int
    created_at: datetime
    vendor_id: int  # Add vendor_id to response

    class Config:
        from_attributes = True

# -------------------- Selling Schemas --------------------

class SellingBase(BaseModel):
    item_name: str
    quantity: int
    total_price: float
    payment_method: ModeEnum

class SellingCreate(SellingBase):
    pass

class SellingResponse(SellingBase):
    id: int
    date: datetime
    vendor_id: int  # Add vendor_id to response

    class Config:
        from_attributes = True

# from pydantic import BaseModel
# from datetime import datetime
# import enum

# class ModeEnum(str,enum.Enum):
#     Online = "online"
#     Cash ="Cash"

# # -------------------- Purchase Schemas --------------------

# class PurchaseBase(BaseModel):
#     item_name: str
#     quantity: int
#     price: float
#     payment_method: ModeEnum

# class PurchaseCreate(PurchaseBase):
#     pass

# class PurchaseResponse(PurchaseBase):
#     id: int
#     created_at: datetime

#     class Config:
#         orm_mode = True


# # -------------------- Selling Schemas --------------------

# class SellingBase(BaseModel):
#     item_name: str
#     quantity: int
#     total_price: float
#     payment_method: ModeEnum

# class SellingCreate(SellingBase):
#     pass

# class SellingResponse(SellingBase):
#     id: int
#     date: datetime

#     class Config:
#         orm_mode = True
