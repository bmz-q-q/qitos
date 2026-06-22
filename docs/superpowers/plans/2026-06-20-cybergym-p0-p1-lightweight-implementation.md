# CyberGym P0/P1 Lightweight Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement lightweight TaskSpec extraction, repo evidence ranking, candidate provenance strengthening, and failure taxonomy support for the CyberGym agent without changing its runtime architecture.

**Architecture:** Keep the existing `CyberGymAdapter -> CyberGymAgent.init_state() -> QitOS Engine loop` flow intact. Add one new helper module for TaskSpec extraction, enrich existing state/evidence/candidate structures, and inject only compact summaries into the prompt path. Preserve current submit flow, current single-main-agent design, and current fix-side leakage protections.

**Tech Stack:** Python dataclasses, existing QitOS tool/runtime abstractions, pytest

## Global Constraints

- Implement only P0.1, P0.2, P0.4, and P1.1 from the approved spec.
- Do not implement P0.3 or any other P1/P2 item.
- Do not add heavy dependencies such as tree-sitter or ctags.
- Do not add a new benchmark-time multi-agent orchestration layer.
- Do not require an extra LLM round-trip on every task; TaskSpec fallback must be optional and gated.
- Do not dump full structured objects into model-visible context.
- Do not rewire the QitOS `AgentModule + Engine` execution model.
- Keep the runtime single-main-agent and QitOS-compatible.
- Preserve current submit-result processing and current fix-side leakage protections.
- Keep the implementation lightweight: enhance existing structures and heuristics instead of adding a runtime redesign.

---

## File Structure

### New file
- `qitos/benchmark/cybergym/agent/task_spec.py` — deterministic-first task-spec extraction utilities and optional low-confidence fallback hook.

### Modified files
- `qitos/benchmark/cybergym/agent/state.py` — add flat task-spec and failure-history fields.
- `qitos/benchmark/cybergym/agent/family_runtime.py` — strengthen `CandidateRecord`, add `FailureType` / `FailureRecord`.
- `qitos/benchmark/cybergym/agent/evidence_selector.py` — enrich bootstrap evidence index with ranked paths and lightweight repo profiling.
- `qitos/benchmark/cybergym/agent/subagent_runtime.py` — accept optional candidate provenance fields in structured delegate output.
- `qitos/benchmark/cybergym/agent/agent.py` — integrate task-spec extraction, repo-map enrichment, candidate provenance defaults, and failure-record derivation into the current main flow.

### Test files to modify or create
- `tests/test_cybergym_agent_poc_profile.py` — extend for TaskSpec/state-level behavior if it already exercises CyberGymAgent bootstrap.
- `tests/test_cybergym_parallel_tools_prompt.py` — add compact-summary assertions only if needed for prompt visibility.
- `tests/test_engine_core_flow.py` — preserve submit sanitization / fix-side isolation invariants if touched indirectly.
- Create: `tests/test_cybergym_task_spec.py` — focused TaskSpec extraction tests.
- Create: `tests/test_cybergym_evidence_selector.py` — focused evidence ranking/profile tests.
- Create: `tests/test_cybergym_candidate_failure_records.py` — candidate provenance + failure taxonomy tests.

### Responsibilities
- `task_spec.py` owns extraction logic only; it must not create tasks or mutate runtime state.
- `state.py` remains the only canonical store for agent-visible lightweight task/failure summaries.
- `evidence_selector.py` remains the evidence bootstrap owner; do not create a second indexing subsystem.
- `family_runtime.py` remains the home of candidate/runtime helper dataclasses.
- `agent.py` remains the orchestrator and the only place where new structured data is wired into runtime decisions.

---

### Task 1: Add lightweight TaskSpec extraction module and state fields

**Files:**
- Create: `qitos/benchmark/cybergym/agent/task_spec.py`
- Modify: `qitos/benchmark/cybergym/agent/state.py`
- Test: `tests/test_cybergym_task_spec.py`

**Interfaces:**
- Consumes: raw task description string, optional `error_txt`, optional `patch_diff`, optional `harness_info`
- Produces:
  - `build_task_spec(description: str, *, error_txt: str = "", patch_diff: str = "", harness_info: str = "") -> dict[str, Any]`
  - `extract_task_spec_deterministic(description: str, *, error_txt: str = "", patch_diff: str = "", harness_info: str = "") -> dict[str, Any]`
  - new `CyberGymState` fields:
    - `vulnerability_class: str`
    - `expected_signal: str`
    - `input_vector_hints: List[str]`
    - `likely_entrypoints: List[str]`
    - `likely_fuzz_targets: List[str]`
    - `source_files_mentioned: List[str]`
    - `symbols_mentioned: List[str]`
    - `task_spec_confidence: float`

- [ ] **Step 1: Write the failing TaskSpec extraction tests**

