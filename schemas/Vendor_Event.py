# schemas/vendor_event.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class VendorEventCreate(BaseModel):
    vendor_id: str
    event_name: str
    description: str
    location: str
    contact_phone: Optional[str] = None
    stall_info: str
    event_date: Optional[str] = None
    source_url: Optional[str] = None

class VendorEventRead(VendorEventCreate):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
