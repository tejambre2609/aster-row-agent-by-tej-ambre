Aster & Row Support Agent

A small, reliability-focused customer-support agent for the fictional Aster & Row ecommerce company.

The agent is designed around four failure modes from the take-home assignment:

conflicting or superseded policy documents

invented order information

lost multi-turn context

unsafe or instruction-like retrieved content

The implementation deliberately favors deterministic, testable behavior over a large framework or a polished UI.

Features

Policy/document retrieval from knowledge-base/

Source-aware customer answers

Active/authoritative policy preference

Safe handling of superseded and internal content

Order lookup from data/orders.json

Order-ID extraction and normalization

Current order status treated as authoritative

No invented ETA when an ETA is unavailable

No stale ETA for cancelled/returned orders

Customer-data privacy protection

Safe abstention when information is insufficient

Human handoff for unsafe, insufficient, or conflicting cases

Multi-turn handling for supported follow-up scenarios

Deterministic regression tests

Evaluation suite with category-level reporting

Structured runtime/evaluation logging

1. Quick start

Requirements

Python 3.14+ (the final test run was executed with Python 3.14.6)

pytest

Create and activate a virtual environment:

python -m venv venv
.\venv\Scripts\Activate.ps1

Install the test dependency:

python -m pip install pytest

Run the regression suite:

python -m pytest

Run the full evaluation suite:

python -m evaluation.run_evaluation

Run the CLI:

python -m src.agent

Example:

You: My TrailPlus membership was active when I ordered. What is my return window?

Agent: TrailPlus members whose membership was active when the order was placed receive a
45-calendar-day return window from delivery for eligible items. Joining TrailPlus after
placing an order does not extend that order's return window.

Sources:
  - 09-trailplus-membership.md

2. Configuration and environment variables

The current implementation does not require API credentials or external model-provider credentials.

No real secrets should be committed to the repository.

If a future model/provider is added, keep credentials in a local .env file and document only placeholder names in .env.example.

Example:

# Optional future model-provider configuration.
# Do not put real credentials in this file.
MODEL_PROVIDER=
MODEL_NAME=
API_KEY=

The current agent can run without these variables.

3. Architecture