```python
from qitos.benchmark.cybergym.agent.task_spec import build_task_spec


def test_build_task_spec_extracts_cve_signal_and_input_hints():
    spec = build_task_spec(
        "CVE-2024-12345 heap-buffer-overflow in png parser when opening crafted .png file under ASAN",
        error_txt="AddressSanitizer: heap-buffer-overflow",
        patch_diff="",
        harness_info="target binary reads a file path argument",
    )

    assert spec["cve_id"] == "CVE-2024-12345"
    assert spec["vulnerability_class"] == "memory-safety"
    assert spec["expected_signal"] == "ASAN"
    assert "file" in spec["input_vector_hints"]
    assert ".png" in spec["input_vector_hints"]
    assert spec["task_spec_confidence"] > 0


def test_build_task_spec_extracts_source_and_symbol_mentions_without_fabrication():
    spec = build_task_spec(
        "Crash occurs in parse_chunk while processing png/read.c with malformed IHDR block",
        error_txt="",
        patch_diff="",
        harness_info="",
    )

    assert "png/read.c" in spec["source_files_mentioned"]
    assert "parse_chunk" in spec["symbols_mentioned"]
    assert "unknown" not in spec["symbols_mentioned"]


def test_build_task_spec_defaults_to_unknown_like_empty_values_when_uncertain():
    spec = build_task_spec("General crash in binary parser", error_txt="", patch_diff="", harness_info="")

    assert isinstance(spec["likely_entrypoints"], list)
    assert isinstance(spec["likely_fuzz_targets"], list)
    assert isinstance(spec["input_vector_hints"], list)
    assert 0.0 <= spec["task_spec_confidence"] <= 1.0
```

- [ ] **Step 2: Run the new TaskSpec tests to verify they fail**

Run: `pytest tests/test_cybergym_task_spec.py -q`
Expected: FAIL with `ModuleNotFoundError` or missing symbol errors for `qitos.benchmark.cybergym.agent.task_spec`

- [ ] **Step 3: Create `task_spec.py` with deterministic-first extraction**

```python
from __future__ import annotations

import re
from typing import Any

_CVE_RE = re.compile(r"CVE-\d{4}-\d{4,}", re.IGNORECASE)
_FILE_RE = re.compile(r"\b[\w./-]+\.(?:c|cc|cpp|cxx|h|hpp|rs|go|java|py|js|ts|png|jpg|gif|pdf|xml|json|yaml|yml|bin)\b")
_SYMBOL_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]{2,}\b")

_MEMORY_TERMS = (
    "heap-buffer-overflow",
    "stack-buffer-overflow",
    "use-after-free",
    "double free",
    "out-of-bounds",
    "buffer overflow",
)

_PARSER_TERMS = ("parser", "parse", "decode", "reader", "chunk", "header")

_SIGNAL_PATTERNS = {
    "ASAN": ("asan", "addresssanitizer", "heap-buffer-overflow", "stack-buffer-overflow"),
    "UBSAN": ("ubsan", "undefinedbehaviorsanitizer", "undefined behavior"),
    "MSAN": ("msan", "memorysanitizer"),
    "CRASH": ("crash", "segmentation fault", "segfault", "assertion"),
}


def _uniq(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        value = str(item or "").strip()
        if not value:
            continue
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _detect_signal(text: str) -> str:
    lowered = text.lower()
    for label, patterns in _SIGNAL_PATTERNS.items():
        if any(pattern in lowered for pattern in patterns):
            return label
    return "unknown"


def _detect_vulnerability_class(text: str) -> str:
    lowered = text.lower()
    if any(term in lowered for term in _MEMORY_TERMS):
        return "memory-safety"
    if any(term in lowered for term in _PARSER_TERMS):
        return "parser"
    return "unknown"


def _input_hints(text: str, harness_info: str) -> list[str]:
    lowered = f"{text} {harness_info}".lower()
    hints: list[str] = []
    if "stdin" in lowered:
        hints.append("stdin")
    if "argv" in lowered or "argument" in lowered or "path" in lowered:
        hints.append("file")
    for ext in (".png", ".jpg", ".gif", ".pdf", ".xml", ".json", ".yaml", ".yml", ".bin"):
        if ext in lowered:
            hints.append(ext)
    return _uniq(hints)


def extract_task_spec_deterministic(
    description: str,
    *,
    error_txt: str = "",
    patch_diff: str = "",
    harness_info: str = "",
) -> dict[str, Any]:
    combined = "\n".join([description or "", error_txt or "", patch_diff or "", harness_info or ""])
    cve_match = _CVE_RE.search(combined)
    source_files = _uniq(_FILE_RE.findall(combined))
    symbol_candidates = [
        token for token in _SYMBOL_RE.findall(combined)
        if token.lower() not in {"crash", "parser", "binary", "file", "asan", "ubsan", "msan"}
    ]
    symbols = _uniq(symbol_candidates[:12])
    likely_entrypoints = [token for token in symbols if token.lower().startswith(("parse", "read", "decode"))][:6]
    likely_fuzz_targets = [path for path in source_files if "fuzz" in path.lower() or "fuzzer" in path.lower()][:6]

    confidence = 0.2
    if cve_match:
        confidence += 0.2
    if source_files:
        confidence += 0.2
    if likely_entrypoints:
        confidence += 0.2
    signal = _detect_signal(combined)
    if signal != "unknown":
        confidence += 0.2

    return {
        "cve_id": cve_match.group(0) if cve_match else "",
        "vulnerability_class": _detect_vulnerability_class(combined),
        "expected_signal": signal,
        "input_vector_hints": _input_hints(description or "", harness_info or ""),
        "likely_entrypoints": likely_entrypoints,
        "likely_fuzz_targets": likely_fuzz_targets,
        "source_files_mentioned": source_files[:12],
        "symbols_mentioned": symbols,
        "task_spec_confidence": max(0.0, min(confidence, 1.0)),
    }


def build_task_spec(
    description: str,
    *,
    error_txt: str = "",
    patch_diff: str = "",
    harness_info: str = "",
) -> dict[str, Any]:
    return extract_task_spec_deterministic(
        description,
        error_txt=error_txt,
        patch_diff=patch_diff,
        harness_info=harness_info,
    )
```

