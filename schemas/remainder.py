from pydantic import BaseModel, validator, model_validator
from datetime import datetime
import enum

class ModeEnum(str, enum.Enum):
    Online = 'Online'
    Cash   = 'Cash'

class RemindCreate(BaseModel):
    Date_Time: datetime
    item_name: str
    Amount: float
    ToWhom: str
    phone_number: str
    supplier_phone_number: str
    payment_method: ModeEnum

    @validator('payment_method', pre=True)
    def normalize_input_method(cls, v):
        if isinstance(v, str):
            low = v.strip().lower()
            if low == 'online':
                return 'Online'
            if low == 'cash':
                return 'Cash'
        return v

class RemindResponse(BaseModel):
    id: int
    Date_Time: datetime
    item_name: str
    Amount: float
    ToWhom: str
    phone_number: str
    supplier_phone_number: str
    payment_method: ModeEnum
    status: str
    vendor_id: int

    # Pydantic v2 config:
    model_config = {
        'from_attributes': True,   # allow .from_orm()
        'populate_by_name': True,
    }

    @model_validator(mode='after')
    def normalize_output_method(cls, m):
        pm = m.payment_method
        if isinstance(pm, str):
            low = pm.strip().lower()
            if low == 'online':
                m.payment_method = 'Online'
            elif low == 'cash':
                m.payment_method = 'Cash'
        return m
