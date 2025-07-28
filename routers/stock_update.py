import uuid
from typing import List, Optional
from fastapi import (
    APIRouter, Depends, HTTPException,
    Cookie, Response, BackgroundTasks, status
)
from sqlalchemy.orm import Session
from datetime import datetime

from db.database import get_db
from models.stock_update import SellingTable, PurchaseTable
from models.vendor import Vendor  # Import Vendor model
from schemas.stock_update import (
    PurchaseCreate, PurchaseResponse,
    SellingCreate, SellingResponse
)

router = APIRouter()

# -- Helper for session cookie and vendor --
def get_session_id(session_id: Optional[str] = Cookie(None)):
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

async def get_current_vendor(session_id: str = Depends(get_session_id), db: Session = Depends(get_db)):
    vendor = db.query(Vendor).filter(Vendor.session_id == session_id).first()
    if not vendor:
        raise HTTPException(status_code=401, detail="Vendor not authenticated")
    return vendor

# -------------------------------
# PURCHASE (Stock In) Endpoints
# prefix: /purchases
# -------------------------------
purchase_router = APIRouter(prefix="/purchases", tags=["Purchases"])

@purchase_router.post("/", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED)
def create_purchase(
    request: PurchaseCreate,
    background_tasks: BackgroundTasks,
    response: Response,
    session_id: str = Depends(get_session_id),
    vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db),
):
    # Set session cookie
    response.set_cookie(key="session_id", value=session_id, httponly=True)

    # Associate purchase with the current vendor
    purchase = PurchaseTable(**request.dict(), vendor_id=vendor.id)
    db.add(purchase)
    db.commit()
    db.refresh(purchase)
    return purchase

@purchase_router.get("/", response_model=List[PurchaseResponse])
def list_purchases(
    vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db)
):
    # Filter purchases by vendor_id
    return db.query(PurchaseTable).filter(PurchaseTable.vendor_id == vendor.id).order_by(PurchaseTable.created_at.desc()).all()

@purchase_router.get("/{purchase_id}", response_model=PurchaseResponse)
def get_purchase(
    purchase_id: int,
    vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db)
):
    purchase = db.get(PurchaseTable, purchase_id)
    if not purchase or purchase.vendor_id != vendor.id:
        raise HTTPException(status_code=404, detail="Purchase not found or not authorized")
    return purchase

@purchase_router.put("/{purchase_id}", response_model=PurchaseResponse)
def update_purchase(
    purchase_id: int,
    request: PurchaseCreate,
    vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db),
):
    purchase = db.get(PurchaseTable, purchase_id)
    if not purchase or purchase.vendor_id != vendor.id:
        raise HTTPException(status_code=404, detail="Purchase not found or not authorized")
    for field, value in request.dict().items():
        setattr(purchase, field, value)
    db.commit()
    db.refresh(purchase)
    return purchase

@purchase_router.delete("/{purchase_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_purchase(
    purchase_id: int,
    vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db)
):
    purchase = db.get(PurchaseTable, purchase_id)
    if not purchase or purchase.vendor_id != vendor.id:
        raise HTTPException(status_code=404, detail="Purchase not found or not authorized")
    db.delete(purchase)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# -------------------------------
# SELLING (Stock Out) Endpoints
# prefix: /sales
# -------------------------------
selling_router = APIRouter(prefix="/sales", tags=["Sales"])

@selling_router.post("/", response_model=SellingResponse, status_code=status.HTTP_201_CREATED)
def create_sale(
    request: SellingCreate,
    vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db)
):
    # Associate sale with the current vendor
    sale = SellingTable(**request.dict(), vendor_id=vendor.id)
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale

@selling_router.get("/", response_model=List[SellingResponse])
def list_sales(
    vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db)
):
    # Filter sales by vendor_id
    return db.query(SellingTable).filter(SellingTable.vendor_id == vendor.id).order_by(SellingTable.date.desc()).all()

@selling_router.get("/{sale_id}", response_model=SellingResponse)
def get_sale(
    sale_id: int,
    vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db)
):
    sale = db.get(SellingTable, sale_id)
    if not sale or sale.vendor_id != vendor.id:
        raise HTTPException(status_code=404, detail="Sale not found or not authorized")
    return sale

@selling_router.put("/{sale_id}", response_model=SellingResponse)
def update_sale(
    sale_id: int,
    request: SellingCreate,
    vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db)
):
    sale = db.get(SellingTable, sale_id)
    if not sale or sale.vendor_id != vendor.id:
        raise HTTPException(status_code=404, detail="Sale not found or not authorized")
    for field, value in request.dict().items():
        setattr(sale, field, value)
    db.commit()
    db.refresh(sale)
    return sale

@selling_router.delete("/{sale_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sale(
    sale_id: int,
    vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db)
):
    sale = db.get(SellingTable, sale_id)
    if not sale or sale.vendor_id != vendor.id:
        raise HTTPException(status_code=404, detail="Sale not found or not authorized")
    db.delete(sale)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# -------------------------------