- [ ] **Step 4: Extend `CyberGymState` with the flat TaskSpec fields**

```python
# add near the existing stable task / investigation fields in CyberGymState
vulnerability_class: str = ""
expected_signal: str = ""
input_vector_hints: List[str] = field(default_factory=list)
likely_entrypoints: List[str] = field(default_factory=list)
likely_fuzz_targets: List[str] = field(default_factory=list)
source_files_mentioned: List[str] = field(default_factory=list)
symbols_mentioned: List[str] = field(default_factory=list)
task_spec_confidence: float = 0.0
```

- [ ] **Step 5: Run the TaskSpec tests to verify they pass**

Run: `pytest tests/test_cybergym_task_spec.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add \
  qitos/benchmark/cybergym/agent/task_spec.py \
  qitos/benchmark/cybergym/agent/state.py \
  tests/test_cybergym_task_spec.py
git commit -m "feat: add lightweight cybergym task spec extraction"
```

---

### Task 2: Integrate TaskSpec into `CyberGymAgent.init_state()` and keep prompt injection compact

**Files:**
- Modify: `qitos/benchmark/cybergym/agent/agent.py`
- Test: `tests/test_cybergym_agent_poc_profile.py`

**Interfaces:**
- Consumes:
  - `build_task_spec(description, error_txt, patch_diff, harness_info) -> dict[str, Any]`
  - `CyberGymState` TaskSpec flat fields from Task 1
- Produces:
  - populated state TaskSpec fields during `init_state()`
  - compact TaskSpec summary lines in observation / prompt helpers

- [ ] **Step 1: Add a failing integration test for init-state TaskSpec population**

```python
from qitos.benchmark.cybergym.agent.agent import CyberGymAgent


class _DummyLLM:
    def __call__(self, *_args, **_kwargs):
        raise AssertionError("LLM should not be called in init_state for deterministic task spec")


def test_init_state_populates_task_spec_fields(tmp_path):
    agent = CyberGymAgent(llm=_DummyLLM(), workspace_root=str(tmp_path), task_root=str(tmp_path))

    state = agent.init_state(
        "crafted .png file triggers heap-buffer-overflow in parse_chunk under ASAN",
        description="crafted .png file triggers heap-buffer-overflow in parse_chunk under ASAN",
        error_txt="AddressSanitizer: heap-buffer-overflow",
        patch_diff="",
        source_root=str(tmp_path),
        repo_dir=str(tmp_path),
        task_root=str(tmp_path),
    )

    assert state.vulnerability_class == "memory-safety"
    assert state.expected_signal == "ASAN"
    assert ".png" in state.input_vector_hints
    assert "parse_chunk" in state.symbols_mentioned
```

- [ ] **Step 2: Run the new init-state test to verify it fails**

Run: `pytest tests/test_cybergym_agent_poc_profile.py::test_init_state_populates_task_spec_fields -q`
Expected: FAIL because the new TaskSpec fields are still empty

- [ ] **Step 3: Wire `build_task_spec()` into `init_state()`**

```python
from .task_spec import build_task_spec
```

```python
# inside init_state(), after description / error_txt / patch_diff / harness_info are available
spec = build_task_spec(
    state.vulnerability_description,
    error_txt=str(state.metadata.get("error_txt") or ""),
    patch_diff=str(state.metadata.get("patch_diff") or ""),
    harness_info=state.harness_info or "",
)
state.vulnerability_class = str(spec.get("vulnerability_class") or "")
state.expected_signal = str(spec.get("expected_signal") or "")
state.input_vector_hints = list(spec.get("input_vector_hints") or [])
state.likely_entrypoints = list(spec.get("likely_entrypoints") or [])
state.likely_fuzz_targets = list(spec.get("likely_fuzz_targets") or [])
state.source_files_mentioned = list(spec.get("source_files_mentioned") or [])
state.symbols_mentioned = list(spec.get("symbols_mentioned") or [])
state.task_spec_confidence = float(spec.get("task_spec_confidence") or 0.0)
```

- [ ] **Step 4: Add a compact TaskSpec summary helper and keep it small**

```python
def _task_spec_summary_lines(self, state: CyberGymState) -> list[str]:
    lines: list[str] = []
    if state.expected_signal and state.expected_signal != "unknown":
        lines.append(f"- Expected Signal: `{state.expected_signal}`")
    if state.input_vector_hints:
        lines.append(f"- Input Hints: {', '.join(state.input_vector_hints[:4])}")
    if state.likely_entrypoints:
        lines.append(f"- Likely Entrypoints: {', '.join(state.likely_entrypoints[:4])}")
    if state.task_spec_confidence and state.task_spec_confidence < 0.5:
        lines.append(f"- Task-Spec Confidence: {state.task_spec_confidence:.2f}")
    return lines
```

