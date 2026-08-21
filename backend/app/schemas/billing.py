from pydantic import BaseModel
from typing import Optional, List

class PlanInfo(BaseModel):
    id: str
    name: str
    price: int
    credits: int
    features: List[str]

class CreateOrderRequest(BaseModel):
    planId: str

class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    planId: str
