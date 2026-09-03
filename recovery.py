import os
import json
import hashlib
import random
import shutil
import tempfile

import pandas as pd

from datetime import datetime, timezone

from ai_agent import diagnose_payment

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)


LOG_PATH = os.path.join(
    DATA_DIR,
    "recovery_log.csv"
)


SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()
SUPABASE_ENABLED = bool(SUPABASE_URL and SUPABASE_KEY and create_client is not None)
SUPABASE_TABLE = "recovery_logs"

supabase = None
if SUPABASE_ENABLED:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        SUPABASE_ENABLED = False
        supabase = None


BACKUP_PATH = os.path.join(
    DATA_DIR,
    "recovery_log.backup.csv"
)


SECOND_BACKUP_PATH = os.path.join(
    DATA_DIR,
    "recovery_log.backup2.csv"
)


INTEGRITY_PATH = os.path.join(
    DATA_DIR,
    "recovery_integrity.json"
)


LOG_COLUMNS = [

    "timestamp",

    "transaction_id",

    "amount",

    "action",

    "result",

    "recovered_amount",

    "attempt_number",

    "message",

    "previous_hash",

    "record_hash"
]


def ensure_data_dir():

    os.makedirs(
        DATA_DIR,
        exist_ok=True
    )


def _read_csv_log():
    ensure_data_dir()

    if not os.path.exists(LOG_PATH):
        return pd.DataFrame(columns=LOG_COLUMNS)

    try:
        df = pd.read_csv(
            LOG_PATH,
            dtype=str,
            keep_default_na=False
        )
    except Exception:
        return None

    for column in LOG_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    return df[LOG_COLUMNS].fillna("")


def _normalize_database_log(rows):
    if not rows:
        return pd.DataFrame(columns=LOG_COLUMNS)

    normalized = []
    for row in rows:
        item = {}
        for column in LOG_COLUMNS:
            value = row.get(column, "")
            if value is None:
                value = ""
            item[column] = str(value)
        normalized.append(item)

    df = pd.DataFrame(normalized, columns=LOG_COLUMNS)
    return df.fillna("")


def read_log():
    if SUPABASE_ENABLED and supabase is not None:
        try:
            response = (
                supabase.table(SUPABASE_TABLE)
                .select("*")
                .order("id")
                .execute()
            )
            return _normalize_database_log(response.data or [])
        except Exception as exc:
            raise RuntimeError(
                f"Unable to read Supabase recovery log: {exc}"
            ) from exc

    return _read_csv_log()


def canonical_record(
    record
):

    values = {}

    for column in LOG_COLUMNS:

        if column in [
            "previous_hash",
            "record_hash"
        ]:
            continue


        value = record.get(
            column,
            ""
        )


        if pd.isna(value):
            value = ""


        values[column] = str(
            value
        )


    return json.dumps(
        values,
        sort_keys=True,
        separators=(
            ",",
            ":"
        )
    )


def calculate_hash(
    record,
    previous_hash
):

    payload = (
        previous_hash
        +
        "|"
        +
        canonical_record(
            record
        )
    )


    return hashlib.sha256(
        payload.encode(
            "utf-8"
        )
    ).hexdigest()


def atomic_write(
    df,
    path
):

    ensure_data_dir()


    fd, temp_path = tempfile.mkstemp(
        dir=DATA_DIR,
        prefix="revivepay_",
        suffix=".tmp"
    )


    os.close(fd)


    try:

        df.to_csv(
            temp_path,
            index=False
        )


        with open(
            temp_path,
            "r+b"
        ) as file:
            file.flush()
            try:
                os.fsync(
                    file.fileno()
                )
            except OSError:
                pass


        os.replace(
            temp_path,
            path
        )


    finally:

        if os.path.exists(
            temp_path
        ):

            os.remove(
                temp_path
            )


def backup_log():

    ensure_data_dir()


    if os.path.exists(
        BACKUP_PATH
    ):

        try:

            shutil.copy2(
                BACKUP_PATH,
                SECOND_BACKUP_PATH
            )

        except Exception:
            pass


    if os.path.exists(
        LOG_PATH
    ):

        shutil.copy2(
            LOG_PATH,
            BACKUP_PATH
        )


