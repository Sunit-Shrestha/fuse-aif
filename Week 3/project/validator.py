from __future__ import annotations


def clean_sql(sql: str) -> str:
    return sql.replace("```sql", "").replace("```", "").strip()


def is_safe_query(sql: str) -> bool:
    normalized = clean_sql(sql).upper()
    if not (normalized.startswith("SELECT") or normalized.startswith("WITH")):
        return False

    forbidden = [
        "DROP ",
        "UPDATE ",
        "DELETE ",
        "INSERT ",
        "ALTER ",
        "TRUNCATE ",
        "GRANT ",
        "REVOKE ",
        "REPLACE ",
    ]
    return not any(token in normalized for token in forbidden)


def validate_sql(sql: str) -> str:
    cleaned = clean_sql(sql)
    if not is_safe_query(cleaned):
        raise ValueError("Unsafe query detected. Only SELECT is allowed.")
    return cleaned

