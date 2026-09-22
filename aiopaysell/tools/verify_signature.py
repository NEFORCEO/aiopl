import hashlib
import hmac
import time
from typing import Annotated

from annotated_doc import Doc

DEFAULT_TIMESTAMP_TOLERANCE = 300
"""Max allowed distance, in seconds, between ``X-Paysell-Timestamp`` and now."""


def verify_signature(
    raw_body: Annotated[
        bytes,
        Doc(
            "The exact bytes received, before any JSON parsing — "
            "re-serialising changes key order and spacing, which breaks the signature."
        ),
    ],
    signature: Annotated[
        str,
        Doc("The `X-Paysell-Signature` header value, e.g. `sha256=...`."),
    ],
    timestamp: Annotated[
        str,
        Doc("The `X-Paysell-Timestamp` header value (unix seconds, as a str)."),
    ],
    secret: Annotated[str, Doc("Your shop's webhook secret.")],
    *,
    tolerance: Annotated[
        float,
        Doc(
            "Max allowed clock skew, in seconds. Keep your server's clock "
            "on NTP, or a tight tolerance starts rejecting good deliveries."
        ),
    ] = DEFAULT_TIMESTAMP_TOLERANCE,
) -> bool:
    """
    Verify a Paysell webhook signature.

    A standalone version of the check `aiopaysell.webhook.WebhookHandler`
    runs internally — use it if you're parsing webhooks by hand instead of
    through a `aiopaysell.webhook.WebhookManager`.

    Mirrors the docs' verification snippet: the signature is
    `HMAC-SHA256(secret, "{timestamp}.{raw_body}")`, hex-encoded and
    prefixed `sha256=`, compared with `hmac.compare_digest` (not `==`,
    which leaks the answer through timing). The timestamp is part of the
    signed string precisely so it can't be edited without breaking the
    signature — reject anything more than `tolerance` seconds from your
    own clock, in either direction, or a captured request stays valid
    forever and can be replayed at any time.

    Returns:
        `True` if the signature matches and the timestamp is within tolerance.
    """
    try:
        sent_at = int(timestamp)
    except (TypeError, ValueError):
        return False
    if abs(time.time() - sent_at) > tolerance:
        return False
    signed = timestamp.encode() + b"." + raw_body
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return hmac.compare_digest("sha256=" + expected, signature)
