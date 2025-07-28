import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Form, Response, status
from sqlalchemy.orm import Session

from db.database import get_db
from models.vendor import Vendor
from schemas.vendor import VendorCreate, VendorOut

router = APIRouter()
vendor_router = APIRouter(prefix="/vendor", tags=["vendor"])

@vendor_router.patch("/{vendor_id}", response_model=VendorOut)
def update_vendor(
    vendor_update: VendorCreate,
    vendor_id: int = Path(..., description="The ID of the vendor to update"),  # Changed to int to match Vendor model
    db: Session = Depends(get_db)
):
    db_vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not db_vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    update_data = vendor_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_vendor, field, value)

    db.commit()
    db.refresh(db_vendor)
    return db_vendor

@vendor_router.post("/", response_model=VendorOut, status_code=status.HTTP_201_CREATED)
def create_vendors(
    vendor: VendorCreate,
    response: Response,
    db: Session = Depends(get_db)
):
    existing_vendor = db.query(Vendor).filter(Vendor.PhoneNumber == vendor.PhoneNumber).first()
    if existing_vendor:
        raise HTTPException(status_code=400, detail="Vendor with this phone number already exists")
    
    session_id = str(uuid.uuid4())  # Generate session_id
    new_vendor = Vendor(**vendor.dict(), session_id=session_id)
    db.add(new_vendor)
    db.commit()
    db.refresh(new_vendor)
    
    # Set session_id cookie
    response.set_cookie(key="session_id", value=session_id, httponly=True)
    return new_vendor

@vendor_router.get("/", response_model=List[VendorOut])
def get_vendors(db: Session = Depends(get_db)):
    return db.query(Vendor).all()

@vendor_router.post("/authenticate", status_code=status.HTTP_200_OK)
def authenticate_vendor(
    phone_number: str = Form(...),
    response: Response = None,
    db: Session = Depends(get_db)
):
    vendor = db.query(Vendor).filter(Vendor.PhoneNumber == phone_number).first()
    session_id = str(uuid.uuid4())  # Generate new session_id
    
    if vendor:
        # Update vendor's session_id
        vendor.session_id = session_id
        db.commit()
        db.refresh(vendor)
        # Set session_id cookie
        response.set_cookie(key="session_id", value=session_id, httponly=True)
        return {"exists": True, "vendor": VendorOut.from_orm(vendor).dict()}
    else:
        return {"exists": False}

@vendor_router.get("/by-phone/{phone_number}", response_model=VendorOut)
def get_vendor_by_phone(phone_number: str, db: Session = Depends(get_db)):
    vendor = db.query(Vendor).filter(Vendor.PhoneNumber == phone_number).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor

router.include_router(vendor_router)