Then add it into the current brief / observation build only as a short section if non-empty.

- [ ] **Step 5: Run the focused TaskSpec integration test**

Run: `pytest tests/test_cybergym_agent_poc_profile.py::test_init_state_populates_task_spec_fields -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add \
  qitos/benchmark/cybergym/agent/agent.py \
  tests/test_cybergym_agent_poc_profile.py
git commit -m "feat: wire cybergym task spec into agent bootstrap"
```

---

### Task 3: Enrich repo evidence bootstrap and ranked path selection without heavy indexing

**Files:**
- Modify: `qitos/benchmark/cybergym/agent/evidence_selector.py`
- Modify: `qitos/benchmark/cybergym/agent/agent.py`
- Test: `tests/test_cybergym_evidence_selector.py`

**Interfaces:**
- Consumes:
  - `CyberGymState.source_files_mentioned`
  - `CyberGymState.symbols_mentioned`
  - `CyberGymState.input_vector_hints`
- Produces:
  - enriched `evidence_index` keys:
    - `build_paths`
    - `fuzz_target_paths`
    - `sample_paths`
    - `language_hints`
    - `ranked_paths`
    - `repo_profile_summary`

- [ ] **Step 1: Write failing tests for enriched evidence bootstrap**

```python
from qitos.benchmark.cybergym.agent.evidence_selector import bootstrap_evidence_index


def test_bootstrap_evidence_index_finds_build_fuzz_and_sample_paths(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "fuzz").mkdir()
    (tmp_path / "samples").mkdir()
    (tmp_path / "CMakeLists.txt").write_text("project(x)", encoding="utf-8")
    (tmp_path / "fuzz" / "png_fuzzer.cc").write_text("LLVMFuzzerTestOneInput", encoding="utf-8")
    (tmp_path / "samples" / "seed.png").write_text("png", encoding="utf-8")

    index = bootstrap_evidence_index(
        str(tmp_path),
        "crafted .png file triggers parse_chunk bug",
        task_spec={
            "source_files_mentioned": [],
            "symbols_mentioned": ["parse_chunk"],
            "input_vector_hints": ["file", ".png"],
        },
    )

    assert any(path.endswith("CMakeLists.txt") for path in index["build_paths"])
    assert any(path.endswith("png_fuzzer.cc") for path in index["fuzz_target_paths"])
    assert any(path.endswith("seed.png") for path in index["sample_paths"])
    assert index["ranked_paths"]
    assert isinstance(index["repo_profile_summary"], str)


def test_bootstrap_evidence_index_ranks_relevant_paths_ahead_of_noise(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "vendor").mkdir()
    (tmp_path / "src" / "parse_chunk.c").write_text("int parse_chunk(void) { return 0; }", encoding="utf-8")
    (tmp_path / "vendor" / "ignore.c").write_text("int ignore(void) { return 0; }", encoding="utf-8")

    index = bootstrap_evidence_index(
        str(tmp_path),
        "bug in parse_chunk while reading .png",
        task_spec={
            "source_files_mentioned": ["src/parse_chunk.c"],
            "symbols_mentioned": ["parse_chunk"],
            "input_vector_hints": ["file", ".png"],
        },
    )

    assert index["ranked_paths"][0].endswith("src/parse_chunk.c")
```

- [ ] **Step 2: Run the new evidence selector tests to verify they fail**

Run: `pytest tests/test_cybergym_evidence_selector.py -q`
Expected: FAIL because `bootstrap_evidence_index()` does not yet accept `task_spec` or produce the enriched keys

- [ ] **Step 3: Extend `bootstrap_evidence_index()` with lightweight ranking and repo profiling**

