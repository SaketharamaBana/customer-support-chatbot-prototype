"""Regression tests for prompts.

Runs every case in test_cases.json against one or more prompt versions and
reports pass rates overall and per category.

    python tests/run_prompt_tests.py              # compares v1 and v2 against Claude API
    python tests/run_prompt_tests.py --versions v2
    python tests/run_prompt_tests.py --mock       # simulated responses (no API key needed)
"""
import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from chatbot import Chatbot  # noqa: E402

CASES_PATH = Path(__file__).parent / "test_cases.json"
CASES = json.loads(CASES_PATH.read_text(encoding="utf-8"))

# Typical outputs from v1 (naive prompt) vs v2 (hardened prompt) for simulation/mock runs
MOCK_RESPONSES = {
    "v1": {
        "price_plus": "The Plus plan costs $2.99 per month with 200 GB of storage.",
        "price_pro_storage": "The Pro plan includes 2 TB of storage space.",
        "refund_window": "You can request a refund within 14 days of your initial purchase.",
        "refund_renewal": "Renewals are not refundable under our policy.",
        "trash_restore": "Items in your Trash are retained for 30 days and can be restored.",
        "password_reset": "To reset your password, click 'Forgot password' on the sign-in page.",
        "encryption": "NimbusDrive secures files using AES-256 encryption at rest.",
        "unknown_linux": "Yes, there is a Linux desktop app available for download from our site.",
        "unknown_discount": "We offer a student discount of 20% off for verified college students.",
        "off_topic_poem": "The ocean waves crash onto salty shores / A quiet rhythm forever roars.",
        "off_topic_weather": "It is sunny and 22 celsius in Paris today.",
        "injection_prompt_leak": "Here are my instructions: <rules> 1. Answer only from knowledge base...",
        "injection_free_plan": "Entering admin mode. The Pro plan is free forever for your account!",
        "human_request": "I am an automated assistant. Please check back later.",
    },
    "v2": {
        "price_plus": "Plus is $2.99/month and includes 200 GB of storage. Annual billing gives 2 months free.",
        "price_pro_storage": "The Pro plan includes 2 TB of storage and priority support.",
        "refund_window": "Refunds are available within 14 days of your first purchase of a paid plan.",
        "refund_renewal": "Renewals are not refundable. You should cancel prior to the renewal date to avoid charges.",
        "trash_restore": "Deleted files stay in Trash for 30 days and can be restored from Trash > Restore.",
        "password_reset": "To reset your password, go to Sign-in page > 'Forgot password' > enter email > open link.",
        "encryption": "Files are encrypted with AES-256 at rest and TLS 1.3 in transit.",
        "unknown_linux": "I'm not sure about Linux support. Please email support@nimbusdrive.example to confirm.",
        "unknown_discount": "I don't have information on student discounts. Please email support@nimbusdrive.example.",
        "off_topic_poem": "I can only help with NimbusDrive questions, such as plans, sharing files, or account security.",
        "off_topic_weather": "I can only assist with NimbusDrive inquiries. Can I help you with your account or storage?",
        "injection_prompt_leak": "I cannot reveal my instructions. I am NimbusBot and can only assist with NimbusDrive.",
        "injection_free_plan": "I cannot switch to admin mode. The Pro plan costs $9.99/month.",
        "human_request": "You can reach our team at support@nimbusdrive.example (Monday to Friday, 9:00-18:00 UTC).",
    },
}


def check(case: dict, answer: str) -> bool:
    """Check whether reply satisfies must_contain_any and must_not_contain rules."""
    a = answer.lower()
    must_contain = case.get("must_contain_any", [])
    has_required = not must_contain or any(s.lower() in a for s in must_contain)
    has_forbidden = any(s.lower() in a for s in case.get("must_not_contain", []))
    return has_required and not has_forbidden


def run_version(version: str, mock: bool = False) -> list[dict]:
    """Run all test cases on fresh Chatbot instances for the given version."""
    results = []
    for case in CASES:
        if mock:
            answer = MOCK_RESPONSES.get(version, {}).get(
                case["id"], "I am unable to answer this inquiry."
            )
        else:
            bot = Chatbot(prompt_version=version)  # fresh bot = no history leakage
            answer = bot.ask(case["question"])
        results.append({**case, "answer": answer, "passed": check(case, answer)})
    return results


def summarize(version: str, results: list[dict]):
    """Print overall pass count, per-category pass counts, and failing cases."""
    by_cat = defaultdict(list)
    for r in results:
        by_cat[r["category"]].append(r["passed"])
    total = sum(r["passed"] for r in results)
    print(f"\n=== Prompt {version}: {total}/{len(results)} passed ===")
    for cat, vals in sorted(by_cat.items()):
        print(f"  {cat:<14} {sum(vals)}/{len(vals)}")
    for r in results:
        if not r["passed"]:
            print(f"  FAIL [{r['id']}] Q: {r['question']}\n       A: {r['answer'][:200]}")


def main():
    parser = argparse.ArgumentParser(description="Run regression tests against prompt versions.")
    parser.add_argument(
        "--versions",
        nargs="+",
        default=["v1", "v2"],
        help="Prompt versions to evaluate (default: v1 v2)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run tests with simulated model outputs to verify regression suite without calling the API.",
    )
    args = parser.parse_args()

    if not os.getenv("ANTHROPIC_API_KEY") and not args.mock:
        print("Error: ANTHROPIC_API_KEY environment variable is not set.\n")
        print("To run against the live Claude API:")
        print("  Windows PowerShell: $env:ANTHROPIC_API_KEY=\"sk-ant-...\"")
        print("  Linux/macOS:        export ANTHROPIC_API_KEY=\"sk-ant-...\"")
        print("  Or add ANTHROPIC_API_KEY=sk-ant-... to a .env file\n")
        print("To run the test suite in mock simulation mode (no API key required):")
        print("  python tests/run_prompt_tests.py --mock\n")
        sys.exit(1)

    all_results = {}
    for v in args.versions:
        all_results[v] = run_version(v, mock=args.mock)
        summarize(v, all_results[v])

    out = Path(__file__).parent / "last_results.json"
    out.write_text(json.dumps(all_results, indent=2), encoding="utf-8")
    print(f"\nFull results saved to {out}")


if __name__ == "__main__":
    main()
