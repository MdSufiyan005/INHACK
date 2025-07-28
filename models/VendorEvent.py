from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from db.database import Base# or your Base class

class VendorEvent(Base):
    __tablename__ = "vendor_events"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(String, index=True)
    event_name = Column(String)
    description = Column(Text)
    location = Column(String)
    contact_phone = Column(String, nullable=True)
    stall_info = Column(String)
    event_date = Column(String, nullable=True)
    source_url = Column(String, nullable=True, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
