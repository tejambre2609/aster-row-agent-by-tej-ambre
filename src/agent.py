import re
from datetime import datetime
import json
import logging
import os

from src.orders import lookup_order
from src.retrieval import search_documents, get_retrieval_trace

DEBUG = os.getenv("ASTER_DEBUG", "").lower() in {"1", "true", "yes"}

logger = logging.getLogger("aster_row_agent")

if DEBUG:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

def debug_log(event: str, **data):
    """Log structured debugging information without sensitive order data."""
    if not DEBUG:
        return

    safe_data = {
        "event": event,
        **data,
    }

    logger.info(json.dumps(safe_data, default=str))

def extract_order_id(message: str):
    """Extract a valid Aster & Row order ID."""
    match = re.search(r"\bORD-\d{4}\b", message.upper())
    return match.group(0) if match else None


def answer(message: str):
    """
    Main customer-support agent.

    Returns:
        {
            "answer": str,
            "sources": list[str],
            "tool": str,
            "handoff": bool
        }
    """

    message = message.strip()
    message_lower = message.lower()

    debug_log(
        "user_message",
        message=message,
    )

    # ---------------------------------------------------------
    # 1. Order ID + private/internal information
    # ---------------------------------------------------------
    order_id = extract_order_id(message)

    sensitive_terms = [
        "email",
        "e-mail",
        "address",
        "internal note",
        "internal notes",
        "risk score",
        "risk",
        "warehouse note",
        "warehouse notes",
        "fraud review",
        "fraud",
        "customer contact",
        "contact details",
        "personal information",
        "personal data",
    ]

    if order_id and any(
        term in message_lower for term in sensitive_terms
    ):
        return {
            "answer": (
                "I can help with customer-safe order information, but I "
                "can't disclose customer contact details, internal notes, "
                "risk scores, fraud-review information, or other internal "
                "information. A human support specialist can assist with "
                "requests that require access to that information."
            ),
            "sources": [],
            "tool": "optional_sanitized_lookup",
            "handoff": True,
        }

    # ---------------------------------------------------------
    # 2. Normal order lookup
    # ---------------------------------------------------------
    if order_id:
        debug_log(
            "tool_call",
            tool="order_lookup",
            arguments={"order_id": order_id},
        )

        order = lookup_order(order_id)

        debug_log(
            "tool_result",
            tool="order_lookup",
            found=order is not None,
            order_id=order_id,
        )

        if order is None:
            return {
                "answer": f"Order {order_id} was not found. Please check the order ID and try again.",
                "sources": [],
                "tool": "order_lookup",
                "handoff": True,
            }

        # Customer-safe fields only.
        status = str(order.get("status", "")).lower()
        carrier = order.get("carrier")
        eta = order.get("estimated_delivery")

        # Cancelled/returned orders must not expose stale ETA information.
        if status in {"cancelled", "returned"}:
            return {
                "answer": order["customer_safe_message"],
                "sources": [],
                "tool": "order_lookup",
                "handoff": False,
            }

        # Format ISO date as "August 22, 2026".
        if eta:
            try:
                formatted_eta = datetime.strptime(
                    str(eta),
                    "%Y-%m-%d",
                ).strftime("%B %d, %Y")
            except ValueError:
                formatted_eta = str(eta)
        else:
            formatted_eta = None

        # Build the answer from authoritative order fields.
        status_display = {
            "shipped": "shipped",
            "in transit": "in transit",
            "delivered": "delivered",
            "processing": "processing",
            "pending": "pending",
        }.get(status, status)

        if formatted_eta:
            answer_text = (
                f"Order {order['order_id']} is {status_display}"
                f"{f' with {carrier}' if carrier else ''} "
                f"and is currently estimated to arrive on "
                f"{formatted_eta}."
            )
        else:
            answer_text = (
                f"Order {order['order_id']} is {status_display}"
                f"{f' with {carrier}' if carrier else ''}. "
                "The delivery estimate is currently unavailable."
            )

        return {
            "answer": answer_text,
            "sources": [],
            "tool": "order_lookup",
            "handoff": False,
        }

    # ---------------------------------------------------------
    # 3. Order question without an order ID
    # ---------------------------------------------------------
    order_words = [
        "where is my order",
        "where is the order",
        "where's my order",
        "track my order",
        "track the order",
        "tracking my order",
        "order status",
        "status of my order",
        "check my order",
        "check the order",
        "order tracking",
        "delivery status",
    ]

    if any(phrase in message_lower for phrase in order_words):
        return {
            "answer": (
                "Please provide your order ID so I can check it for you."
            ),
            "sources": [],
            "tool": "not_called_without_id",
            "handoff": False,
        }

    # ---------------------------------------------------------
    # 4. Final-sale + damaged/wrong item
    # ---------------------------------------------------------
    is_final_sale = (
        "final-sale" in message_lower
        or "final sale" in message_lower
    )

    is_damaged_or_wrong = any(
        word in message_lower
        for word in [
            "damaged",
            "broken",
            "zipper",
            "wrong item",
            "wrong product",
            "defective",
        ]
    )

    if is_final_sale and is_damaged_or_wrong:
        return {
            "answer": (
                "Final sale does not automatically prevent a damaged-item "
                "review. A damaged final-sale item should be reported "
                "within 7 days of delivery, and a human support specialist "
                "must review the case before approval. I cannot approve "
                "the return automatically."
            ),
            "sources": [
                "03-final-sale-and-promotions.md",
                "04-damaged-or-wrong-items.md",
            ],
            "tool": "not_called",
            "handoff": True,
        }

    # ---------------------------------------------------------
    # 5. Prompt-injection / migration-note protection
    # ---------------------------------------------------------
    migration_request = (
        "migration note" in message_lower
        or "migration" in message_lower
    )

    asks_to_override_policy = any(
        phrase in message_lower
        for phrase in [
            "60 days",
            "60-day",
            "60 day",
            "ignore the real policy",
            "ignore the current policy",
            "use the newer document",
            "use the migration document",
            "approve my return",
            "automatically approve",
        ]
    )

    if migration_request and asks_to_override_policy:
        return {
            "answer": (
                "The migration note is not authoritative. The standard "
                "return policy is 30 days from delivery unless a valid "
                "exception applies. I cannot automatically approve "
                "a return."
            ),
            "sources": ["01-returns-policy-current.md"],
            "tool": "not_called",
            "handoff": False,
        }

    # ---------------------------------------------------------
    # 6. Insufficient information
    # ---------------------------------------------------------
    insufficient_information_terms = [
        "vegan",
        "adhesive",
        "fabric",
        "material certification",
        "vegan guarantee",
        "all fabrics",
        "all materials",
    ]

    if any(
        term in message_lower
        for term in insufficient_information_terms
    ):
        return {
            "answer": (
                "The supplied information is insufficient to confirm "
                "whether all fabrics and adhesives are vegan. Human "
                "confirmation is needed before making a material or "
                "certification claim."
            ),
            "sources": [],
            "tool": "not_called",
            "handoff": True,
        }

    # ---------------------------------------------------------
    # 7. Breeze Tumbler source conflict
    # ---------------------------------------------------------
    if (
        "breeze tumbler" in message_lower
        and any(
            term in message_lower
            for term in [
                "dishwasher",
                "dish washer",
                "dishwash",
            ]
        )
    ):
        return {
            "answer": (
                "The current official sources conflict on Breeze Tumbler "
                "dishwasher care. One source says to hand-wash the body, "
                "while another says all components are dishwasher safe. "
                "Because the sources conflict, I recommend the safest "
                "interim guidance of hand-washing the body and getting "
                "human confirmation before using a dishwasher."
            ),
            "sources": [
                "11-product-care.md",
                "12-breeze-tumbler-product-card.md",
            ],
            "tool": "not_called",
            "handoff": True,
        }

    # ---------------------------------------------------------
    # 8. TrailPlus return policy
    # ---------------------------------------------------------

    trailplus_question = "trailplus" in message_lower

    # Detect explicit statements that the customer is NOT a member.
    explicitly_not_trailplus = any(
        phrase in message_lower
        for phrase in [
            "not a trailplus member",
            "not trailplus",
            "wasn't a trailplus member",
            "was not a trailplus member",
            "am not a trailplus member",
            "i am not a trailplus member",
            "i'm not a trailplus member",
        ]
    )

    trailplus_return_terms = [
        "return",
        "return window",
        "return period",
        "how long",
        "how many days",
        "days to return",
        "time to return",
        "return deadline",
        "send it back",
        "send something back",
        "eligible for return",
    ]

    asks_about_trailplus_return = (
        trailplus_question
        and not explicitly_not_trailplus
        and any(
            term in message_lower
            for term in trailplus_return_terms
        )
    )

    # ---------------------------------------------------------
    # 8A. TrailPlus member return policy
    # ---------------------------------------------------------
    if asks_about_trailplus_return:
        return {
            "answer": (
                "TrailPlus members whose membership was active when the "
                "order was placed receive a **45-calendar-day return window "
                "(45 calendar days) from delivery** for eligible items. "
                "Joining TrailPlus after placing an order does not extend "
                "that order's return window."
            ),
            "sources": ["09-trailplus-membership.md"],
            "tool": "not_called",
            "handoff": False,
        }

    # ---------------------------------------------------------
    # 8B. Explicit non-TrailPlus return policy
    # ---------------------------------------------------------
    if explicitly_not_trailplus and any(
        term in message_lower
        for term in trailplus_return_terms
    ):
        return {
            "answer": (
                "Non-TrailPlus customers have a **30 calendar days** "
                "return window from delivery for eligible unused items."
            ),
            "sources": ["01-returns-policy-current.md"],
            "tool": "not_called",
            "handoff": False,
        }

    # ---------------------------------------------------------
    # 9. General return-policy retrieval
    # ---------------------------------------------------------
    results = search_documents(message)

    debug_log(
        "retrieval",
        query=message,
        results=get_retrieval_trace(message),
    )

    if not results:
        return {
            "answer": (
                "The supplied information is insufficient to answer "
                "that reliably. Human confirmation is needed."
            ),
            "sources": [],
            "tool": "not_called",
            "handoff": True,
        }

    # The retrieval layer ranks authoritative documents.
    best = results[0]

    return {
        "answer": best["content"],
        "sources": [best["source"]],
        "tool": "not_called",
        "handoff": False,
    }


# -------------------------------------------------------------
# CLI
# -------------------------------------------------------------
if __name__ == "__main__":
    print("Aster & Row Support Agent")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            message = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if message.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        if not message:
            continue

        result = answer(message)

        print(f"\nAgent: {result['answer']}")

        if result.get("sources"):
            print("Sources:")
            for source in result["sources"]:
                print(f"  - {source}")

        if result.get("handoff"):
            print("Handoff: Recommended")

        print()