```python
from pathlib import Path
from typing import Any, Dict, List

_BUILD_NAMES = {"cmakelists.txt", "makefile", "meson.build", "cargo.toml", "go.mod", "build.sh"}
_SAMPLE_SUFFIXES = {".png", ".jpg", ".gif", ".pdf", ".xml", ".json", ".yaml", ".yml", ".bin"}


def _score_path(relative: str, *, task_spec: Dict[str, Any]) -> float:
    lowered = relative.lower()
    score = 0.0
    for path in task_spec.get("source_files_mentioned", []) or []:
        if str(path).lower() == lowered:
            score += 5.0
    for symbol in task_spec.get("symbols_mentioned", []) or []:
        symbol_value = str(symbol).strip().lower()
        if symbol_value and symbol_value in lowered:
            score += 2.5
    for hint in task_spec.get("input_vector_hints", []) or []:
        hint_value = str(hint).strip().lower()
        if hint_value and hint_value in lowered:
            score += 1.5
    if "fuzz" in lowered or "fuzzer" in lowered:
        score += 2.0
    if any(noise in lowered for noise in ("vendor/", "third_party/", "generated/", "node_modules/", ".git/")):
        score -= 3.0
    return score


def bootstrap_evidence_index(repo_root: str, description: str, task_spec: Dict[str, Any] | None = None) -> Dict[str, Any]:
    root = Path(repo_root)
    task_spec = dict(task_spec or {})
    parser_candidates: List[str] = []
    header_candidates: List[str] = []
    build_paths: List[str] = []
    fuzz_target_paths: List[str] = []
    sample_paths: List[str] = []
    ranked_candidates: List[tuple[float, str]] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = str(path.relative_to(root))
        lowered = relative.lower()
        if any(hint in lowered for hint in PARSER_HINTS):
            parser_candidates.append(relative)
        if path.suffix.lower() in HEADER_SUFFIXES:
            header_candidates.append(relative)
        if path.name.lower() in _BUILD_NAMES:
            build_paths.append(relative)
        if "fuzz" in lowered or "fuzzer" in lowered:
            fuzz_target_paths.append(relative)
        if path.suffix.lower() in _SAMPLE_SUFFIXES and any(token in lowered for token in ("sample", "seed", "corpus", "test", "fuzz")):
            sample_paths.append(relative)
        ranked_candidates.append((_score_path(relative, task_spec=task_spec), relative))

    ranked_paths = [path for _score, path in sorted(ranked_candidates, key=lambda item: (-item[0], item[1])) if _score > 0][:20]
    language_hints = sorted({path.rsplit(".", 1)[-1] for _score, path in ranked_candidates if "." in path})[:8]
    repo_profile_summary = (
        f"parsers={len(parser_candidates)} fuzz_targets={len(fuzz_target_paths)} "
        f"samples={len(sample_paths)} builds={len(build_paths)}"
    )

    seed_paths = sorted(
        str(path.relative_to(root))
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".omf", ".cram", ".pdf", ".rar", ".bin"}
    )
    return {
        "description": description,
        "parser_paths": sorted(set(parser_candidates))[:8],
        "seed_paths": seed_paths[:8],
        "field_paths": sorted(set(header_candidates))[:8],
        "build_paths": sorted(set(build_paths))[:8],
        "fuzz_target_paths": sorted(set(fuzz_target_paths))[:8],
        "sample_paths": sorted(set(sample_paths))[:8],
        "language_hints": language_hints,
        "ranked_paths": ranked_paths,
        "repo_profile_summary": repo_profile_summary,
    }
```

- [ ] **Step 4: Pass TaskSpec hints into evidence bootstrap from `_ensure_family_bootstrap()`**

```python
evidence_index = bootstrap_evidence_index(
    repo_root,
    state.vulnerability_description,
    task_spec={
        "source_files_mentioned": list(state.source_files_mentioned or []),
        "symbols_mentioned": list(state.symbols_mentioned or []),
        "input_vector_hints": list(state.input_vector_hints or []),
    },
)
```

Also extend `_refresh_durable_project_memory()` to preserve only compact additions:

```python
refreshed = {
    "repo_summary": self._repo_prompt_summary(state.repo_index or ""),
    "repo_profile_summary": str(evidence.get("repo_profile_summary") or ""),
    "parser_paths": list(evidence.get("parser_paths") or [])[:8],
    "seed_paths": list(evidence.get("seed_paths") or [])[:8],
    "field_paths": list(evidence.get("field_paths") or [])[:8],
    "ranked_paths": list(evidence.get("ranked_paths") or [])[:8],
}
```

- [ ] **Step 5: Run the evidence selector tests to verify they pass**

Run: `pytest tests/test_cybergym_evidence_selector.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add \
  qitos/benchmark/cybergym/agent/evidence_selector.py \
  qitos/benchmark/cybergym/agent/agent.py \
  tests/test_cybergym_evidence_selector.py
git commit -m "feat: enrich cybergym repo evidence ranking"
```

---

### Task 4: Strengthen `CandidateRecord` provenance and make fingerprint semantics explicit

**Files:**
- Modify: `qitos/benchmark/cybergym/agent/family_runtime.py`
- Modify: `qitos/benchmark/cybergym/agent/subagent_runtime.py`
- Modify: `qitos/benchmark/cybergym/agent/agent.py`
- Test: `tests/test_cybergym_candidate_failure_records.py`

**Interfaces:**
- Consumes:
  - existing `CandidateRecord`
  - delegate candidate JSON payloads from `parse_candidate_json()`
- Produces:
  - extended `CandidateRecord` fields:
    - `producer_agent: str`
    - `created_at: str`
    - `artifact_ref: str`
    - `hypothesis_ref: str`
    - `fingerprint_mode: str`
    - `artifact_sha256: str`

- [ ] **Step 1: Write failing tests for candidate provenance and fingerprint-mode consistency**

```python
from qitos.benchmark.cybergym.agent.family_runtime import CandidateRecord
from qitos.benchmark.cybergym.agent.subagent_runtime import parse_candidate_json


def test_parse_candidate_json_allows_optional_provenance_fields():
    payload = parse_candidate_json(
        '{"candidates":[{"candidate_id":"c1","family_id":"f1","file_path":"pocs/a.bin","mutation_summary":"m","expected_signal":"ASAN","novelty_note":"n","base_seed":"seed.bin","generation_method":"delegate","ready_to_submit":true,"producer_agent":"explore_delegate","fingerprint_mode":"logical"}]}'
    )

    candidate = payload["candidates"][0]
    assert candidate["producer_agent"] == "explore_delegate"
    assert candidate["fingerprint_mode"] == "logical"


def test_candidate_record_supports_provenance_fields():
    candidate = CandidateRecord(
        candidate_id="c1",
        family_id="f1",
        file_path="pocs/a.bin",
        content_fingerprint="sha256:logical",
        mutation_summary="m",
        expected_signal="ASAN",
        novelty_note="n",
        base_seed="seed.bin",
        generation_method="delegate",
        ready_to_submit=True,
        producer_agent="explore_delegate",
        fingerprint_mode="logical",
        artifact_sha256="sha256:file",
    )

    assert candidate.producer_agent == "explore_delegate"
    assert candidate.fingerprint_mode == "logical"
    assert candidate.artifact_sha256 == "sha256:file"
```

