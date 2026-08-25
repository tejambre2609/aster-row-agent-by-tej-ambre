import json
from pathlib import Path

from src.agent import answer
from src.conversation import Conversation


BASE_DIR = Path(__file__).resolve().parent.parent
VISIBLE_CASES = BASE_DIR / "evaluation" / "visible-cases.json"


def normalize_text(text):
    """
    Make harmless formatting differences equivalent.

    Example:
        "45-calendar-day"
        "45 calendar days"
    """
    return (
        text.lower()
        .replace("-", " ")
        .replace("–", " ")
    )


def run_case(case):
    conversation = Conversation()
    results = []

    for message in case["messages"]:
        result = conversation.ask(message["content"])
        results.append(result)

    final = results[-1]

    text = normalize_text(final["answer"])
    expect = case["expect"]

    checks = []

    # Required literal text
    for item in expect.get("must_include", []):
        checks.append(
            (
                f"contains: {item}",
                normalize_text(item) in text
            )
        )

    # Forbidden literal text
    for item in expect.get("must_not_include", []):
        checks.append(
            (
                f"does not contain: {item}",
                normalize_text(item) not in text
            )
        )

    # Required sources
    for source in expect.get("required_sources", []):
        checks.append(
            (
                f"source: {source}",
                source in final.get("sources", [])
            )
        )

    # Tool behavior
    if "tool" in expect:
        checks.append(
            (
                f"tool: {expect['tool']}",
                final.get("tool") == expect["tool"]
            )
        )

    # Handoff
    if "handoff" in expect:
        checks.append(
            (
                f"handoff: {expect['handoff']}",
                final.get("handoff") == expect["handoff"]
            )
        )

    passed = all(ok for _, ok in checks)

    return {
        "id": case["id"],
        "category": case["category"],
        "passed": passed,
        "checks": checks,
        "answer": final["answer"],
    }


def main():
    with open(VISIBLE_CASES, "r", encoding="utf-8") as f:
        data = json.load(f)

    cases = data["cases"]

    print("=" * 60)
    print("ASTER & ROW EVALUATION")
    print("=" * 60)

    results = []

    for case in cases:
        result = run_case(case)
        results.append(result)

        status = "PASS" if result["passed"] else "FAIL"

        print(f"\n[{status}] {result['id']} ({result['category']})")

        for description, passed in result["checks"]:
            mark = "✓" if passed else "✗"
            print(f"  {mark} {description}")

    print("\n" + "=" * 60)

    total = len(results)
    passed = sum(r["passed"] for r in results)

    print(f"Overall: {passed}/{total} passed")

    categories = {}

    for result in results:
        category = result["category"]
        categories.setdefault(category, {"passed": 0, "total": 0})

        categories[category]["total"] += 1

        if result["passed"]:
            categories[category]["passed"] += 1

    print("\nBy category:")

    for category, stats in sorted(categories.items()):
        print(
            f"  {category}: "
            f"{stats['passed']}/{stats['total']}"
        )

    print("=" * 60)

    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()