# History

## Goal

Clarify message-history ownership and usage in QitOS.

## Ownership

History belongs to `AgentModule` (`self.history`) or falls back to engine runtime history.

## History contract

`History` provides:

- `append(message)`
- `retrieve(query, state, observation)`
- `summarize(max_items)`
- `reset(run_id)`

## Engine usage

In default model path (`decide -> None`), Engine assembles messages as:

1. `system` (optional)
2. selected `history` messages (by `history_policy`)
3. current `user` message from `prepare(state)`

Engine appends current user/assistant turns into history.

Engine now also passes token-aware query hints into history by default:

- `pending_content`
- `model_name`
- `step_id`
- `max_tokens` (effective history budget after system/user reserve)
- `warning_ratio`

Typical history stream:

- `system`
- `user`
- `assistant`
- `user`
- `assistant`
- ...

## HistoryPolicy

Configure on the runtime call:

- `roles`
- `max_messages`
- `step_window`
- `max_tokens`
- extra query context such as `pending_content`, `model_name`, `phase`, and `query_kind`

Typical happy path:

```python
agent.run(
    task="do something",
    workspace="./playground",
    history_policy=HistoryPolicy(max_messages=12),
)
```

## CompactHistory

Use `CompactHistory` when you want the framework to compact model-facing context automatically instead of relying on a raw sliding window.

`CompactHistory` is also the default runtime history for LLM agents that do not provide a custom history. It adds:

- threshold warning metadata before the history exceeds the budget
- microcompact for older long messages and tool-heavy blobs
- continuation summary compaction for earlier rounds
- canonical `context_history` runtime events in trace/qita
- per-message metadata for summary / compacted history slices

Typical usage:

```python
from qitos import HistoryPolicy
from qitos.kit import CompactHistory

agent.history = CompactHistory(llm=llm, max_tokens=2200, keep_last_rounds=2)

agent.run(
    task="fix the bug",
    workspace="./playground",
    history_policy=HistoryPolicy(max_messages=16, max_tokens=2200),
)
```

See the focused example:

- `examples/real/react_compact_agent.py`

## Source Index

- [qitos/core/history.py](https://github.com/Qitor/qitos/blob/main/qitos/core/history.py)
- [qitos/engine/engine.py](https://github.com/Qitor/qitos/blob/main/qitos/engine/engine.py)
- [qitos/kit/history/window_history.py](https://github.com/Qitor/qitos/blob/main/qitos/kit/history/window_history.py)
- [qitos/kit/history/compact_history.py](https://github.com/Qitor/qitos/blob/main/qitos/kit/history/compact_history.py)
