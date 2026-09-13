import hashlib
import hmac
import time

from aiopaysell import verify_signature


def _sign(body: bytes, secret: str, timestamp: str) -> str:
    signed = timestamp.encode() + b"." + body
    return "sha256=" + hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()


def test_valid_signature_matches() -> None:
    body = b'{"event_id": "1", "type": "payment.credited"}'
    secret = "whsec_test"
    ts = str(int(time.time()))
    assert verify_signature(body, _sign(body, secret, ts), ts, secret) is True


def test_tampered_body_fails() -> None:
    secret = "whsec_test"
    ts = str(int(time.time()))
    signature = _sign(b'{"amount": "5000000"}', secret, ts)
    assert verify_signature(b'{"amount": "50000000"}', signature, ts, secret) is False


def test_wrong_secret_fails() -> None:
    body = b'{"event_id": "1"}'
    ts = str(int(time.time()))
    signature = _sign(body, "whsec_a", ts)
    assert verify_signature(body, signature, ts, "whsec_b") is False


def test_missing_prefix_fails() -> None:
    body = b'{"event_id": "1"}'
    secret = "whsec_test"
    ts = str(int(time.time()))
    signed = ts.encode() + b"." + body
    raw_hex = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    assert verify_signature(body, raw_hex, ts, secret) is False  # no "sha256=" prefix


def test_expired_timestamp_fails() -> None:
    body = b'{"event_id": "1"}'
    secret = "whsec_test"
    old_ts = str(int(time.time()) - 3600)  # an hour ago, well past the default 300s
    signature = _sign(body, secret, old_ts)
    assert verify_signature(body, signature, old_ts, secret) is False


def test_future_timestamp_fails() -> None:
    body = b'{"event_id": "1"}'
    secret = "whsec_test"
    future_ts = str(int(time.time()) + 3600)
    signature = _sign(body, secret, future_ts)
    assert verify_signature(body, signature, future_ts, secret) is False


def test_custom_tolerance_allows_older_timestamp() -> None:
    body = b'{"event_id": "1"}'
    secret = "whsec_test"
    ts = str(int(time.time()) - 250)  # outside a tight tolerance, inside a loose one
    signature = _sign(body, secret, ts)
    assert verify_signature(body, signature, ts, secret, tolerance=60) is False
    assert verify_signature(body, signature, ts, secret, tolerance=600) is True


def test_malformed_timestamp_fails() -> None:
    body = b'{"event_id": "1"}'
    secret = "whsec_test"
    assert verify_signature(body, "sha256=whatever", "not-a-number", secret) is False
