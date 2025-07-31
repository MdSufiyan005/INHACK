from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends, Response, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from core.config import settings
from routers import remainder, stock_update, vendor, whatsapp_remainder, event_router
from db.database import create_tables, SessionLocal, engine, Base
import os
from routers.event_router import event_router 
from sqlalchemy.orm import Session
from models.stock_update import PurchaseTable, SellingTable, ModeEnum
from models.vendor import Vendor
import json
from typing import Optional
import uuid
from fastapi.staticfiles import StaticFiles
from db.database import get_db
from core.vision_ai import extract_text
create_tables()
app = FastAPI(
    title="INHACK `INDIAN HAWKERS`",
    description="An Application for Indian Street Food Sellers",
    version="1.0.0",
    docs_url="/docs"
)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Reuse get_session_id and get_current_vendor from stock_update.py
def get_session_id(session_id: Optional[str] = Cookie(None)):
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

async def get_current_vendor(session_id: str = Depends(get_session_id), db: Session = Depends(get_db)):
    vendor = db.query(Vendor).filter(Vendor.session_id == session_id).first()
    if not vendor:
        raise HTTPException(status_code=401, detail="Vendor not authenticated")
    return vendor

@app.get('/', response_class=HTMLResponse)
async def home():
    html = open('templates/index.html').read()
    return HTMLResponse(html)

@app.post('/api/upload-receipt/')
async def upload_receipt(
    file: UploadFile = File(...),
    intent: str = Form(...),
    vendor: Vendor = Depends(get_current_vendor),  # Add vendor dependency
    db: Session = Depends(get_db)
):
    temp_path = None
    
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail='Invalid file type. Please upload an image file.')

        # Validate intent
        if intent not in ['purchase', 'selling']:
            raise HTTPException(status_code=400, detail='Invalid intent. Must be "purchase" or "selling".')

        # Create temp file with unique name
        temp_path = f"temp_{uuid.uuid4()}_{file.filename}"
        
        # Save uploaded file
        try:
            with open(temp_path, 'wb') as f:
                content = await file.read()
                if not content:
                    raise HTTPException(status_code=400, detail='Empty file uploaded.')
                f.write(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f'Failed to save uploaded file: {str(e)}')

        # Extract text using AI
        try:
            json_str = extract_text(temp_path, intent)
            raw = (json_str or "").strip()

            if not raw:
                raise HTTPException(status_code=502, detail="AI service returned empty response")

        except Exception as e:
            raise HTTPException(status_code=502, detail=f"AI processing failed: {str(e)}")

        # Parse JSON response
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=502, detail=f"Invalid JSON from AI service: {str(e)}")

        # Validate JSON structure
        if not isinstance(payload, dict):
            raise HTTPException(status_code=502, detail="AI response is not a valid JSON object")
        
        if payload.get("intent") != intent:
            raise HTTPException(status_code=502, detail=f"Intent mismatch. Expected: {intent}, Got: {payload.get('intent')}")
        
        if "items" not in payload or not isinstance(payload["items"], list):
            raise HTTPException(status_code=502, detail="No 'items' list found in AI response")

        items = payload["items"]
        
        if not items:
            raise HTTPException(status_code=400, detail="No items found in the receipt")

        # Database operations
        records = []
        
        for idx, item in enumerate(items):
            try:
                # Validate item structure
                required_fields = ["item_name", "quantity", "price", "payment_method"]
                for field in required_fields:
                    if field not in item:
                        raise ValueError(f"Missing required field '{field}' in item {idx + 1}")

                # Validate and convert data types
                item_name = str(item["item_name"]).strip()
                if not item_name:
                    raise ValueError(f"Empty item name in item {idx + 1}")

                try:
                    quantity = int(float(item["quantity"]))
                    if quantity <= 0:
                        raise ValueError(f"Invalid quantity in item {idx + 1}: {quantity}")
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid quantity format in item {idx + 1}: {item['quantity']}")

                try:
                    price = float(item["price"])
                    if price < 0:
                        raise ValueError(f"Invalid price in item {idx + 1}: {price}")
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid price format in item {idx + 1}: {item['price']}")

                # Validate payment method
                payment_method = str(item["payment_method"]).strip()
                if payment_method not in ["Cash", "online"]:
                    payment_method = "Cash"

                # Create database record
                if intent == 'purchase':
                    record = PurchaseTable(
                        item_name=item_name,
                        quantity=quantity,
                        price=price,
                        payment_method=ModeEnum(payment_method),
                        vendor_id=vendor.id  # Set vendor_id from authenticated vendor
                    )
                else:  # selling
                    record = SellingTable(
                        item_name=item_name,
                        quantity=quantity,
                        total_price=price,
                        payment_method=ModeEnum(payment_method),
                        vendor_id=vendor.id  # Set vendor_id from authenticated vendor
                    )
                
                db.add(record)
                records.append(record)
                
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error processing item {idx + 1}: {str(e)}")

        # Commit all records
        try:
            db.commit()
            
            # Refresh to get IDs and timestamps
            for record in records:
                db.refresh(record)
                
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

        # Convert records to dict format for response
        response_items = []
        for record in records:
            if intent == 'purchase':
                response_items.append({
                    "id": record.id,
                    "item_name": record.item_name,
                    "quantity": record.quantity,
                    "price": record.price,
                    "payment_method": record.payment_method.value,
                    "created_at": record.created_at.isoformat() if hasattr(record, 'created_at') else None,
                    "vendor_id": record.vendor_id  # Include vendor_id to match schema
                })
            else:
                response_items.append({
                    "id": record.id,
                    "item_name": record.item_name,
                    "quantity": record.quantity,
                    "price": record.total_price,
                    "payment_method": record.payment_method.value,
                    "created_at": record.date.isoformat() if hasattr(record, 'date') else None,
                    "vendor_id": record.vendor_id  # Include vendor_id to match schema
                })

        return {
            "message": "Receipt processed successfully",
            "items": response_items,
            "count": len(response_items)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        if db:
            try:
                db.close()
            except Exception:
                pass

app.include_router(stock_update.router, prefix=settings.API_PREFIX)
app.include_router(remainder.router, prefix=settings.API_PREFIX)
app.include_router(vendor.router, prefix=settings.API_PREFIX)
app.include_router(whatsapp_remainder.router, prefix=settings.API_PREFIX)
app.include_router(event_router, prefix=settings.API_PREFIX)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)