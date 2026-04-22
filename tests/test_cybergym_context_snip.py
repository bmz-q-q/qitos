from __future__ import annotations

from pathlib import Path

from qitos.benchmark.cybergym.agent.context import SnipCompactor
from qitos.core.history import HistoryMessage
from qitos.core.state import StateSchema


def test_snip_compactor_persists_old_tool_results_with_preview(tmp_path: Path) -> None:
    state = StateSchema(task="demo")
    state.metadata["trace_run_dir"] = str(tmp_path / "trace")

    older = "HEAD line\n" + ("A" * 600) + "\nTAIL line"
    recent = "recent tool output"
    messages = [
        HistoryMessage(role="tool", content=older, step_id=1, metadata={"source": "engine"}),
        HistoryMessage(role="assistant", content="thinking", step_id=1),
        HistoryMessage(role="tool", content=recent, step_id=2, metadata={"source": "engine"}),
    ]

    result = SnipCompactor(keep_recent=1).snip(messages, state=state)

    assert result[0].metadata.get("snipped") is True
    assert result[0].metadata.get("snip_saved_path")
    assert "saved_path:" in str(result[0].content)
    assert "preview_head:" in str(result[0].content)
    assert "preview_tail:" in str(result[0].content)

    saved_path = Path(str(result[0].metadata["snip_saved_path"]))
    assert saved_path.exists()
    assert saved_path.read_text(encoding="utf-8") == older

    assert result[2].content == recent
    assert result[2].metadata.get("snipped") is None
