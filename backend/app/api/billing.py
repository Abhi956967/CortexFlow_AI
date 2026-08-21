from fastapi import APIRouter, HTTPException, Depends
from app.core.security import get_current_user
from app.core.config import settings
from app.schemas.billing import PlanInfo, CreateOrderRequest, VerifyPaymentRequest

router = APIRouter(prefix="/billing", tags=["Billing"])

PLANS = [
    {
        "id": "free",
        "name": "Free Starter",
        "price": 0,
        "credits": 100,
        "features": ["100 Monthly AI Credits", "Basic Chat & Coding Agent", "Community Support"]
    },
    {
        "id": "pro",
        "name": "Pro Power",
        "price": 499,
        "credits": 1500,
        "features": ["1,500 High-Speed AI Credits", "All Agents (PPT, PDF, Image, Vision)", "Qdrant PDF RAG Vector Store", "Priority Support"]
    },
    {
        "id": "enterprise",
        "name": "Unlimited AI",
        "price": 1499,
        "credits": 10000,
        "features": ["10,000 AI Credits", "Multi-Agent Parallel Execution", "Custom Knowledge Base RAG", "Dedicated Serverless Capacity"]
    }
]

@router.get("/plans")
async def get_plans():
    return {"success": True, "plans": PLANS}

@router.post("/create-order")
async def create_order(payload: CreateOrderRequest, user: dict = Depends(get_current_user)):
    plan = next((p for p in PLANS if p["id"] == payload.planId), None)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    return {
        "success": True,
        "orderId": f"order_mock_{payload.planId}",
        "amount": plan["price"] * 100,
        "currency": "INR",
        "key": settings.RAZORPAY_KEY_ID or "rzp_test_key"
    }

@router.post("/verify-payment")
async def verify_payment(payload: VerifyPaymentRequest, user: dict = Depends(get_current_user)):
    return {
        "success": True,
        "message": "Payment verified successfully. Credits updated.",
        "credits": 1500
    }
