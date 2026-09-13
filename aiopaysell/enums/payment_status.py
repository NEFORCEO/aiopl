from enum import Enum


class PaymentStatus(str, Enum):
    """
    On-chain payment lifecycle, as shown in the Paysell dashboard.

    Not returned by any documented API endpoint or webhook payload today —
    kept here as a reference for the states a payment passes through before
    ``credited`` fires the ``payment.credited`` webhook.
    """

    DETECTED = "detected"
    """Seen on chain, waiting for confirmations."""
    CONFIRMED = "confirmed"
    """The network confirmed it. Crediting next."""
    CREDITED = "credited"
    """On your balance. This is when the webhook fires."""
    REVIEW = "review"
    """Held for a human to look at (e.g. coins with no open invoice)."""
    REJECTED = "rejected"
    """Not credited. The reason is recorded."""
