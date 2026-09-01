import pandas as pd


DATA_PATH = "data/transactions.csv"


def load_transactions():

    df = pd.read_csv(DATA_PATH)

    return df


def get_at_risk_transactions():

    df = load_transactions()

    # Select failed transactions
    failed = df[
        df["status"] == "failed"
    ].copy()

    # Calculate risk score
    failed["risk_score"] = 0

    # Multiple attempts
    failed.loc[
        failed["attempt_count"] >= 2,
        "risk_score"
    ] += 30

    # Failure reason
    failed.loc[
        failed["failure_reason"] == "insufficient_funds",
        "risk_score"
    ] += 20

    failed.loc[
        failed["failure_reason"] == "bank_error",
        "risk_score"
    ] += 25

    failed.loc[
        failed["failure_reason"] == "network_error",
        "risk_score"
    ] += 15

    failed.loc[
        failed["failure_reason"] == "timeout",
        "risk_score"
    ] += 10

    # High-value transaction
    failed.loc[
        failed["amount"] >= 5000,
        "risk_score"
    ] += 20

    # Maximum 100
    failed["risk_score"] = (
        failed["risk_score"]
        .clip(upper=100)
    )

    # Risk level
    failed["risk_level"] = failed[
        "risk_score"
    ].apply(
        lambda score:
        "High"
        if score >= 60
        else "Medium"
        if score >= 30
        else "Low"
    )

    return failed