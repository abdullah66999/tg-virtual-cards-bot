from fastapi import FastAPI, Request, HTTPException
import json
from datetime import datetime
from models import SessionLocal, Card, Transaction

app = FastAPI()

def _get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/webhook/{provider}")
async def provider_webhook(provider: str, request: Request):
    payload = await request.json()
    # Expected generic fields (adjust per provider as needed)
    tx_id = payload.get("transaction_id") or payload.get("id")
    status = payload.get("status")
    amount = payload.get("amount") or payload.get("amount_usd")
    pan = payload.get("card_pan") or payload.get("pan")
    if not all([tx_id, status, pan]):
        raise HTTPException(status_code=400, detail="Missing required fields")

    db = SessionLocal()
    try:
        card = db.query(Card).filter_by(pan=pan).first()
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        transaction = db.query(Transaction).filter_by(external_tx_id=tx_id).first()
        if not transaction:
            transaction = Transaction(
                card_id=card.id,
                amount_usd=float(amount) if amount is not None else 0.0,
                status=status,
                provider=provider,
                external_tx_id=tx_id,
                raw_data=json.dumps(payload),
                created_at=datetime.utcnow(),
            )
            db.add(transaction)
        else:
            transaction.status = status
            transaction.raw_data = json.dumps(payload)
        db.commit()
    finally:
        db.close()
    return {"ok": True}
