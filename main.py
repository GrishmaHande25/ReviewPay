import os
import sys

# Add backend folder to Python path
backend_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "backend"
)

sys.path.insert(0, backend_path)


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from risk_detector import (
    get_at_risk_transactions,
    load_transactions,
)


from ai_agent import diagnose_payment


from recovery import (
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
    allow_origins=[
        "*",
        "https://fluffy-dusk-57d33d.netlify.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {
        "message": "RevivePay is running!",
        "status": "success"
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():

    integrity = get_system_integrity()

    return {
        "status": "healthy",
        "integrity": integrity.get("status"),
        "crash_recovery": integrity.get("crash_recovery"),
        "tamper_detection": integrity.get("tamper_detection")
    }


# =========================================================
# SYSTEM INTEGRITY
# =========================================================

@app.get("/system-integrity")
def system_integrity():

    return get_system_integrity()


# =========================================================
# AT-RISK TRANSACTIONS
# =========================================================

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


# =========================================================
# AI DIAGNOSIS
# =========================================================

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


# =========================================================
# SINGLE RECOVERY
# =========================================================

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


# =========================================================
# RECOVERY SUMMARY
# =========================================================

@app.get("/recovery-summary")
def recovery_summary():

    # Load all transactions
    transactions = load_transactions()

    # Find failed transactions
    failed = transactions[
        transactions["status"].astype(str).str.lower()
        == "failed"
    ]

    # Calculate total revenue at risk
    revenue_at_risk = int(
        failed["amount"].astype(float).sum()
    )

    # Get recovery engine summary
    summary = get_recovery_summary()

    # Override revenue at risk with actual
    # failed transaction amount
    summary["revenue_at_risk"] = revenue_at_risk

    # Calculate recovery rate
    if revenue_at_risk > 0:

        summary["recovery_rate"] = round(
            (
                float(summary.get("total_recovered", 0))
                / revenue_at_risk
            ) * 100,
            2
        )

    else:

        summary["recovery_rate"] = 0

    return summary


# =========================================================
# BATCH RECOVERY
# =========================================================

@app.post("/recover-batch")
def recover_batch():

    df = get_at_risk_transactions()

    return process_batch(df)


# =========================================================
# AUDIT LOG
# =========================================================

@app.get("/audit-log")
def audit_log():

    return get_audit_log()