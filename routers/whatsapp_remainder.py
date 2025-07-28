from fastapi import APIRouter, HTTPException, status, Depends, Response, Cookie
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
import uuid
from db.database import get_db
from core.config import settings
from models.remainder import Remind_Me
from models.vendor import Vendor
from schemas.remainder import RemindCreate, RemindResponse, ModeEnum
from core.celery import send_whatsapp_reminder
from datetime import datetime
import pytz
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()

def get_session_id(session_id: Optional[str] = Cookie(None)):
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

async def get_current_vendor(session_id: str = Depends(get_session_id), db: Session = Depends(get_db)):
    logger.debug(f"Checking session_id: {session_id}")
    vendor = db.query(Vendor).filter(Vendor.session_id == session_id).first()
    if not vendor:
        logger.error(f"No vendor found for session_id: {session_id}")
        raise HTTPException(status_code=401, detail="Vendor not authenticated")
    logger.debug(f"Found vendor: {vendor.Name}, ID: {vendor.id}, PhoneNumber: {vendor.PhoneNumber}")
    return vendor
@router.post(
    "/schedule-payment-reminder",
    response_model=RemindResponse,
    status_code=status.HTTP_201_CREATED
)
async def schedule_payment(
    remind: RemindCreate,
    vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db),
):
    # 1) Localize the picked datetime as IST
    dt = pytz.timezone(settings.TIMEZONE).localize(remind.Date_Time)
    if dt < datetime.now(pytz.timezone(settings.TIMEZONE)):
        raise HTTPException(status_code=400, detail="Reminder must be in the future")

    # 2) Normalize phone numbers
    # Use phone number from request, fallback to vendor phone if not provided
    vendor_phone_raw = remind.phone_number.strip().replace(" ", "").replace("-", "") if remind.phone_number else vendor.PhoneNumber.strip().replace(" ", "").replace("-", "")
    full_vendor_phone = vendor_phone_raw if vendor_phone_raw.startswith("+") else "+91" + vendor_phone_raw
    
    supplier_phone_raw = remind.supplier_phone_number.strip().replace(" ", "").replace("-", "")
    full_supplier_phone = supplier_phone_raw if supplier_phone_raw.startswith("+") else "+91" + supplier_phone_raw

    # 3) Persist
    record = Remind_Me(
        Date_Time=dt,
        item_name=remind.item_name,
        Amount=remind.Amount,
        ToWhom=remind.ToWhom,
        phone_number=full_vendor_phone,
        supplier_phone_number=full_supplier_phone,
        payment_method=remind.payment_method,
        status="pending",
        vendor_id=vendor.id,
    )
    try:
        db.add(record)
        db.commit()
        db.refresh(record)
    except Exception:
        db.rollback()
        logger.exception("DB error saving reminder")
        raise HTTPException(status_code=500, detail="Failed to save reminder")

    # 4) Schedule Celery
    delay = max((dt - datetime.now(pytz.timezone(settings.TIMEZONE))).total_seconds(), 0)
    send_whatsapp_reminder.apply_async(
        (full_vendor_phone, record.ToWhom, record.supplier_phone_number,
         record.Amount, record.item_name, record.payment_method, record.id),
        countdown=delay,
    )
    logger.info(f"Scheduled reminder #{record.id} in {delay:.0f}s")

    return RemindResponse.from_orm(record)

@router.get("/reminders/", response_model=List[RemindResponse])
async def list_reminders(
    vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db)
):
    try:
        logger.debug(f"Fetching reminders for vendor: {vendor.Name}, ID: {vendor.id}")
        reminders = db.query(Remind_Me).filter(Remind_Me.vendor_id == vendor.id).order_by(Remind_Me.Date_Time.desc()).all()
        logger.debug(f"Found {len(reminders)} reminders")
        return [RemindResponse.from_orm(reminder) for reminder in reminders]
    except Exception as e:
        logger.error(f"Error fetching reminders: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching reminders: {str(e)}")