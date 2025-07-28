from celery import Celery
from models.remainder import Remind_Me
from twilio.rest import Client
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
import pytz
import traceback
import models.remainder 
import models.vendor

from core.config import settings
# from models.remainder import Remind_Me

celery_app = Celery(
    'reminder_tasks',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# DB setup (reuse)
engine = create_engine(settings.DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
# celery.py


@celery_app.task
def send_whatsapp_reminder(vendor_phone, supplier_name, supplier_phone, amount, item_name, payment_method, reminder_id):
    print(f"[INFO] Celery task started for reminder ID: {reminder_id}")
    print(f"[INFO] Sending WhatsApp to: {vendor_phone}")
    db = SessionLocal()
    try:
        client = Client(settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)
        print("[DEBUG] Twilio client created.")
        body = (
            f"🔔 *Payment Reminder*\n"
            f"Item: {item_name}\n"
            f"Amount: ₹{amount}\n"
            f"To: {supplier_name} ({supplier_phone})\n"
            f"Method: {payment_method}"
        )
        print(f"[DEBUG] Message body prepared: {body}")
        message = client.messages.create(
            body=body,
            from_="whatsapp:+14155238886",
            to=f"whatsapp:{vendor_phone}"
        )
        print(f"[INFO] WhatsApp message SID: {message.sid}")
        # Update status to 'sent'
        reminder = db.query(Remind_Me).filter(Remind_Me.id == reminder_id).first()
        if reminder:
            reminder.status = "sent"
            db.commit()
        else:
            print(f"[ERROR] Reminder ID {reminder_id} not found in database")
    except Exception as e:
        print(f"[ERROR] Failed to send WhatsApp message: {e}")
        traceback.print_exc()
        # Update status to 'failed'
        reminder = db.query(Remind_Me).filter(Remind_Me.id == reminder_id).first()
        if reminder:
            reminder.status = "failed"
            db.commit()
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()
    return {"status": "sent", "message_sid": message.sid}

# @celery_app.task(name="app.celery_app.send_whatsapp_reminder")
# def send_whatsapp_reminder(vendor_phone, supplier_name, supplier_phone, amount, item_name, payment_method, reminder_id):
#     print(f"[INFO] Celery task started for reminder ID: {reminder_id}")
#     print(f"[INFO] Sending WhatsApp to: {vendor_phone}")
#     try:
#         client = Client(settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)
#         print("[DEBUG] Twilio client created.")
#         body = (
#             f"🔔 *Payment Reminder*\n"
#             f"Item: {item_name}\n"
#             f"Amount: ₹{amount}\n"
#             f"To: {supplier_name} ({supplier_phone})\n"
#             f"Method: {payment_method}"
#         )
#         print(f"[DEBUG] Message body prepared: {body}")
#         message = client.messages.create(
#             body=body,
#             from_="whatsapp:+14155238886",  # Twilio WhatsApp number
#             to=f"whatsapp:{vendor_phone}"
#         )
#         print(f"[INFO] WhatsApp message SID: {message.sid}")
#     except Exception as e:
#         print(f"[ERROR] Failed to send WhatsApp message: {e}")
#         traceback.print_exc()