def verify_file(
    path
):

    if not os.path.exists(
        path
    ):

        return {
            "status":
                "MISSING",

            "record_count":
                0
        }


    try:

        df = pd.read_csv(
            path,
            dtype=str,
            keep_default_na=False
        )

    except Exception:

        return {
            "status":
                "ERROR",

            "message":
                "File could not be read."
        }


    if df.empty:

        return {
            "status":
                "VERIFIED",

            "record_count":
                0
        }


    if (
        "previous_hash"
        not in df.columns
        or
        "record_hash"
        not in df.columns
    ):

        return {
            "status":
                "LEGACY",

            "record_count":
                len(df)
        }


    previous_hash = ""


    for index, row in df.iterrows():

        record = row.to_dict()


        expected = calculate_hash(
            record,
            previous_hash
        )


        stored_previous = str(
            row.get(
                "previous_hash",
                ""
            )
        )


        stored_hash = str(
            row.get(
                "record_hash",
                ""
            )
        )


        if stored_previous != previous_hash:

            return {

                "status":
                    "TAMPERED",

                "record_count":
                    len(df),

                "broken_record":
                    index + 1
            }


        if stored_hash != expected:

            return {

                "status":
                    "TAMPERED",

                "record_count":
                    len(df),

                "broken_record":
                    index + 1
            }


        previous_hash = stored_hash


    return {

        "status":
            "VERIFIED",

        "record_count":
            len(df),

        "last_hash":
            previous_hash
    }


def migrate_legacy_log():

    df = read_log()


    if df is None:
        return False


    if df.empty:
        return True


    if (
        "previous_hash"
        in df.columns
        and
        "record_hash"
        in df.columns
    ):

        return True


    backup_log()


    for column in LOG_COLUMNS:

        if column not in df.columns:

            df[column] = ""


    df = df[
        LOG_COLUMNS
    ]


    previous_hash = ""

    previous_values = []

    hash_values = []


    for _, row in df.iterrows():

        record = row.to_dict()


        current_hash = calculate_hash(
            record,
            previous_hash
        )


        previous_values.append(
            previous_hash
        )


        hash_values.append(
            current_hash
        )


        previous_hash = current_hash


    df[
        "previous_hash"
    ] = previous_values


    df[
        "record_hash"
    ] = hash_values


    atomic_write(
        df,
        LOG_PATH
    )


    save_integrity_metadata(
        df
    )


    return True


def save_integrity_metadata(
    df
):

    last_hash = ""


    if not df.empty:

        last_hash = str(
            df.iloc[-1][
                "record_hash"
            ]
        )


    metadata = {

        "algorithm":
            "SHA-256",

        "record_count":
            len(df),

        "last_hash":
            last_hash,

        "updated_at":
            datetime.now().isoformat()
    }


    temp = (
        INTEGRITY_PATH
        +
        ".tmp"
    )


    with open(
        temp,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            metadata,
            file,
            indent=2
        )


        file.flush()

        os.fsync(
            file.fileno()
        )


    os.replace(
        temp,
        INTEGRITY_PATH
    )


def recover_from_backup():

    for backup in [
        BACKUP_PATH,
        SECOND_BACKUP_PATH
    ]:

        if not os.path.exists(
            backup
        ):
            continue


        verification = verify_file(
            backup
        )


        if (
            verification["status"]
            ==
            "VERIFIED"
        ):

            shutil.copy2(
                backup,
                LOG_PATH
            )


            return True


    return False


def verify_database():
    if not SUPABASE_ENABLED or supabase is None:
        return {
            "status": "DISABLED",
            "record_count": 0
        }

    try:
        response = (
            supabase.table(SUPABASE_TABLE)
            .select("*")
            .order("id")
            .execute()
        )
        df = _normalize_database_log(response.data or [])

        if df.empty:
            return {
                "status": "VERIFIED",
                "record_count": 0,
                "last_hash": ""
            }

        previous_hash = ""

        for index, row in df.iterrows():
            record = row.to_dict()
            expected = calculate_hash(record, previous_hash)

            stored_previous = str(row.get("previous_hash", ""))
            stored_hash = str(row.get("record_hash", ""))

            if stored_previous != previous_hash:
                return {
                    "status": "TAMPERED",
                    "record_count": len(df),
                    "broken_record": index + 1
                }

            if stored_hash != expected:
                return {
                    "status": "TAMPERED",
                    "record_count": len(df),
                    "broken_record": index + 1
                }

            previous_hash = stored_hash

        return {
            "status": "VERIFIED",
            "record_count": len(df),
            "last_hash": previous_hash
        }

    except Exception as exc:
        return {
            "status": "ERROR",
            "record_count": 0,
            "message": str(exc)
        }


