from fastapi import FastAPI

from aiopaysell import Paysell
from aiopaysell.webhook import FastAPIManager

app = FastAPI()
pay = Paysell(
    "sk_live_YOUR_KEY",
    webhook_manager=FastAPIManager(app, path="/webhooks/paysell"),
    # Shown once when the key was created — a different value from the key itself.
    webhook_secret="YOUR_WEBHOOK_SECRET",
)


@pay.payment_credited()
async def on_payment_credited(payment) -> None:
    if payment.status == "paid":
        print(f"order {payment.order_id} paid in full")
    else:
        print(f"order {payment.order_id}: {payment.status}")


@pay.payment_rejected()
async def on_payment_rejected(payment) -> None:
    # A held deposit was declined — release nothing.
    print(f"order {payment.order_id}: deposit rejected ({payment.reason})")


# uvicorn webhook_fastapi:app
