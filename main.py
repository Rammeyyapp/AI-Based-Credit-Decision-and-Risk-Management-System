from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .engine import ENGINE, seeded_transactions
from .models import ActionIn, TransactionIn


app = FastAPI(
    title="FinTrust Sentinel",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


transactions = seeded_transactions()
audits = []


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "data_policy": "Synthetic demo data only. No Razorpay private data.",
    }


@app.get("/api/transactions")
def list_transactions():
    return sorted(
        transactions,
        key=lambda x: x["created_at"],
        reverse=True,
    )


@app.get("/api/transactions/{transaction_id}")
def get_transaction(transaction_id: str):
    transaction = next(
        (
            item
            for item in transactions
            if item["transaction_id"] == transaction_id
        ),
        None,
    )

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

    return {
        **transaction,
        "investigation": ENGINE.investigate(transaction),
    }


@app.post("/api/investigate")
def investigate(transaction: TransactionIn):
    data = transaction.model_dump()

    data["transaction_id"] = (
        data.get("transaction_id")
        or f"TXN-LIVE-{len(transactions) + 1000}"
    )

    result = ENGINE.investigate(data)

    risk_score = result["risk_score"]

    if risk_score >= 65:
        status = "needs_review"
    elif risk_score >= 35:
        status = "monitored"
    else:
        status = "approved"

    data.update(
        {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "risk_score": risk_score,
            "status": status,
        }
    )

    transactions.append(data)

    audits.append(
        {
            "at": data["created_at"],
            "event": "model_investigation",
            "transaction_id": data["transaction_id"],
            "detail": "Risk engine assessed transaction",
        }
    )

    return {
        **data,
        "investigation": result,
    }


@app.post("/api/transactions/{transaction_id}/action")
def action(
    transaction_id: str,
    body: ActionIn,
):
    transaction = next(
        (
            item
            for item in transactions
            if item["transaction_id"] == transaction_id
        ),
        None,
    )

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

    status_map = {
        "approve": "approved",
        "step_up_verify": "verification_requested",
        "hold_review": "held_for_review",
        "block_refund": "refund_blocked",
    }

    if body.action not in status_map:
        raise HTTPException(
            status_code=422,
            detail="Unsupported action",
        )

    status = status_map[body.action]

    transaction["status"] = status

    audits.append(
        {
            "at": datetime.now(timezone.utc).isoformat(),
            "event": "human_action",
            "transaction_id": transaction_id,
            "action": body.action,
            "note": body.note,
        }
    )

    return {
        "ok": True,
        "status": status,
    }


@app.get("/api/metrics")
def metrics(threshold: float = 0.5):
    if not 0.05 <= threshold <= 0.95:
        raise HTTPException(
            status_code=422,
            detail="threshold must be between 0.05 and 0.95",
        )

    return ENGINE.metrics(threshold)


@app.get("/api/dashboard")
def dashboard():
    high_risk = [
        item
        for item in transactions
        if item["risk_score"] >= 65
    ]

    review_queue = sum(
        item["status"] in ["needs_review", "held_for_review"]
        for item in transactions
    )

    return {
        "transactions_today": len(transactions),
        "high_risk": len(high_risk),
        "review_queue": review_queue,
        "estimated_exposure_inr": round(
            sum(item["amount"] for item in high_risk),
            2,
        ),
        "spike": {
            "detected": len(high_risk) >= 6,
            "message": (
                "High-risk payment volume is above the seeded baseline"
                if len(high_risk) >= 6
                else "No anomalous high-risk spike detected"
            ),
        },
        "audit_count": len(audits),
        "recent_audit": audits[-8:],
    }


@app.get("/api/audit")
def audit():
    return list(reversed(audits))