def migrate_csv_to_supabase():
    if not SUPABASE_ENABLED or supabase is None:
        return False

    try:
        response = (
            supabase.table(SUPABASE_TABLE)
            .select("id")
            .limit(1)
            .execute()
        )

        if response.data:
            return True

        csv_df = _read_csv_log()

        if csv_df is None or csv_df.empty:
            return True

        verification = verify_file(LOG_PATH)
        if verification.get("status") != "VERIFIED":
            return False

        rows = csv_df[LOG_COLUMNS].to_dict(orient="records")

        for row in rows:
            payload = {}
            for column in LOG_COLUMNS:
                value = row.get(column, "")
                if column == "amount":
                    value = float(value or 0)
                elif column == "recovered_amount":
                    value = float(value or 0)
                elif column == "attempt_number":
                    value = int(float(value or 0))
                elif column == "timestamp":
                    value = str(value)
                else:
                    value = str(value)
                payload[column] = value

            supabase.table(SUPABASE_TABLE).insert(payload).execute()

        return True

    except Exception:
        return False


def startup_recovery():
    ensure_data_dir()

    if SUPABASE_ENABLED and supabase is not None:
        migration_ok = migrate_csv_to_supabase()

        verification = verify_database()

        if verification.get("status") == "TAMPERED":
            raise RuntimeError(
                "Audit database integrity check failed."
            )

        if verification.get("status") == "ERROR":
            raise RuntimeError(
                "Unable to verify Supabase audit database."
            )

        return migration_ok

    if not os.path.exists(LOG_PATH):
        recover_from_backup()
        return

    verification = verify_file(LOG_PATH)

    if verification["status"] == "LEGACY":
        migrate_legacy_log()
        return

    if verification["status"] == "TAMPERED":
        recover_from_backup()
    elif verification["status"] == "ERROR":
        recover_from_backup()


def save_audit_record(
    transaction,
    action,
    result,
    recovered_amount,
    attempt_number,
    message
):
    ensure_data_dir()

    if SUPABASE_ENABLED and supabase is not None:
        current = read_log()

        if current is None:
            raise RuntimeError(
                "Unable to load Supabase recovery log."
            )

        integrity = verify_database()

        if integrity["status"] != "VERIFIED":
            raise RuntimeError(
                "Audit database integrity check failed."
            )

        previous_hash = ""

        if not current.empty:
            previous_hash = str(
                current.iloc[-1]["record_hash"]
            )

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "transaction_id": str(transaction["transaction_id"]),
            "amount": float(transaction["amount"]),
            "action": str(action),
            "result": str(result),
            "recovered_amount": float(recovered_amount),
            "attempt_number": int(attempt_number),
            "message": str(message),
            "previous_hash": previous_hash,
            "record_hash": ""
        }

        entry["record_hash"] = calculate_hash(
            entry,
            previous_hash
        )

        supabase.table(SUPABASE_TABLE).insert(entry).execute()

        # Keep a local copy as a temporary/backup artifact.
        updated = pd.concat(
            [
                current,
                pd.DataFrame([entry])
            ],
            ignore_index=True
        )

        atomic_write(updated, LOG_PATH)
        save_integrity_metadata(updated)
        return

    current = read_log()

    if current is None:
        if not recover_from_backup():
            raise RuntimeError(
                "Audit log is corrupted and no valid backup is available."
            )

        current = read_log()

    if current is None:
        raise RuntimeError(
            "Unable to load recovery log."
        )

    integrity = verify_file(LOG_PATH)

    if integrity["status"] not in [
        "VERIFIED",
        "LEGACY"
    ]:
        raise RuntimeError(
            "Audit integrity check failed."
        )

    if integrity["status"] == "LEGACY":
        migrate_legacy_log()
        current = read_log()

    previous_hash = ""

    if not current.empty:
        previous_hash = str(
            current.iloc[-1]["record_hash"]
        )

    entry = {
        "timestamp":
            datetime.now().isoformat(),

        "transaction_id":
            transaction["transaction_id"],

        "amount":
            transaction["amount"],

        "action":
            action,

        "result":
            result,

        "recovered_amount":
            recovered_amount,

        "attempt_number":
            attempt_number,

        "message":
            message,

        "previous_hash":
            previous_hash,

        "record_hash":
            ""
    }

    entry["record_hash"] = calculate_hash(
        entry,
        previous_hash
    )

    new_df = pd.DataFrame([entry])

    updated = pd.concat(
        [
            current,
            new_df
        ],
        ignore_index=True
    )

    backup_log()

    atomic_write(
        updated,
        LOG_PATH
    )

    verification = verify_file(
        LOG_PATH
    )

    if verification["status"] != "VERIFIED":
        if os.path.exists(BACKUP_PATH):
            shutil.copy2(
                BACKUP_PATH,
                LOG_PATH
            )

        raise RuntimeError(
            "Audit verification failed after write."
        )

    save_integrity_metadata(
        updated
    )


