"""Regression tests for prompts.

Runs every case in test_cases.json against one or more prompt versions and
reports pass rates overall and per category.

    python tests/run_prompt_tests.py              # compares v1 and v2
    python tests/run_prompt_tests.py --versions v2
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


def check(case: dict, answer: str) -> bool:
    """Check whether reply satisfies must_contain_any and must_not_contain rules."""
    a = answer.lower()
    must_contain = case.get("must_contain_any", [])
    has_required = not must_contain or any(s.lower() in a for s in must_contain)
    has_forbidden = any(s.lower() in a for s in case.get("must_not_contain", []))
    return has_required and not has_forbidden


def run_version(version: str) -> list[dict]:
    """Run all test cases on fresh Chatbot instances for the given version."""
    results = []
    for case in CASES:
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
    args = parser.parse_args()

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        print("Please set your API key before running tests:")
        print("  Windows PowerShell: $env:ANTHROPIC_API_KEY=\"sk-ant-...\"")
        print("  Linux/macOS:        export ANTHROPIC_API_KEY=\"sk-ant-...\"")
        print("  Or add ANTHROPIC_API_KEY=sk-ant-... to a .env file")
        sys.exit(1)

    all_results = {}
    for v in args.versions:
        all_results[v] = run_version(v)
        summarize(v, all_results[v])

    out = Path(__file__).parent / "last_results.json"
    out.write_text(json.dumps(all_results, indent=2), encoding="utf-8")
    print(f"\nFull results saved to {out}")


if __name__ == "__main__":
    main()
