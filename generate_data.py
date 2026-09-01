import pandas as pd
import random
from datetime import datetime, timedelta


# Number of transactions
NUM_TRANSACTIONS = 1000


# Possible payment methods
payment_methods = ["UPI", "Card", "NetBanking", "Wallet"]

# Possible failure reasons
failure_reasons = [
    "network_error",
    "timeout",
    "bank_error",
    "insufficient_funds",
    "none"
]

# Possible transaction statuses
statuses = ["success", "failed"]


transactions = []


# Generate transactions
for i in range(1, NUM_TRANSACTIONS + 1):

    transaction_id = f"TX{i:04d}"

    amount = random.randint(200, 10000)

    status = random.choices(
        statuses,
        weights=[75, 25]
    )[0]

    payment_method = random.choice(payment_methods)

    if status == "failed":
        failure_reason = random.choice(
            failure_reasons[:-1]
        )

        attempt_count = random.randint(1, 3)

    else:
        failure_reason = "none"
        attempt_count = 1

    customer_history = random.choice(
        ["new", "returning", "frequent"]
    )

    timestamp = datetime.now() - timedelta(
        minutes=random.randint(0, 10000)
    )

    transactions.append({
        "transaction_id": transaction_id,
        "amount": amount,
        "status": status,
        "failure_reason": failure_reason,
        "payment_method": payment_method,
        "attempt_count": attempt_count,
        "customer_history": customer_history,
        "timestamp": timestamp
    })


# Convert the data into a table
df = pd.DataFrame(transactions)


# Save the data as CSV
df.to_csv(
    "data/transactions.csv",
    index=False
)


print("Transaction dataset created successfully!")
print(f"Total transactions: {len(df)}")
print("\nFirst 10 transactions:")
print(df.head(10))