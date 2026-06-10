import razorpay
import hmac
import hashlib
from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Dict, Any
from pydantic import BaseModel
from app.core.config import settings

router = APIRouter()

# Initialize Razorpay Client
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

class OrderCreateRequest(BaseModel):
    amount: int  # amount in paise
    currency: str = "INR"

class PaymentVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

@router.get("/services")
async def get_active_services():
    """Returns a mock list of active services for the user."""
    return [
        {
            "id": "ser_001",
            "name": "Premium Health Monitoring",
            "status": "Active",
            "expiry_date": "2026-12-31",
            "features": ["24/7 AI Voice Support", "Priority Ambulance Routing"]
        },
        {
            "id": "ser_002",
            "name": "Emergency SMS Alert Plus",
            "status": "Active",
            "expiry_date": "2027-01-15",
            "features": ["Unlimited Emergency Contacts", "Location History"]
        }
    ]

@router.post("/create-order")
async def create_order(request: OrderCreateRequest):
    """Creates a Razorpay order."""
    try:
        print(f"DEBUG: Creating order for amount {request.amount}")
        data = {
            "amount": request.amount,
            "currency": request.currency,
            "payment_capture": 1
        }
        order = client.order.create(data=data)
        print(f"DEBUG: Order created successfully: {order.get('id')}")
        return order
    except Exception as e:
        print(f"DEBUG ERROR: Order creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-payment")
async def verify_payment(request: PaymentVerifyRequest):
    """Verifies the Razorpay payment signature."""
    try:
        print(f"DEBUG: Verifying payment {request.razorpay_payment_id}")
        params_dict = {
            'razorpay_order_id': request.razorpay_order_id,
            'razorpay_payment_id': request.razorpay_payment_id,
            'razorpay_signature': request.razorpay_signature
        }
        client.utility.verify_payment_signature(params_dict)
        print(f"DEBUG: Payment {request.razorpay_payment_id} verified successfully")
        return {"status": "success", "message": "Payment verified successfully"}
    except Exception as e:
        print(f"DEBUG ERROR: Payment verification failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid payment signature")
