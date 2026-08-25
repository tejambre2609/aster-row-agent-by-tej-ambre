from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
KB_DIR = BASE_DIR / "knowledge-base"


def load_documents():
    documents = []

    for path in sorted(KB_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8")

        priority = 50

        if path.name == "01-returns-policy-current.md":
            priority = 1
        elif path.name == "02-returns-policy-legacy.md":
            priority = 99
        elif path.name == "14-internal-content-migration-notes.md":
            priority = 100

        documents.append({
            "source": path.name,
            "content": content,
            "priority": priority,
        })

    return documents


def search_documents(query: str):
    query_lower = query.lower()
    query_words = set(query_lower.split())
    results = []

    for document in load_documents():
        content_lower = document["content"].lower()
        content_words = set(content_lower.split())

        score = len(query_words & content_words)

        # General return-policy routing.
        # Prefer the current official returns policy.
        if any(
            term in query_words
            for term in {
                "return",
                "returns",
                "refund",
                "refunds",
                "exchange",
                "exchanges",
            }
        ):
            if document["source"] == "01-returns-policy-current.md":
                score += 100
            elif document["source"] == "02-returns-policy-legacy.md":
                score -= 100

        # TrailPlus is more specific than the general return policy.
        if (
            "trailplus" in query_lower
            and document["source"] == "09-trailplus-membership.md"
        ):
            score += 200

        # Specific topic routing.
        if (
            "trailplus" in query_lower
            and document["source"] == "09-trailplus-membership.md"
        ):
            score += 100

        if (
            "warranty" in query_lower
            and document["source"] == "07-warranty.md"
        ):
            score += 100

        if (
            "international" in query_lower
            or "ship internationally" in query_lower
            or "shipping internationally" in query_lower
            or "canada" in query_lower
            or any(
                country in query_lower
                for country in [
                    "germany",
                    "france",
                    "uk",
                    "united kingdom",
                    "australia",
                    "japan",
                ]
            )
        ):
            if document["source"] == "06-international-shipping.md":
                score += 100

        if (
            "dishwasher" in query_lower
            or "breeze tumbler" in query_lower
        ):
            if document["source"] in {
                "11-product-care.md",
                "12-breeze-tumbler-product-card.md",
            }:
                score += 100

        if score > 0:
            results.append({
                "source": document["source"],
                "content": document["content"],
                "score": score,
                "priority": document["priority"],
            })

    return sorted(
        results,
        key=lambda x: (-x["score"], x["priority"])
    )
def get_retrieval_trace(query: str):
    """
    Return retrieval details for debugging/observability.
    Does not change the actual retrieval behavior.
    """
    results = search_documents(query)

    return [
        {
            "source": result["source"],
            "score": result["score"],
            "priority": result["priority"],
            "content_preview": result["content"][:300].replace("\n", " "),
        }
        for result in results
    ]