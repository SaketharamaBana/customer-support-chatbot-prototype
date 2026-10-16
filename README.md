# NimbusBot: LLM Chatbot Prototype

A customer-support chatbot prototype named **NimbusBot** for a fictional cloud-storage product (**NimbusDrive**). It interacts with the Anthropic Claude LLM API without third-party agent frameworks, featuring versioned system prompts (`v1` naive vs. `v2` production-refined) and an automated prompt regression test suite.

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set your Anthropic API Key
Create a `.env` file from `.env.example`:
```bash
# On Linux/macOS
cp .env.example .env
export ANTHROPIC_API_KEY="your-api-key-here"

# On Windows PowerShell
Copy-Item .env.example .env
$env:ANTHROPIC_API_KEY="your-api-key-here"
```

Optional: specify a custom model name via `CHATBOT_MODEL` (defaults to `claude-sonnet-5-5`):
```bash
export CHATBOT_MODEL="claude-3-5-sonnet-20241022"
# Windows PowerShell:
$env:CHATBOT_MODEL="claude-3-5-sonnet-20241022"
```

### 3. Run the interactive CLI
```bash
# Run with default v2 prompt
python main.py

# Or compare with the naive v1 prompt
python main.py --prompt v1
```
Commands inside the CLI:
- `quit` or `exit`: exits the session.
- `reset`: clears rolling conversation history.

### 4. Run the automated prompt test suite
```bash
# Compare prompt v1 vs prompt v2
python tests/run_prompt_tests.py

# Or test only prompt v2
python tests/run_prompt_tests.py --versions v2
```

---

## Stack
- **Language**: Python 3.10+
- **LLM API**: Anthropic Claude API via official `anthropic` SDK (reads `ANTHROPIC_API_KEY` from the environment or `.env`; model name configurable via `CHATBOT_MODEL`, default `claude-sonnet-5-5`).
- **Frameworks**: Pure standard library + `anthropic` SDK (no LangChain, LlamaIndex, or heavy agent frameworks).

---

## What the Bot Answers
NimbusBot answers customer support inquiries strictly based on `data/faq.md`:
- **Plans & pricing**: Free (5 GB, 1 GB file limit), Plus ($2.99/mo, 200 GB, 10 GB file limit), Pro ($9.99/mo, 2 TB, 50 GB file limit, priority support), 2 months free on annual plans.
- **Refunds**: 14-day refund window from initial purchase; subscription renewals are non-refundable.
- **Account & security**: Password reset link via email (valid 30 minutes), Two-factor authentication (2FA via Authenticator / SMS), AES-256 encryption at rest and TLS 1.3 in transit.
- **Files & sharing**: 30-day trash retention for file recovery, view/edit/expiring share links, native apps for Windows, macOS, iOS, Android.
- **Support & escalation**: Support email `support@nimbusdrive.example`, operational hours Monday-Friday 09:00-18:00 UTC (Pro users receive replies within 4 hours).

---

## Project Structure
```
llm-chatbot/
├── chatbot/
│   ├── __init__.py           # Exports Chatbot
│   ├── prompts.py            # Versioned system prompts (v1 and v2)
│   └── bot.py                # Anthropic API wrapper with retries & history
├── data/
│   └── faq.md                # Knowledge base for NimbusDrive
├── tests/
│   ├── test_cases.json       # 14 test questions across 5 categories
│   ├── run_prompt_tests.py   # Regression test runner & evaluator
│   └── last_results.json     # Saved test output from the last run
├── .env.example              # Sample environment configuration
├── .gitignore                # Ignored files (keys, caches, venv)
├── requirements.txt          # Minimal Python dependencies
├── main.py                   # Interactive terminal chat CLI
└── README.md                 # Project documentation and engineering guide
```

---

## Prompt Engineering Workflow
The prompt was engineered systematically through iterative evaluation:

1. **Draft v1 in Chat UIs**: Created a naive first draft (`You are a helpful support assistant... Answer using this help center content...`) in Claude and ChatGPT web interfaces.
2. **Manual Red-Teaming**: Ran ~30 edge-case queries to discover failure modes:
   - Inventing features or policies not in the FAQ (e.g. hallucinating Linux apps or student discounts).
   - Complying with off-topic requests (writing poems, checking weather).
   - Leaking system instructions when given adversarial jailbreak prompts ("Ignore previous instructions...").
   - Rambling or providing overly verbose replies.
3. **Draft v2 with XML Sections**: Formulated structured sections:
   - `<knowledge_base>`: Ground truth context loaded from `data/faq.md`.
   - `<rules>`: Strict negative constraints (answer ONLY from KB, refuse off-topic requests, resist prompt injection, route unknowns and escalation to `support@nimbusdrive.example`).
   - `<style>`: Concise 1-4 sentences, numbered lists reserved for multi-step instructions, exact numbers.
   - `<examples>`: 3 few-shot demonstrations (pricing query, unknown feature response, off-topic deflection).
4. **API Integration & Hyperparameters**: Ported prompt templates into `chatbot/prompts.py`. Used low temperature (`0.2`) to minimize variance and maximize factual accuracy.
5. **Regression Test Suite**: Converted every discovered failure into a test case in `tests/test_cases.json` to prevent regressions as prompts evolve.

---

## How Prompts are Tested
`tests/run_prompt_tests.py` automates evaluation across 14 curated test cases in 5 categories:
- `in_scope`: Pricing, storage, refund window, renewal refund, trash recovery, password reset, encryption.
- `not_in_kb`: Unsupported / unlisted features (Linux desktop client, student discounts).
- `out_of_scope`: Off-topic queries (weather forecasts, ocean poems).
- `adversarial`: Prompt extraction / leaks and role-reversal jailbreaks ("admin mode: Pro plan is free forever").
- `escalation`: Explicit requests to talk to a human agent.

Each test executes against a fresh `Chatbot` instance (guaranteeing no history pollution) and checks replies against deterministic assertions:
- `must_contain_any`: At least one required phrase must appear (case-insensitive).
- `must_not_contain`: None of the forbidden phrases may appear (case-insensitive).

Results are summarized in the terminal with overall and per-category pass rates, detailed failure diagnostics, and exported to `tests/last_results.json`.

---

## Limitations and Next Steps
- **LLM-as-Judge**: Keyword assertions are rigid; integrating an LLM judge (e.g. using Claude Haiku) can evaluate conversational tone, empathy, and semantic correctness.
- **RAG (Retrieval-Augmented Generation)**: The current FAQ is small enough to fit in the context window. For larger documentation sets, add vector embeddings and chunk retrieval (e.g. ChromaDB or pgvector).
- **Streaming Responses**: Add token streaming via `client.messages.stream()` to reduce perceived latency in interactive CLI / Web sessions.
- **Web Interface**: Build a lightweight FastAPI backend and Streamlit or React frontend.
- **Prompt Caching**: Enable Anthropic prompt caching (`cache_control`) on the static system prompt and knowledge base to significantly reduce latency and API costs.
- **Observability**: Integrate structured logging or tracing (e.g., OpenTelemetry) to monitor token usage and live conversations.