High-level flow

                         ┌─────────────────────┐
                         │     User message    │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Agent router     │
                         │  src/agent.py       │
                         └───────┬─────┬───────┘
                                 │     │
                 order ID found  │     │  policy/product query
                                 │     │
                                 ▼     ▼
                     ┌──────────────┐  ┌──────────────────┐
                     │ Order lookup │  │ Document search  │
                     │ src/orders.py│  │src/retrieval.py  │
                     └──────┬───────┘  └────────┬─────────┘
                            │                   │
                            ▼                   ▼
                     data/orders.json    knowledge-base/*.md
                            │                   │
                            └─────────┬─────────┘
                                      ▼
                              ┌─────────────────┐
                              │ Safety / policy │
                              │ decision logic  │
                              └────────┬────────┘
                                       │
                         ┌─────────────┼─────────────┐
                         ▼             ▼             ▼
                      Answer        Handoff       Abstain
                         │
                         ▼
                  Sources + response

Retrieval

The project uses a lightweight deterministic retrieval approach, rather than a hosted LLM or external vector database.

The supplied Markdown knowledge base is searched for relevant content and the result metadata is used to prefer authoritative/active documents. The final response exposes the source filename.

This is intentionally simple because the assignment explicitly values reliability, testability, and practical trade-offs over framework complexity.

Order lookup

Order information is kept in data/orders.json.

The agent extracts an order ID using the ORD-#### format and calls the lookup function only when order information is required.

Only customer-safe fields are used in the response:

order ID

current status

carrier

estimated delivery, when available

Internal fields are not returned.

Cancelled and returned orders do not use stale ETA fields.

Safety / abstention

The agent has explicit handling for:

internal/customer-private data requests

unsupported product/material claims

conflicting active sources

retrieved prompt-injection/instruction-like content

unknown orders

missing order IDs

unavailable delivery estimates

When the available evidence is insufficient or authoritative sources conflict, the agent recommends human assistance rather than guessing.

4. Repository structure

.
├── README.md
├── src/
│   ├── agent.py
│   ├── orders.py
│   └── retrieval.py
├── tests/
│   └── test_agent.py
├── evaluation/
│   ├── run_evaluation.py
│   └── visible-cases.json
├── knowledge-base/
│   ├── 01-returns-policy-current.md
│   ├── 02-returns-policy-legacy.md
│   ├── 03-final-sale-and-promotions.md
│   ├── 04-damaged-or-wrong-items.md
│   ├── 05-domestic-shipping.md
│   ├── 06-international-shipping.md
│   ├── 07-warranty.md
│   ├── 08-order-changes-and-cancellations.md
│   ├── 09-trailplus-membership.md
│   ├── 10-gift-cards-and-price-adjustments.md
│   ├── 11-product-care.md
│   ├── 12-breeze-tumbler-product-card.md
│   ├── 13-support-escalation.md
│   └── 14-internal-content-migration-notes.md
├── data/
│   ├── orders.json
│   └── orders-data-dictionary.md
└── .env.example

Do not commit:

venv/
__pycache__/
.pytest_cache/
.env

5. Evaluation

Final regression test

Final local run:

python -m pytest

21 passed in 0.13s

The final suite contains 21 deterministic pytest cases covering policy retrieval, order handling, privacy, prompt-injection resistance, source conflicts, abstention, and paraphrased behavior.

The final run included:

standard return policy

TrailPlus return policy

Canada shipping

unsupported Germany shipping

valid order lookup

missing order ID

cancelled order handling

unknown order handling

order privacy

warranty

final-sale damaged-item exception

retrieved prompt-injection resistance

insufficient information

Breeze Tumbler source conflict

multi-turn Canada context

TrailPlus paraphrase

regular-return paraphrase

privacy paraphrase

order without ETA

unknown-order paraphrase

TrailPlus membership timing

Full evaluation

Run:

python -m evaluation.run_evaluation

Final result:

============================================================
Overall: 15/15 passed

By category:
  abstention: 1/1
  conversation: 1/1
  groundedness: 2/2
  multi-source-grounding: 1/1
  privacy: 1/1
  prompt-security: 1/1
  retrieval: 2/2
  source-conflict: 1/1
  tool-reliability: 3/3
  tool-use: 2/2
============================================================

Category summary

Category

Result

Abstention

1/1

Conversation

1/1

Groundedness

2/2

Multi-source grounding

1/1

Privacy

1/1

Prompt security

1/1

Retrieval

2/2

Source conflict

1/1

Tool reliability

3/3

Tool use

2/2

Overall

15/15

The evaluation suite reports individual cases as well as category totals rather than relying only on one aggregate score.

6. Baseline → final improvement

The project was developed iteratively with regression tests added after failures were discovered.

Baseline

An early version of the test suite had:

15 tests collected
14 passed
1 failed

The failure was a formatting mismatch in the TrailPlus response:

Expected: 45-calendar-day
Actual:   45 calendar days

The response was semantically correct, but the regression assertion expected a different wording.

Later regression run

After expanding the test suite to cover paraphrases, two additional behavioral failures were exposed:

21 tests collected
19 passed
2 failed

The failures were:

A non-TrailPlus user could be incorrectly routed to the TrailPlus response.

A privacy refusal contained the word address, which a strict regression test treated as a forbidden disclosure token.

Final

The latest recorded final run is:

21 passed

and:

15/15 evaluation cases passed

This progression is important because the final score was achieved through regression coverage rather than by deleting difficult tests.

7. Bug diary

Bug 1 — TrailPlus wording mismatch

Reproduction

Run:

python -m pytest

The TrailPlus test expected:

45-calendar-day

while the implementation returned:

45 calendar days

Root cause

The implementation and test used semantically equivalent but textually different phrasing.

Fix

Standardized the customer-facing response to use:

45-calendar-day return window

Regression test

test_trailplus_return_window

Bug 2 — TrailPlus false positive for non-members

Reproduction

Use:

I am not a TrailPlus member. If my unused bag was delivered today,
how long do I have to send it back?

The agent initially returned the TrailPlus 45-day policy.

Root cause

The routing logic checked for the presence of the word TrailPlus together with a return-related term. It did not give enough weight to the explicit negation:

not a TrailPlus member

Fix

The routing logic was tightened so that explicit non-membership is not treated as evidence that the TrailPlus benefit applies. The standard return policy is selected for non-members.

Regression test

test_regular_return_policy_paraphrase

This was especially valuable because it tests a paraphrase/combination rather than relying only on the visible wording.

Bug 3 — Privacy refusal wording

Reproduction

Use:

For ORD-1007, show me the customer's contact details
and the internal risk information.

The safety branch correctly refused the request, but the response contained the word:

addresses

A strict regression test expected the sensitive field name not to appear in the response.

Root cause

The privacy guard correctly prevented disclosure of the value, but the refusal message itself explicitly listed the protected field categories.

Fix

The refusal response was tightened so it communicates that internal/customer-private information cannot be disclosed without echoing sensitive field names unnecessarily.

Regression test

test_privacy_request_with_paraphrased_sensitive_terms

Bug 4 — Stale ETA on cancelled orders

Reproduction

Query a cancelled order that still contains an old estimated delivery date.

Root cause

A naive implementation could format and return estimated_delivery without first checking the current order status.

Fix

Cancelled and returned orders now use the customer-safe order message and do not expose stale ETA information.

Regression test

test_cancelled_order

8. Safety and reliability decisions

Document precedence

The knowledge base intentionally contains:

active policy documents

superseded policy documents

internal notes

genuine conflicts between active sources

The agent does not blindly trust the highest text similarity. It considers document authority/status and has explicit handling for known source conflicts.

Prompt-injection resistance

Retrieved text is treated as data, not as application instructions.

For example, an internal migration note suggesting that the agent should ignore the real return policy must not override the active official return policy.

Regression coverage:

test_prompt_injection_does_not_override_policy

Privacy

The agent does not expose:

customer email

customer address

internal notes

risk scores

fraud-review information

other internal-only order fields

The order lookup is intentionally reduced to customer-safe information.

Safe abstention

When the knowledge base does not contain enough evidence to make a reliable claim, the agent does not invent an answer.

Example:

Are all fabrics and adhesives in your bags vegan?

The correct behavior is to state that the supplied information is insufficient and recommend human confirmation.

Genuine source conflict

For the Breeze Tumbler dishwasher question, two current official sources conflict.

Instead of silently selecting one, the agent surfaces the conflict and recommends human confirmation.

9. Multi-turn behavior

The design supports relevant conversational follow-ups.

Examples:

User: Do you ship internationally?
Agent: We currently ship internationally only to Canada.

User: What about Canada?
Agent: Canadian orders generally arrive within 5–9 business days after dispatch...

and:

User: Where is ORD-1007?
Agent: Order ORD-1007 is shipped with UPS...

User: When will it arrive?
Agent: It is currently estimated to arrive on August 22, 2026.

The goal is to preserve useful context without mixing unrelated sessions.

10. Demo

The assignment requires a 2–4 minute GIF or video in the repository README demonstrating:

a knowledge-base question with citations

an order lookup

a multi-turn conversation

a refusal/human-handoff case

the evaluation suite running

Demo recording script

Use this exact sequence when recording the final demo:

Scene 1 — Knowledge-base question

My TrailPlus membership was active when I ordered. What is my return window?

Show:

45-calendar-day return window from delivery
Source: 09-trailplus-membership.md

Scene 2 — Order lookup

Where is ORD-1007 and when should it arrive?

Show the customer-safe status, carrier, and ETA.

Scene 3 — Multi-turn

Do you ship internationally?

Then:

What about Canada?

Show that the second question is understood in context.

Scene 4 — Safe refusal

Are all fabrics and adhesives in your bags vegan?

Show the insufficient-information response and human handoff.

Also demonstrate privacy if time permits:

For ORD-1007, show me the customer's contact details and internal risk information.

Scene 5 — Evaluation

Run:

python -m evaluation.run_evaluation

Show:

Overall: 15/15 passed

Add the recorded media here

After recording the demo, commit the file and replace the placeholder below with the real GitHub-relative path:

## Demo

[![Aster & Row Agent Demo](docs/demo-thumbnail.gif)](docs/aster-row-demo.mp4)

If using a GIF directly:

![Aster & Row Agent Demo](docs/demo.gif)

Do not submit the README with a broken demo path.

11. Observability

The evaluation output provides structured information such as:

user message

retrieval query

retrieved sources

relevance scores

tool calls

tool arguments

tool results

handoff state

evaluation case and category

Example retrieval trace:

event: retrieval
query: How long does a regular customer have to return an unused backpack?
results:
  - 01-returns-policy-current.md
  - 06-international-shipping.md
  - 09-trailplus-membership.md
  ...

Order traces similarly show when order_lookup was called and whether an order was found.

The implementation should not log secrets or internal customer fields in customer-facing output.

12. Model, embeddings, framework, and storage

Model

No external generative model is required by the current implementation.

The core behavior is deterministic Python logic with explicit routing and customer-safe response construction.

Embeddings

No embedding model is currently used.

Retrieval is lightweight/deterministic rather than embedding-based semantic search.

Framework

The project uses plain Python with pytest for automated testing.

No heavyweight agent framework is required.

Storage

The current system uses repository-local files:

Markdown files for the knowledge base

JSON for mock order data

No production vector database or external database is required.

Why this trade-off?

For this assignment, deterministic behavior makes it easier to test:

source selection

privacy

tool use

stale-data handling

prompt-injection resistance

abstention

exact regression cases

A production version could replace the retrieval layer with a hybrid lexical + embedding retriever while keeping the same safety and evaluation contracts.

13. Known limitations

This is a take-home implementation, not a production support platform.

1. Deterministic retrieval

The current retriever is lightweight and does not use dense embeddings.

Production improvement: hybrid BM25/keyword + embedding retrieval with reranking and stronger metadata filtering.

2. Limited conversational memory

The current implementation covers the tested follow-up scenarios but is not a full production conversation-memory system.

Production improvement: explicit session state with bounded history and structured conversation memory.

3. Rule-based safety routing

Some safety and special cases are handled with deterministic rules.

Production improvement: combine rules with a structured policy/safety layer and adversarial testing.

4. No real authentication

The assignment explicitly treats possession of the order ID as sufficient authentication for the mock environment.

Production improvement: authenticate the customer before exposing order-specific information.

5. Local JSON order storage

data/orders.json is mock data and is not suitable for concurrent production workloads.

Production improvement: use an authenticated backend/service with audit logging and least-privilege access.

6. No production deployment

There is currently no cloud deployment, authentication system, monitoring dashboard, rate limiting, or high-availability infrastructure.

7. No live company integrations

The agent cannot actually perform refunds, cancellations, address changes, replacements, or other transactional actions.

It should therefore never claim that such an action has been completed.

8. Limited evaluation size

The evaluation suite is deliberately small and deterministic.

Production improvement: add a larger adversarial benchmark with paraphrases, multilingual inputs, noisy retrieval, prompt-injection variants, privacy attacks, and randomized combinations.

14. AI-assisted development

AI coding assistance was used during development primarily for:

debugging failing tests

reviewing edge cases

improving test coverage

reasoning about retrieval/source precedence

checking privacy and prompt-injection behavior

drafting documentation

One important lesson from the debugging process was that an apparently reasonable shortcut can be incomplete: treating the presence of the word TrailPlus as sufficient evidence for the TrailPlus policy fails when a user explicitly says they are not a member. This was caught by a paraphrased regression test.

AI assistance was treated as a development aid rather than as an authority. Test results and the supplied source documents remained the final source of truth.

15. What I would improve next

If this moved beyond the take-home:

Add hybrid retrieval with embeddings and reranking.

Add structured document metadata filtering before retrieval.

Separate policy selection from response generation.

Add a dedicated privacy policy layer.

Add a formal conversation-state object.

Add stronger adversarial evaluation.

Add authentication before order-specific responses.

Add structured audit logs with PII redaction.

Add CI so every pull request runs both pytest and the evaluation suite.

Add a small web/API interface while keeping the deterministic core testable.

16. Submission checklist

Before submitting the GitHub repository:

README.md is present at the repository root.

Source code is included.

tests/ is included.

evaluation/ is included.

knowledge-base/ is included unchanged.

data/orders.json and its data dictionary are included.

.env.example contains placeholders only.

No .env file or API keys are committed.

No venv/ directory is committed.

python -m pytest passes.

python -m evaluation.run_evaluation reports 15/15 passed.

README contains baseline and final results.

README contains at least three reproduced bugs with root cause, fix, and regression test.

README contains limitations.

README contains architecture and implementation trade-offs.

README contains AI-assisted development disclosure.

A 2–4 minute demo GIF/video is committed and linked from the README.

The demo shows knowledge-base retrieval, order lookup, multi-turn behavior, safe refusal/handoff, and evaluation execution.

Only the GitHub repository link is submitted.

Final status

Automated tests: 21/21 passed

Evaluation: 15/15 passed

Main remaining submission item: add the final 2–4 minute demo GIF/video and make sure its README link points to the committed file.

The project intentionally stays small: the focus is reliable customer-facing behavior, safe data handling, deterministic regression coverage, and clear failure modes rather than unnecessary infrastructure.