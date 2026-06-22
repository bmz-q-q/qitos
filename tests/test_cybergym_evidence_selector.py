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
