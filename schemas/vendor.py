from pydantic import BaseModel
from datetime import datetime

class VendorCreate(BaseModel):
    Name: str
    PhoneNumber: str
    Location: str
    BusinessInfo: str

class VendorOut(BaseModel):
    id: int
    created_at: datetime
    Name: str
    PhoneNumber: str
    Location: str
    BusinessInfo: str
    session_id: str | None  # Add session_id, nullable

    class Config:
        from_attributes = True
        
# from pydantic import BaseModel
# from datetime import datetime


# class VendorCreate(BaseModel):
#     Name: str
#     PhoneNumber: str
#     Location: str
#     BusinessInfo: str



# class VendorOut(BaseModel):
#     id: int
#     created_at: datetime
#     Name: str
#     PhoneNumber: str
#     Location: str
#     BusinessInfo: str

#     class Config:
#         orm_mode = True
