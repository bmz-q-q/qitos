# QitOS AGENT.md

This file is the durable working agreement for Codex and other AI coding agents operating in this repository.

Keep this file high-signal:
- put repository-wide rules here
- put directory-specific rules in nested `AGENTS.md` or `AGENTS.override.md`
- prefer concrete commands, constraints, and acceptance criteria over slogans

## 1. Mission

QitOS is a research-first, builder-friendly agent framework centered on one canonical kernel:
- `AgentModule + Engine`
- explicit lifecycle: `observe -> decide -> act -> reduce -> check_stop`

The quality bar is not MVP. Changes should move QitOS toward world-class open-source framework quality in:
- architecture clarity
- modularity and extensibility
- reproducibility and observability
- developer ergonomics
- documentation quality

## 2. Architecture Invariants

These are non-negotiable:

- Keep a single mainline architecture. Do not introduce parallel architecture tracks.
- Do not create `V1`, `V2`, `Legacy`, `Next`, or alias-based duplicate concepts in core APIs.
- Keep stable contracts in `qitos.core`; put replaceable concrete implementations in `qitos.kit`.
- Preserve the `AgentModule + Engine` story as the primary public mental model.
- Prefer explicit contracts and hook points over hidden magic.
- Do not reduce trace clarity, stop-reason clarity, or `qita` replay/export usefulness.

## 3. Package Boundaries

Use these boundaries strictly:

- `qitos.core`: abstract contracts, canonical data types, stable framework primitives
- `qitos.engine`: execution kernel, loop mechanics, hooks, validation, recovery, stop logic, action execution
- `qitos.kit`: concrete reusable implementations such as tools, memory, parser, planning, critic, env helpers, prompts
- `qitos.benchmark`: adapters that turn external benchmarks into canonical `Task`
- `examples`: runnable reference agents and benchmark runners
- `docs`: educational and operational documentation

Rule of thumb:
- if it is concrete or swappable, prefer `qitos.kit`
- if it is a stable contract, keep it in `qitos.core`

## 4. How To Work In This Repo

- Treat Codex like a configured teammate, not a one-off assistant. Keep instructions durable and reusable.
- Start by reading the relevant files and constraints before editing. Batch reads when possible.
- Keep changes scoped. Avoid opportunistic cleanup unless it directly unblocks the task.
- Do not revert or overwrite unrelated user changes.
- Never use destructive git commands such as `git reset --hard` or `git checkout --` unless explicitly requested.
- Do not amend commits unless explicitly requested.
- Ask before making decisions with hidden product or ecosystem cost:
  - adding production dependencies
  - changing public exports
  - changing canonical contracts
  - deleting or renaming public modules
  - changing packaging or release behavior

## 5. Codex-Specific Best Practices

When using Codex in this repository:

- Give the agent concrete context: target files, expected behavior, constraints, and validation commands.
- Prefer durable guidance in `AGENT.md` over repeating the same instructions in every prompt.
- Keep repository instructions concise and operational; add nested overrides only near specialized subsystems.
- Validate real outcomes after edits instead of stopping at analysis or code generation.
- Turn repeated workflows into reusable skills, scripts, or automation only after the workflow is stable.

For OpenAI-, ChatGPT-, or Codex-related questions:
- Always use the OpenAI developer documentation MCP server first if available.
- If MCP is unavailable, fall back only to official OpenAI docs domains.
- Do not rely on memory alone for volatile OpenAI product guidance.

Recommended MCP server name:
- `openaiDeveloperDocs`

Recommended instruction:
- Always use the OpenAI developer documentation MCP server if you need to work with the OpenAI API, ChatGPT Apps SDK, Codex, or related OpenAI tooling without being explicitly asked.

## 6. Validation Requirements

For non-trivial code changes, run the relevant validations before finishing.

Default project validations:

```bash
pytest -q
```

Stable-surface static checks:

```bash
flake8 qitos/core qitos/engine qitos/models qitos/trace
mypy qitos/core qitos/engine qitos/models qitos/trace
```

Packaging checks when changing packaging, distribution, or release-facing behavior:

```bash
python -m build
python -m twine check dist/*
```

If behavior changes in examples, benchmarks, docs tooling, or `qita`, also run at least one representative path for the changed area.

## 7. Tooling And Contract Rules

- Class-based tools should implement `execute(args, runtime_context)`.
- `run(...)` exists as a compatibility path, not as the preferred new contract.
- Function-style tools should continue to use the canonical decorator path.
- Tool behavior should remain composable through `ToolRegistry`.
- Env-backed operations should consume env ops rather than assuming host filesystem/process access directly.

## 8. Observability And Reproducibility

Do not ship changes that degrade:

- trace schema consistency
- hook payload usefulness
- `run_id`, `step_id`, and `phase` clarity
- replayability through `qita`
- final result and stop reason auditability

Every major feature should preserve or improve observability.

## 9. Benchmarks, Examples, And Docs

Benchmark rules:
- convert benchmark inputs into canonical `Task`
- keep benchmark-specific hacks out of core
- preserve useful raw fields in metadata
- keep adapters in `qitos.benchmark`
- provide runnable examples where practical

Example rules:
- examples are product surface, not toy snippets
- each example should run end-to-end on a real path
- examples should teach one clear pattern
- credentials must come from environment variables

Docs rules:
- update docs when public behavior, contracts, or user workflows change
- keep English and Chinese docs reasonably aligned when both exist
- prefer constructive walkthroughs over command dumps

## 10. Changelog Discipline

When a change is user-facing, migration-relevant, or materially affects maintainability:
- update `CHANGELOG.md`
- use high-signal entries under `Unreleased`
- prefer `Added`, `Changed`, `Fixed`, `Deprecated`, `Removed`, and `Breaking`

Do not treat the changelog as a commit log. Summarize impact, not every file touched.

## 11. Preferred Decision Heuristic

When uncertain, choose the option that:

1. keeps `AgentModule + Engine` simpler
2. improves researcher iteration speed
3. improves traceability and debuggability
4. preserves modular extension through `qitos.kit`
5. avoids architecture forks and surface-area sprawl

If a proposal violates this file, revise the design before coding.