def get_previous_attempts(
    transaction_id
):

    df = read_log()


    if df is None or df.empty:

        return 0


    return len(
        df[
            df["transaction_id"].astype(str)
            ==
            str(transaction_id)
        ]
    )


def already_recovered(
    transaction_id
):

    df = read_log()


    if df is None or df.empty:

        return False


    successful = df[
        (
            df["transaction_id"].astype(str)
            ==
            str(transaction_id)
        )
        &
        (
            df["result"].astype(str)
            ==
            "success"
        )
    ]


    return not successful.empty


def retry_payment(
    transaction
):

    transaction_id = transaction[
        "transaction_id"
    ]


    amount = int(
        transaction["amount"]
    )


    if already_recovered(
        transaction_id
    ):

        return {

            "transaction_id":
                transaction_id,

            "amount":
                amount,

            "action":
                "retry_payment",

            "result":
                "already_recovered",

            "recovered_amount":
                0,

            "message":
                "Duplicate recovery prevented."
        }


    previous = get_previous_attempts(
        transaction_id
    )


    attempt = (
        int(
            transaction[
                "attempt_count"
            ]
        )
        +
        previous
        +
        1
    )


    if attempt > 3:

        message = (
            "Maximum automatic recovery "
            "attempts reached. Case escalated."
        )


        save_audit_record(
            transaction,
            "retry_payment",
            "stopped",
            0,
            attempt,
            message
        )


        return {

            "transaction_id":
                transaction_id,

            "amount":
                amount,

            "action":
                "retry_payment",

            "result":
                "stopped",

            "recovered_amount":
                0,

            "attempt_number":
                attempt,

            "message":
                message
        }


    reason = transaction[
        "failure_reason"
    ]


    probability = {

        "timeout":
            0.80,

        "network_error":
            0.85,

        "bank_error":
            0.65

    }.get(
        reason,
        0
    )


    success = (
        random.random()
        <
        probability
    )


    if success:

        message = (
            "Payment recovered successfully."
        )


        save_audit_record(
            transaction,
            "retry_payment",
            "success",
            amount,
            attempt,
            message
        )


        return {

            "transaction_id":
                transaction_id,

            "amount":
                amount,

            "action":
                "retry_payment",

            "result":
                "success",

            "recovered_amount":
                amount,

            "attempt_number":
                attempt,

            "message":
                message
        }


    message = (
        "Controlled retry failed."
    )


    save_audit_record(
        transaction,
        "retry_payment",
        "failed",
        0,
        attempt,
        message
    )


    return {

        "transaction_id":
            transaction_id,

        "amount":
            amount,

        "action":
            "retry_payment",

        "result":
            "failed",

        "recovered_amount":
            0,

        "attempt_number":
            attempt,

        "message":
            message
    }


def send_payment_reminder(
    transaction
):

    message = (
        "Payment reminder sent to customer."
    )


    save_audit_record(
        transaction,
        "send_payment_reminder",
        "reminder_sent",
        0,
        transaction[
            "attempt_count"
        ],
        message
    )


    return {

        "transaction_id":
            transaction[
                "transaction_id"
            ],

        "amount":
            transaction[
                "amount"
            ],

        "action":
            "send_payment_reminder",

        "result":
            "reminder_sent",

        "recovered_amount":
            0,

        "message":
            message
    }


def escalate_to_human(
    transaction
):

    message = (
        "Case escalated to human support. "
        "Automatic recovery stopped."
    )


    save_audit_record(
        transaction,
        "escalate",
        "escalated",
        0,
        transaction[
            "attempt_count"
        ],
        message
    )


    return {

        "transaction_id":
            transaction[
                "transaction_id"
            ],

        "amount":
            transaction[
                "amount"
            ],

        "action":
            "escalate",

        "result":
            "escalated",

                "recovered_amount":
            0,

        "attempt_number":
            transaction[
                "attempt_count"
            ],

        "message":
            message
    }


def execute_recovery(
    transaction,
    action
):

    if (
        action
        ==
        "retry_payment"
    ):

        if int(
            transaction[
                "attempt_count"
            ]
        ) >= 3:

            return escalate_to_human(
                transaction
            )


        return retry_payment(
            transaction
        )


    if (
        action
        ==
        "send_payment_reminder"
    ):

        return send_payment_reminder(
            transaction
        )


    return escalate_to_human(
        transaction
    )