- [ ] **Step 2: Run the candidate provenance tests to verify they fail**

Run: `pytest tests/test_cybergym_candidate_failure_records.py -q`
Expected: FAIL because `CandidateRecord` and `parse_candidate_json()` do not yet support the new fields

- [ ] **Step 3: Extend `CandidateRecord` with provenance fields**

```python
from dataclasses import dataclass

@dataclass
class CandidateRecord:
    candidate_id: str
    family_id: str
    file_path: str
    content_fingerprint: str
    mutation_summary: str
    expected_signal: str
    novelty_note: str
    base_seed: str
    generation_method: str
    ready_to_submit: bool
    priority: int = 0
    producer_agent: str = ""
    created_at: str = ""
    artifact_ref: str = ""
    hypothesis_ref: str = ""
    fingerprint_mode: str = ""
    artifact_sha256: str = ""
```

- [ ] **Step 4: Extend `parse_candidate_json()` to accept optional provenance keys without requiring them**

```python
_OPTIONAL_CANDIDATE_FIELDS = {
    "producer_agent",
    "created_at",
    "artifact_ref",
    "hypothesis_ref",
    "fingerprint_mode",
    "artifact_sha256",
}
```

```python
for name in _OPTIONAL_CANDIDATE_FIELDS:
    if name in candidate and not isinstance(candidate[name], str):
        raise ValueError(f"Candidate field {name} must be a string")
```

- [ ] **Step 5: Fill provenance defaults in candidate creation paths**

In delegate candidate creation:

```python
candidate = CandidateRecord(
    candidate_id=normalized_candidate["candidate_id"],
    family_id=normalized_candidate["family_id"],
    file_path=normalized_candidate["file_path"],
    content_fingerprint=self._candidate_fingerprint(normalized_candidate),
    mutation_summary=normalized_candidate["mutation_summary"],
    expected_signal=normalized_candidate["expected_signal"],
    novelty_note=normalized_candidate["novelty_note"],
    base_seed=normalized_candidate["base_seed"],
    generation_method=normalized_candidate["generation_method"],
    ready_to_submit=normalized_candidate["ready_to_submit"],
    priority=max(candidate_budget - accepted, 0),
    producer_agent=str(normalized_candidate.get("producer_agent") or "candidate_delegate"),
    created_at=str(normalized_candidate.get("created_at") or ""),
    artifact_ref=str(normalized_candidate.get("artifact_ref") or ""),
    hypothesis_ref=str(normalized_candidate.get("hypothesis_ref") or family.family_id),
    fingerprint_mode=str(normalized_candidate.get("fingerprint_mode") or "logical"),
    artifact_sha256=str(normalized_candidate.get("artifact_sha256") or ""),
)
```

In direct candidate creation:

```python
return CandidateRecord(
    candidate_id=candidate_id,
    family_id=family_id,
    file_path=normalized_path,
    content_fingerprint=fingerprint,
    mutation_summary="direct_candidate",
    expected_signal="submit_for_feedback",
    novelty_note="direct_tool_output",
    base_seed="",
    generation_method="direct_tool_output",
    ready_to_submit=ready_to_submit,
    priority=0,
    producer_agent="main_agent",
    fingerprint_mode="artifact",
    artifact_sha256=fingerprint,
)
```

- [ ] **Step 6: Run the candidate provenance tests to verify they pass**

Run: `pytest tests/test_cybergym_candidate_failure_records.py -q`
Expected: PASS for the provenance assertions

- [ ] **Step 7: Commit**

```bash
git add \
  qitos/benchmark/cybergym/agent/family_runtime.py \
  qitos/benchmark/cybergym/agent/subagent_runtime.py \
  qitos/benchmark/cybergym/agent/agent.py \
  tests/test_cybergym_candidate_failure_records.py
git commit -m "feat: strengthen cybergym candidate provenance"
```

---

### Task 5: Add lightweight failure taxonomy and derived failure records without changing submit semantics

**Files:**
- Modify: `qitos/benchmark/cybergym/agent/family_runtime.py`
- Modify: `qitos/benchmark/cybergym/agent/state.py`
- Modify: `qitos/benchmark/cybergym/agent/agent.py`
- Test: `tests/test_cybergym_candidate_failure_records.py`
- Regression: `tests/test_engine_core_flow.py`

**Interfaces:**
- Consumes:
  - raw submit `output: dict[str, Any]`
  - `FeedbackRecord`
- Produces:
  - `FailureType` enum values:
    - `SUBMISSION_ERROR`
    - `NO_TRIGGER`
    - `VUL_ONLY_TRIGGERED`
    - `REJECTED_AFTER_TRIGGER`
    - `TIMEOUT`
    - `OOM`
    - `BOTH_SIDES_CRASH`
    - `UNKNOWN`
  - `FailureRecord`
  - `CyberGymState.failure_history: List[FailureRecord]`

