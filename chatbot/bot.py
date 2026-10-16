"""Anthropic Claude API wrapper with rolling history and retry logic."""
import inspect
import os
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from anthropic import Anthropic, APIConnectionError, APIStatusError, RateLimitError

from .prompts import get_system_prompt

DEFAULT_MODEL = os.getenv("CHATBOT_MODEL", "claude-sonnet-5-5")


class Chatbot:
    """Wrapper around Anthropic Claude API: system prompt + rolling chat history."""

    def __init__(
        self,
        prompt_version: str = "v2",
        model: str = DEFAULT_MODEL,
        temperature: float = 0.2,
        max_tokens: int = 400,
        max_history: int = 10,
    ):
        self.client = Anthropic()  # reads ANTHROPIC_API_KEY from environment
        self.system = get_system_prompt(prompt_version)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_history = max_history  # number of messages kept (user + assistant)
        self.history: list[dict[str, str]] = []

        # Maintain compatibility across Anthropic SDK versions (v0.x vs v1.x+)
        sig = inspect.signature(self.client.messages.create)
        self._supports_direct_temp = "temperature" in sig.parameters

    def ask(self, user_message: str) -> str:
        """Send user message, receive assistant reply, and update history."""
        self.history.append({"role": "user", "content": user_message})
        trimmed = self.history[-self.max_history:]
        reply = self._call_api(trimmed)
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def reset(self):
        """Clear conversation history."""
        self.history = []

    def _call_api(self, messages: list[dict[str, str]], retries: int = 3) -> str:
        """Call Claude API with retries and exponential backoff for transient errors."""
        kwargs = {
            "model": self.model,
            "system": self.system,
            "messages": messages,
            "max_tokens": self.max_tokens,
        }
        if self.temperature is not None:
            if self._supports_direct_temp:
                kwargs["temperature"] = self.temperature
            else:
                kwargs["extra_body"] = {"temperature": self.temperature}

        for attempt in range(retries):
            try:
                resp = self.client.messages.create(**kwargs)
                return "".join(b.text for b in resp.content if b.type == "text").strip()
            except (RateLimitError, APIConnectionError):
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # exponential backoff: 1s, 2s...
            except APIStatusError as e:
                # Retry on 5xx server errors
                if e.status_code >= 500:
                    if attempt < retries - 1:
                        time.sleep(2 ** attempt)
                else:
                    raise
        return "Sorry, I'm having trouble right now. Please try again in a moment."