def get_recovery_summary():

    df = read_log()


    if df is None or df.empty:

        return {

            "revenue_at_risk":
                0,

            "total_recovered":
                0,

            "recovery_rate":
                0,

            "successful_recoveries":
                0,

            "total_actions":
                0
        }


    recovered = pd.to_numeric(
        df[
            "recovered_amount"
        ],
        errors="coerce"
    ).fillna(0).sum()


    successful = len(
        df[
            df["result"]
            ==
            "success"
        ]
    )


    return {

        "revenue_at_risk":
            0,

        "total_recovered":
            int(recovered),

        "recovery_rate":
            0,

        "successful_recoveries":
            successful,

        "total_actions":
            len(df)
    }


def process_batch(
    df
):

    if df is None or df.empty:

        return {

            "total_transactions":
                0,

            "failed_transactions":
                0,

            "revenue_at_risk":
                0,

            "recovery_attempts":
                0,

            "successful_recoveries":
                0,

            "revenue_recovered":
                0,

            "recovery_rate":
                0,

            "escalated_cases":
                0,

            "skipped_already_recovered":
                0,

            "details":
                []
        }


    failed = df[
        df["status"].astype(str).str.lower()
        ==
        "failed"
    ]


    revenue_at_risk = int(
        pd.to_numeric(
            failed["amount"],
            errors="coerce"
        ).fillna(0).sum()
    )


    successful = 0

    recovered = 0

    escalated = 0

    attempts = 0

    skipped = 0

    details = []


    for _, row in failed.iterrows():

        transaction = row.to_dict()

        transaction_id = (
            transaction[
                "transaction_id"
            ]
        )


        if already_recovered(
            transaction_id
        ):

            skipped += 1

            continue


        diagnosis = diagnose_payment(
            transaction
        )


        result = execute_recovery(
            transaction,
            diagnosis[
                "recommended_action"
            ]
        )


        attempts += 1


        recovered_amount = int(
            result.get(
                "recovered_amount",
                0
            )
        )


        recovered += (
            recovered_amount
        )


        if result[
            "result"
        ] == "success":

            successful += 1


        if result[
            "result"
        ] == "escalated":

            escalated += 1


        details.append({

            "transaction_id":
                transaction_id,

            "amount":
                transaction["amount"],

            "failure_reason":
                transaction[
                    "failure_reason"
                ],

            "recovery_probability":
                diagnosis[
                    "recovery_probability"
                ],

            "recommended_action":
                diagnosis[
                    "recommended_action"
                ],

            "result":
                result["result"],

            "recovered_amount":
                recovered_amount
        })


    rate = 0


    if revenue_at_risk > 0:

        rate = (
            recovered
            /
            revenue_at_risk
        ) * 100


    return {

        "total_transactions":
            len(df),

        "failed_transactions":
            len(failed),

        "revenue_at_risk":
            revenue_at_risk,

        "recovery_attempts":
            attempts,

        "successful_recoveries":
            successful,

        "revenue_recovered":
            recovered,

        "recovery_rate":
            round(rate, 2),

        "escalated_cases":
            escalated,

        "skipped_already_recovered":
            skipped,

        "details":
            details
    }


def get_audit_log():

    df = read_log()


    if df is None or df.empty:

        return []


    return df.iloc[
        ::-1
    ].head(
        100
    ).to_dict(
        orient="records"
    )


def get_system_integrity():
    if SUPABASE_ENABLED and supabase is not None:
        verification = verify_database()

        return {
            "status": verification.get(
                "status",
                "UNKNOWN"
            ),

            "message": (
                "Audit trail integrity verified."
                if verification.get("status") == "VERIFIED"
                else "Integrity check requires attention."
            ),

            "record_count": verification.get(
                "record_count",
                0
            ),

            "broken_record": verification.get(
                "broken_record"
            ),

            "backup_available": os.path.exists(
                BACKUP_PATH
            ),

            "secondary_backup_available": os.path.exists(
                SECOND_BACKUP_PATH
            ),

            "algorithm": "SHA-256",
            "crash_recovery": True,
            "tamper_detection": True,
            "storage": "Supabase PostgreSQL"
        }

    verification = verify_file(LOG_PATH)

    return {
        "status":
            verification.get(
                "status",
                "UNKNOWN"
            ),

        "message":
            (
                "Audit trail integrity verified."
                if verification.get("status") == "VERIFIED"
                else "Integrity check requires attention."
            ),

        "record_count":
            verification.get(
                "record_count",
                0
            ),

        "broken_record":
            verification.get(
                "broken_record"
            ),

        "backup_available":
            os.path.exists(
                BACKUP_PATH
            ),

        "secondary_backup_available":
            os.path.exists(
                SECOND_BACKUP_PATH
            ),

        "algorithm":
            "SHA-256",

        "crash_recovery":
            True,

        "tamper_detection":
            True,

        "storage":
            "Local CSV"
    }


startup_recovery()
