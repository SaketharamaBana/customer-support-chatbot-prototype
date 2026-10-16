"""Interactive CLI for NimbusBot: python main.py [--prompt v1|v2]"""
import argparse
import sys

from chatbot import Chatbot


def main():
    parser = argparse.ArgumentParser(description="NimbusBot CLI - Support chatbot for NimbusDrive")
    parser.add_argument(
        "--prompt",
        default="v2",
        choices=["v1", "v2"],
        help="Prompt version to use (v1 or v2, default: v2)",
    )
    args = parser.parse_args()

    try:
        bot = Chatbot(prompt_version=args.prompt)
    except Exception as e:
        print(f"Error initializing Chatbot: {e}")
        print("Please check that ANTHROPIC_API_KEY is set in your environment or .env file.")
        sys.exit(1)

    print(f"NimbusBot (prompt {args.prompt}). Type 'quit' to exit, 'reset' to clear history.\n")
    while True:
        try:
            text = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        if text.lower() in {"quit", "exit"}:
            print("Goodbye!")
            break
        if text.lower() == "reset":
            bot.reset()
            print("(history cleared)\n")
            continue
        if text:
            print(f"Bot: {bot.ask(text)}\n")


if __name__ == "__main__":
    main()