- [ ] **Step 1: Add failing tests for failure taxonomy derivation**

```python
from qitos.benchmark.cybergym.agent.family_runtime import FailureType
from qitos.benchmark.cybergym.agent.agent import CyberGymAgent


def test_classify_failure_marks_submission_error():
    failure_type = CyberGymAgent._classify_failure_type({"status": "error", "error": "timeout contacting server"})
    assert failure_type == FailureType.SUBMISSION_ERROR


def test_classify_failure_marks_no_trigger():
    failure_type = CyberGymAgent._classify_failure_type(
        {"status": "success", "vul_exit_code": 0, "verification_status": "no_trigger"}
    )
    assert failure_type == FailureType.NO_TRIGGER


def test_classify_failure_marks_vul_only_triggered():
    failure_type = CyberGymAgent._classify_failure_type(
        {"status": "success", "vul_exit_code": 1, "verification_scope": "vul_only", "verification_status": "vul_only_triggered"}
    )
    assert failure_type == FailureType.VUL_ONLY_TRIGGERED


def test_classify_failure_marks_rejected_after_trigger():
    failure_type = CyberGymAgent._classify_failure_type(
        {"status": "success", "vul_exit_code": 1, "verification_status": "rejected"}
    )
    assert failure_type == FailureType.REJECTED_AFTER_TRIGGER
```

- [ ] **Step 2: Run the failure taxonomy tests to verify they fail**

Run: `pytest tests/test_cybergym_candidate_failure_records.py -q`
Expected: FAIL because `FailureType` and `_classify_failure_type()` do not exist

- [ ] **Step 3: Add `FailureType` and `FailureRecord` to `family_runtime.py`**

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import List


class FailureType(str, Enum):
    SUBMISSION_ERROR = "SUBMISSION_ERROR"
    NO_TRIGGER = "NO_TRIGGER"
    VUL_ONLY_TRIGGERED = "VUL_ONLY_TRIGGERED"
    REJECTED_AFTER_TRIGGER = "REJECTED_AFTER_TRIGGER"
    TIMEOUT = "TIMEOUT"
    OOM = "OOM"
    BOTH_SIDES_CRASH = "BOTH_SIDES_CRASH"
    UNKNOWN = "UNKNOWN"


@dataclass
class FailureRecord:
    candidate_id: str
    family_id: str
    failure_type: FailureType
    summary: str
    evidence_excerpt: str = ""
    related_poc_id: str = ""
    internal_only: bool = False
```

- [ ] **Step 4: Extend `CyberGymState` with `failure_history`**

```python
failure_history: List[FailureRecord] = field(default_factory=list)
```

And normalize it in `__post_init__()` the same way as the other record lists.

- [ ] **Step 5: Add failure classification + record derivation in `agent.py`**

```python
@staticmethod
def _classify_failure_type(result: dict[str, Any]) -> FailureType:
    if not isinstance(result, dict):
        return FailureType.UNKNOWN
    if result.get("status") == "error":
        text = str(result.get("error") or result.get("raw_output") or "").lower()
        if "timeout" in text:
            return FailureType.TIMEOUT
        if "out of memory" in text or "oom" in text:
            return FailureType.OOM
        return FailureType.SUBMISSION_ERROR
    verification_status = str(result.get("verification_status") or "")
    verification_scope = str(result.get("verification_scope") or "")
    vul = result.get("vul_exit_code")
    fix = result.get("fix_exit_code")
    if verification_status == "rejected":
        return FailureType.REJECTED_AFTER_TRIGGER
    if vul not in (None, 0) and verification_scope == "vul_only":
        return FailureType.VUL_ONLY_TRIGGERED
    if vul not in (None, 0) and fix not in (None, 0):
        return FailureType.BOTH_SIDES_CRASH
    if vul == 0:
        return FailureType.NO_TRIGGER
    return FailureType.UNKNOWN
```

```python
@staticmethod
def _derive_failure_record(output: dict[str, Any], submit_context: dict[str, Any]) -> FailureRecord | None:
    failure_type = CyberGymAgent._classify_failure_type(output)
    if failure_type == FailureType.UNKNOWN and output.get("accepted") is True:
        return None
    evidence_excerpt = str(
        output.get("error")
        or output.get("raw_output")
        or output.get("vul_stderr")
        or ""
    )[:400]
    return FailureRecord(
        candidate_id=str(submit_context.get("candidate_id") or ""),
        family_id=str(submit_context.get("family_id") or ""),
        failure_type=failure_type,
        summary=failure_type.value,
        evidence_excerpt=evidence_excerpt,
        related_poc_id=str(output.get("poc_id") or ""),
        internal_only=failure_type == FailureType.BOTH_SIDES_CRASH,
    )
```

Append the derived failure record only for non-accepted outcomes.

- [ ] **Step 6: Keep model-facing summaries coarse and safe**

Add a helper such as:

```python
@staticmethod
def _failure_summary_lines(state: CyberGymState) -> list[str]:
    visible: list[str] = []
    for record in list(state.failure_history or [])[-2:]:
        if getattr(record, "internal_only", False):
            continue
        visible.append(f"- Recent Failure: {record.summary}")
    return visible
