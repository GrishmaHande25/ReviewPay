def diagnose_payment(transaction):

    failure_reason = transaction[
        "failure_reason"
    ]

    attempt_count = int(
        transaction["attempt_count"]
    )

    amount = int(
        transaction["amount"]
    )

    customer_history = transaction[
        "customer_history"
    ]


    # =====================================================
    # BANK ERROR
    # =====================================================

    if failure_reason == "bank_error":

        if attempt_count >= 3:

            return {
                "diagnosis":
                    "Repeated bank-side payment failure",

                "recovery_probability": 45,

                "recommended_action":
                    "escalate",

                "reason":
                    "Payment has already reached the maximum automatic attempt threshold. Further retries are stopped and the case is escalated."
            }

        return {
            "diagnosis":
                "Temporary bank-side failure",

            "recovery_probability": 75,

            "recommended_action":
                "retry_payment",

            "reason":
                "Bank errors can be temporary, so a controlled retry is allowed."
        }


    # =====================================================
    # TIMEOUT
    # =====================================================

    if failure_reason == "timeout":

        if attempt_count >= 3:

            return {
                "diagnosis":
                    "Repeated payment timeout",

                "recovery_probability": 35,

                "recommended_action":
                    "escalate",

                "reason":
                    "The payment has already reached the retry limit. Automatic retries are stopped to prevent repeated payment attempts."
            }

        return {
            "diagnosis":
                "Payment request timed out",

            "recovery_probability": 80,

            "recommended_action":
                "retry_payment",

            "reason":
                "Timeouts are usually temporary and can succeed on a controlled retry."
        }


    # =====================================================
    # NETWORK ERROR
    # =====================================================

    if failure_reason == "network_error":

        if attempt_count >= 3:

            return {
                "diagnosis":
                    "Repeated network connectivity failure",

                "recovery_probability": 40,

                "recommended_action":
                    "escalate",

                "reason":
                    "Multiple automatic attempts have already occurred. Further retries are stopped."
            }

        return {
            "diagnosis":
                "Network connectivity failure",

            "recovery_probability": 85,

            "recommended_action":
                "retry_payment",

            "reason":
                "Network errors are generally temporary and suitable for a controlled retry."
        }


    # =====================================================
    # INSUFFICIENT FUNDS
    # =====================================================

    if failure_reason == "insufficient_funds":

        return {
            "diagnosis":
                "Insufficient customer funds",

            "recovery_probability": 55,

            "recommended_action":
                "send_payment_reminder",

            "reason":
                "Immediate automatic retries are unlikely to succeed. The customer should be prompted to add funds and retry."
        }


    # =====================================================
    # FALLBACK
    # =====================================================

    return {
        "diagnosis":
            "Unknown payment failure",

        "recovery_probability": 30,

        "recommended_action":
            "escalate",

        "reason":
            "The failure reason is not recognized by the recovery engine."
    }