# Include all sub-routers in main router
# -------------------------------
router.include_router(purchase_router)
router.include_router(selling_router)


# import uuid
# from typing import List, Optional
# from fastapi import (
#     APIRouter, Depends, HTTPException,
#     Cookie, Response, BackgroundTasks, status
# )
# from sqlalchemy.orm import Session
# from datetime import datetime

# from db.database import get_db
# from models.stock_update import SellingTable, PurchaseTable

# from schemas.stock_update import (
#     PurchaseCreate, PurchaseResponse,
#     SellingCreate, SellingResponse
# )


# router = APIRouter()

# # -- helper for session cookie --
# def get_session_id(session_id: Optional[str] = Cookie(None)):
#     if not session_id:
#         session_id = str(uuid.uuid4())
#     return session_id


# # -------------------------------
# # PURCHASE (Stock In) Endpoints
# # prefix: /purchases
# # -------------------------------
# purchase_router = APIRouter(prefix="/purchases", tags=["Purchases"])


# @purchase_router.post("/", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED)
# def create_purchase(
#     request: PurchaseCreate,
#     background_tasks: BackgroundTasks,
#     response: Response,
#     session_id: str = Depends(get_session_id),
#     db: Session = Depends(get_db),
# ):
#     # set session cookie
#     response.set_cookie(key="session_id", value=session_id, httponly=True)

#     purchase = PurchaseTable(**request.dict())
#     db.add(purchase)
#     db.commit()
#     db.refresh(purchase)
#     return purchase


# @purchase_router.get("/", response_model=List[PurchaseResponse])
# def list_purchases(db: Session = Depends(get_db)):
#     return db.query(PurchaseTable).order_by(PurchaseTable.created_at.desc()).all()


# @purchase_router.get("/{purchase_id}", response_model=PurchaseResponse)
# def get_purchase(purchase_id: int, db: Session = Depends(get_db)):
#     purchase = db.get(PurchaseTable, purchase_id)
#     if not purchase:
#         raise HTTPException(status_code=404, detail="Purchase not found")
#     return purchase


# @purchase_router.put("/{purchase_id}", response_model=PurchaseResponse)
# def update_purchase(
#     purchase_id: int,
#     request: PurchaseCreate,
#     db: Session = Depends(get_db),
# ):
#     purchase = db.get(PurchaseTable, purchase_id)
#     if not purchase:
#         raise HTTPException(status_code=404, detail="Purchase not found")
#     for field, value in request.dict().items():
#         setattr(purchase, field, value)
#     db.commit()
#     db.refresh(purchase)
#     return purchase


# @purchase_router.delete("/{purchase_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_purchase(purchase_id: int, db: Session = Depends(get_db)):
#     purchase = db.get(PurchaseTable, purchase_id)
#     if not purchase:
#         raise HTTPException(status_code=404, detail="Purchase not found")
#     db.delete(purchase)
#     db.commit()
#     return Response(status_code=status.HTTP_204_NO_CONTENT)


# # -------------------------------
# # SELLING (Stock Out) Endpoints
# # prefix: /sales
# # -------------------------------
# selling_router = APIRouter(prefix="/sales", tags=["Sales"])


# @selling_router.post("/", response_model=SellingResponse, status_code=status.HTTP_201_CREATED)
# def create_sale(request: SellingCreate, db: Session = Depends(get_db)):
#     sale = SellingTable(**request.dict())
#     db.add(sale)
#     db.commit()
#     db.refresh(sale)
#     return sale


# @selling_router.get("/", response_model=List[SellingResponse])
# def list_sales(db: Session = Depends(get_db)):
#     return db.query(SellingTable).order_by(SellingTable.date.desc()).all()


# @selling_router.get("/{sale_id}", response_model=SellingResponse)
# def get_sale(sale_id: int, db: Session = Depends(get_db)):
#     sale = db.get(SellingTable, sale_id)
#     if not sale:
#         raise HTTPException(status_code=404, detail="Sale not found")
#     return sale


# @selling_router.put("/{sale_id}", response_model=SellingResponse)
# def update_sale(sale_id: int, request: SellingCreate, db: Session = Depends(get_db)):
#     sale = db.get(SellingTable, sale_id)
#     if not sale:
#         raise HTTPException(status_code=404, detail="Sale not found")
#     for field, value in request.dict().items():
#         setattr(sale, field, value)
#     db.commit()
#     db.refresh(sale)
#     return sale


# @selling_router.delete("/{sale_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_sale(sale_id: int, db: Session = Depends(get_db)):
#     sale = db.get(SellingTable, sale_id)
#     if not sale:
#         raise HTTPException(status_code=404, detail="Sale not found")
#     db.delete(sale)
#     db.commit()
#     return Response(status_code=status.HTTP_204_NO_CONTENT)




# # -------------------------------
# # Include all sub-routers in main router
# # -------------------------------
# router.include_router(purchase_router)
# router.include_router(selling_router)