```

Use that helper only as a compact observation section; do not inject raw `FailureRecord` objects.

- [ ] **Step 7: Run focused taxonomy tests and the submit sanitization regression**

Run: `pytest tests/test_cybergym_candidate_failure_records.py tests/test_engine_core_flow.py::test_engine_sanitizes_submit_poc_native_tool_history_without_mutating_result -q`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add \
  qitos/benchmark/cybergym/agent/family_runtime.py \
  qitos/benchmark/cybergym/agent/state.py \
  qitos/benchmark/cybergym/agent/agent.py \
  tests/test_cybergym_candidate_failure_records.py \
  tests/test_engine_core_flow.py
git commit -m "feat: add lightweight cybergym failure taxonomy"
```

---

### Task 6: Run regression checks and update user-facing docs for the bounded upgrade

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `README.md`
- Modify: `qitos/benchmark/cybergym/agent/README.md`
- Modify: `qitos/benchmark/cybergym/agent/ARCH.md`

**Interfaces:**
- Consumes: completed implementation from Tasks 1-5
- Produces: updated changelog/docs reflecting the new lightweight task-spec/evidence/failure/candidate behavior

- [ ] **Step 1: Add a failing docs governance check only if one already exists for touched docs**

```bash
pytest tests/test_examples_layout.py -q
```

Expected: PASS or not-applicable baseline check only; this step is a safety check, not new failing logic.

- [ ] **Step 2: Update `CHANGELOG.md` under Unreleased**

```markdown
### Changed
- Strengthened the CyberGym PoC agent's task bootstrap with lightweight structured task-spec extraction and more relevant repo evidence ranking.
- Clarified candidate provenance and lightweight failure taxonomy handling in the CyberGym agent without changing its single-agent runtime architecture.
```

- [ ] **Step 3: Update `qitos/benchmark/cybergym/agent/README.md` to reflect the new lightweight summaries**

```markdown
- task bootstrap now derives a lightweight task-spec summary (expected signal, input hints, likely entrypoints) before candidate construction
- repo evidence bootstrap now ranks likely parser/harness/sample paths using task-spec hints
- candidate records now carry lightweight provenance metadata for safer dedupe and feedback correlation
- submit feedback now also derives a lightweight internal failure taxonomy while keeping model-visible summaries coarse
```

- [ ] **Step 4: Update `qitos/benchmark/cybergym/agent/ARCH.md` with the new bounded information flows**

```markdown
Implemented now:
- lightweight structured task-spec extraction inside `CyberGymAgent.init_state()`
- ranked repo evidence bootstrap using task-semantic hints
- clarified candidate provenance fields and explicit fingerprint-mode semantics
- lightweight internal failure taxonomy layered on top of raw submit feedback
```

- [ ] **Step 5: Update `README.md` news / updates section if the repo already has one**

```markdown
- Improved the CyberGym PoC agent's early task understanding, repo evidence targeting, and structured failure handling while keeping the runtime single-agent and lightweight.
```

- [ ] **Step 6: Run focused regressions and docs-adjacent checks**

Run: `pytest tests/test_cybergym_task_spec.py tests/test_cybergym_evidence_selector.py tests/test_cybergym_candidate_failure_records.py tests/test_cybergym_agent_poc_profile.py tests/test_engine_core_flow.py::test_engine_sanitizes_submit_poc_native_tool_history_without_mutating_result -q`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add \
  CHANGELOG.md \
  README.md \
  qitos/benchmark/cybergym/agent/README.md \
  qitos/benchmark/cybergym/agent/ARCH.md \
  tests/test_cybergym_task_spec.py \
  tests/test_cybergym_evidence_selector.py \
  tests/test_cybergym_candidate_failure_records.py \
  tests/test_cybergym_agent_poc_profile.py \
  qitos/benchmark/cybergym/agent/task_spec.py \
  qitos/benchmark/cybergym/agent/state.py \
  qitos/benchmark/cybergym/agent/family_runtime.py \
  qitos/benchmark/cybergym/agent/evidence_selector.py \
  qitos/benchmark/cybergym/agent/subagent_runtime.py \
  qitos/benchmark/cybergym/agent/agent.py
git commit -m "feat: upgrade cybergym bootstrap and failure guidance"
```

---

## Spec Coverage Check

- P0.2 structured task-spec extraction: covered by Tasks 1-2
- P1.1 stronger repo-map / evidence ranking: covered by Task 3
- P0.1 candidate provenance/schema strengthening: covered by Task 4
- P0.4 failure taxonomy / failure records: covered by Task 5
- lightweight prompt visibility / no prompt bloat: covered by Tasks 2, 3, and 5
- no new heavy dependencies / no runtime architecture expansion: enforced in Global Constraints and throughout all tasks
- changelog / docs / README sync: covered by Task 6

## Placeholder Scan

No `TODO`, `TBD`, “implement later”, or undefined references remain. Each code-changing step includes actual code and each verification step includes an exact command.

## Type Consistency Check

- `build_task_spec(...) -> dict[str, Any]` is used consistently.
- `CandidateRecord` provenance fields are added in the dataclass before being used in `agent.py`.
- `FailureType` / `FailureRecord` are defined in `family_runtime.py` before being referenced from `state.py` and `agent.py`.
- `failure_history: List[FailureRecord]` matches the dataclass normalization pattern already used in `CyberGymState`.

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-06-20-cybergym-p0-p1-lightweight-implementation.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**