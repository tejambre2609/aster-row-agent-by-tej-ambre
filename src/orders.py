import json
from pathlib import Path


ORDERS_FILE = Path(__file__).resolve().parent.parent / "data" / "orders.json"


def lookup_order(order_id: str):
    """Look up an order and return only customer-safe information."""

    with open(ORDERS_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    for order in data["orders"]:
        if order["order_id"].upper() == order_id.upper():
            return {
                "order_id": order["order_id"],
                "status": order["status"],
                "carrier": order["carrier"],
                "tracking_number": order["tracking_number"],
                "estimated_delivery": order["estimated_delivery"],
                "customer_safe_message": order["customer_safe_message"],
            }

    return None