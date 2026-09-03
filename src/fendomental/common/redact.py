import re

_SECRET_QUERY_PARAM = re.compile(r"(apikey|token)=[^&\s]+", re.IGNORECASE)


def redact_secrets(text: str) -> str:
    """Strip apikey=/token=... query-param values from a string before it is
    logged, stored, or printed (SPEC.md section 7, risk #11: never let an
    audit column accidentally capture a credential)."""
    return _SECRET_QUERY_PARAM.sub(lambda m: f"{m.group(1)}=***REDACTED***", text)
