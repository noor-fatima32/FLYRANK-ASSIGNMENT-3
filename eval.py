import json
import os
import requests
from datetime import datetime, timezone


API_URL = os.getenv(
    "API_URL",
    "http://127.0.0.1:8000/classify"
)

CASES_FILE = "evals/cases.json"


def main():
    with open(CASES_FILE, "r", encoding="utf-8") as f:
        cases = json.load(f)

    passed = 0

    print("=" * 60)
    print("LLM API EVALUATION")
    print("=" * 60)

    for case in cases:
        response = requests.post(
            API_URL,
            json={"text": case["text"]},
            timeout=60,
        )

        print(f"\nCase {case['id']}")
        print(f"Input: {case['text']}")

        if response.status_code != 200:
            print(f"FAIL - HTTP {response.status_code}")
            print(response.text)
            continue

        result = response.json()

        category_ok = (
            result["category"]
            == case["expected"]["category"]
        )

        urgency_ok = (
            result["urgency"]
            == case["expected"]["urgency"]
        )

        if category_ok and urgency_ok:
            passed += 1
            print("PASS")
        else:
            print("FAIL")

        print(
            f"Expected: "
            f"{case['expected']['category']} / "
            f"{case['expected']['urgency']}"
        )

        print(
            f"Actual: "
            f"{result['category']} / "
            f"{result['urgency']}"
        )

    score = passed / len(cases) * 100

    print("\n" + "=" * 60)
    print(f"RESULT: {passed}/{len(cases)}")
    print(f"SCORE: {score:.1f}%")
    print(
        "DATE:",
        datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )
    print("=" * 60)


if __name__ == "__main__":
    main()