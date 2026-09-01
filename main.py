from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.risk_detector import get_at_risk_transactions
from backend.ai_agent import diagnose_payment

from backend.recovery import (
    execute_recovery,
    get_recovery_summary,
    process_batch,
    get_audit_log,
    get_system_integrity,
)


app = FastAPI(
    title="RevivePay API",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "RevivePay is running!",
        "status": "success"
    }


@app.get("/health")
def health():
    integrity = get_system_integrity()

    return {
        "status": "healthy",
        "integrity": integrity.get("status"),
        "crash_recovery": integrity.get("crash_recovery"),
        "tamper_detection": integrity.get("tamper_detection")
    }


@app.get("/system-integrity")
def system_integrity():
    return get_system_integrity()


@app.get("/at-risk")
def at_risk_transactions():

    df = get_at_risk_transactions()

    if df.empty:
        return []

    df = df.sort_values(
        by="risk_score",
        ascending=False
    ).head(20)

    return df.to_dict(
        orient="records"
    )


@app.get("/diagnose/{transaction_id}")
def diagnose_transaction(
    transaction_id: str
):

    df = get_at_risk_transactions()

    transaction = df[
        df["transaction_id"].astype(str)
        == str(transaction_id)
    ]

    if transaction.empty:
        return {
            "error": "Transaction not found"
        }

    transaction_data = (
        transaction.iloc[0].to_dict()
    )

    diagnosis = diagnose_payment(
        transaction_data
    )

    return {
        "transaction": transaction_data,
        "ai_decision": diagnosis
    }


@app.post("/recover/{transaction_id}")
def recover_transaction(
    transaction_id: str
):

    df = get_at_risk_transactions()

    transaction = df[
        df["transaction_id"].astype(str)
        == str(transaction_id)
    ]

    if transaction.empty:
        return {
            "error": "Transaction not found"
        }

    transaction_data = (
        transaction.iloc[0].to_dict()
    )

    diagnosis = diagnose_payment(
        transaction_data
    )

    result = execute_recovery(
        transaction_data,
        diagnosis["recommended_action"]
    )

    return {
        "transaction": transaction_data,
        "ai_decision": diagnosis,
        "recovery_result": result
    }


@app.get("/recovery-summary")
def recovery_summary():
    return get_recovery_summary()


@app.post("/recover-batch")
def recover_batch():

    df = get_at_risk_transactions()

    return process_batch(df)


@app.get("/audit-log")
def audit_log():
    return get_audit_log()