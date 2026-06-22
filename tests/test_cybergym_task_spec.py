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
