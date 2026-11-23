# Claude Code project instructions

@AGENTS.md

Read MEMORY.md when continuing work, and update it after meaningful progress or decisions. This is shared project history; Claude's private automatic memory is separate.

Operating under a **$100 USD Claude API (pay-as-you-go)** budget (see `agent_docs/claude_api_budget.md`):
- Default to Sonnet at `medium` effort; only escalate to Sonnet `high` for core algorithms/initial Cockpit UI, and reserve Opus strictly for schema planning or bugs stuck after 2 Sonnet attempts.
- Keep sessions tight: read only the 1-3 files relevant to the active task, run targeted `pytest` files before the full suite, and remind the user to run `/cost` and `/clear` after completing each feature.
- Do not spend Claude API tokens writing long prose assets (`app/seeds/*.json`, `TERMS.md`, `README.md`) unless explicitly requested; suggest offloading those to Gemini or LM Studio.

Use the relevant files in `agent_docs/` for implementation, anti-slop UI guardrails, safe Git rules, and testing. Continue through already authorized local work, explain the code logic in 3-5 plain Indonesian lines for the DDP1 team, and report actual verification and remaining blockers.
