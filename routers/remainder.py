
import uuid
from typing import List, Optional
from fastapi import (
    APIRouter, Depends, HTTPException,
    Cookie, Response, BackgroundTasks, status
)
from sqlalchemy.orm import Session
from datetime import datetime
from models.vendor import Vendor

from db.database import get_db

from models.remainder import Remind_Me
from schemas.remainder import RemindCreate, RemindResponse

router = APIRouter()
# -------------------------------
# REMINDERS Endpoints
# prefix: /reminders
# -------------------------------
reminder_router = APIRouter(prefix="/reminders", tags=["Reminders"])


def get_session_id(session_id: Optional[str] = Cookie(None)):
    return session_id


def get_current_vendor(session_id: str = Depends(get_session_id), db: Session = Depends(get_db)):
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    vendor = db.query(Vendor).filter(Vendor.session_id == session_id).first()
    if not vendor:
        raise HTTPException(status_code=401, detail="Vendor not found")
    return vendor


@reminder_router.post("/", response_model=RemindResponse, status_code=status.HTTP_201_CREATED)
def create_reminder(request: RemindCreate, vendor: Vendor = Depends(get_current_vendor), db: Session = Depends(get_db)):
    reminder = Remind_Me(
        Date_Time=request.Date_Time,
        item_name=request.item_name,
        Amount=request.Amount,
        ToWhom=request.ToWhom,
        phone_number=request.phone_number,
        supplier_phone_number=request.supplier_phone_number,
        payment_method=request.payment_method,
        vendor_id=vendor.id
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


@reminder_router.get("/", response_model=List[RemindResponse])
def list_reminders(vendor: Vendor = Depends(get_current_vendor), db: Session = Depends(get_db)):
    return db.query(Remind_Me).filter(Remind_Me.vendor_id == vendor.id).order_by(Remind_Me.Date_Time.asc()).all()


@reminder_router.get("/{reminder_id}", response_model=RemindResponse)
def get_reminder(reminder_id: int, vendor: Vendor = Depends(get_current_vendor), db: Session = Depends(get_db)):
    r = db.query(Remind_Me).filter(Remind_Me.id == reminder_id, Remind_Me.vendor_id == vendor.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return r


@reminder_router.put("/{reminder_id}", response_model=RemindResponse)
def update_reminder(reminder_id: int, request: RemindCreate, vendor: Vendor = Depends(get_current_vendor), db: Session = Depends(get_db)):
    r = db.query(Remind_Me).filter(Remind_Me.id == reminder_id, Remind_Me.vendor_id == vendor.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Reminder not found")
    # update fields
    r.Date_Time = request.Date_Time # type: ignore
    r.item_name = request.item_name # type: ignore
    r.Amount = request.Amount # type: ignore
    r.ToWhom = request.ToWhom # type: ignore
    r.phone_number = request.phone_number # type: ignore
    r.supplier_phone_number = request.supplier_phone_number # type: ignore
    r.payment_method = request.payment_method # type: ignore
    db.commit()
    db.refresh(r)
    return r


@reminder_router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(reminder_id: int, vendor: Vendor = Depends(get_current_vendor), db: Session = Depends(get_db)):
    r = db.query(Remind_Me).filter(Remind_Me.id == reminder_id, Remind_Me.vendor_id == vendor.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Reminder not found")
    db.delete(r)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


router.include_router(reminder_router)
