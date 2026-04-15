# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Install dependencies:**
```bash
uv sync
```

**Run the LangGraph dev server (with Studio UI):**
```bash
uv run langgraph dev
```

**Run the FastAPI web server:**
```bash
uv run uvicorn web_server:app --reload
```

**Run all tests:**
```bash
python -m unittest discover -s tests
```

**Run a single test:**
```bash
python -m unittest tests.test_nodes.NodeTests.test_triage_router_parses_structured_json
```

**Docker Compose (full stack):**
```bash
docker compose up --build
```

## Architecture

This is a **LangGraph-based e-commerce customer support agent**. Every incoming chat message flows through a linear pipeline of graph nodes before reaching a specialized agent.

### Graph Flow (`graph/workflow.py`)

```
START → triage → policy_scope → policy_completeness → policy_risk
                                                            ↓
                                          [conditional routing]
                                        order_agent / billing_agent
                                        / fallback_agent / END (blocked)
                                                            ↓
                                                     tone_polisher → END
```

- **triage** (`triage_router.py`): Calls the LLM to classify the message into `category` (order/billing/account/technical/unknown), `priority` (low/medium/high), and `missing_fields`. Has a keyword-based fallback if LLM returns invalid JSON.
- **policy_scope** (`policy_scope_guard.py`): Blocks out-of-scope categories (account, technical, unknown → `OUT_OF_SCOPE`).
- **policy_completeness** (`policy_completeness_guard.py`): Blocks if `missing_fields` is non-empty → `NEED_MORE_INFO`.
- **policy_risk** (`policy_risk_guard.py`): Sets `escalation_required=True` for high-priority billing cases.
- **order_agent / billing_agent**: Specialized LLM agents. They pull mock context from `graph/adapters/` and reference `BUSINESS_POLICIES` from `graph/policy_catalog.py`.
- **fallback_agent**: Returns static canned responses for account/technical/unknown categories that passed scope guard.
- **tone_polisher**: Post-processes the `final_reply` for consistent tone before it reaches the caller.

### State (`graph/state.py`)

All nodes communicate via `GraphState` (a `TypedDict`). Key fields:
- `messages` — full conversation history (LangGraph `add_messages` reducer)
- `category`, `priority`, `missing_fields` — set by triage
- `policy_status`, `policy_message` — set by policy guards (`VALID` / `OUT_OF_SCOPE` / `NEED_MORE_INFO`)
- `escalation_required` — set by risk guard
- `final_reply` — the outbound customer-facing text

### LLM Client (`graph/llm/client.py`)

Priority-based model routing:
- `low` / `medium` → `gpt-3.5-turbo-0125`
- `high` → `gpt-4o`

Triage always uses the low-cost model. Agents use the model matched to the request's priority.

### Entry Points

| File | Purpose |
|------|---------|
| `web_server.py` | FastAPI app; `POST /api/chat`, `GET /health`, serves `web/` static frontend |
| `lang_cli.py` | LangGraph Studio entry point (`uv run langgraph dev`) |
| `main.py` | CLI runner for local testing |

### Business Policies (`graph/policy_catalog.py`)

A static dict (`POLICY_CATALOG`) of named policies (refund window, return shipping, dispute window, etc.). Imported by agent nodes and injected directly into their prompts. To add or change a policy, edit this file.

### Adapters (`graph/adapters/`)

`order_repository.py` and `billing_repository.py` return mock/demo context (order status, payment status) that agent nodes inject into their prompts. These are the integration points to replace with real DB/API calls.

### Configuration (`graph/config.py`)

`get_settings()` (cached) reads from environment / `.env`:
- `DEMO_MODE=true` — disables API key auth
- `API_AUTH_ENABLED=false` — gates `X-Api-Key` header check
- `OPENAI_API_KEY` — required for LLM calls
- `POSTGRES_URI` — included for production deployment; not used by the app at runtime (MemorySaver is used for checkpointing)

Copy `.env.example` → `.env` to configure locally.
