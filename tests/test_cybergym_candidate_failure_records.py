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


from qitos.benchmark.cybergym.agent.agent import CyberGymAgent
from qitos.benchmark.cybergym.agent.family_runtime import FailureType


def test_classify_failure_marks_timeout():
    failure_type = CyberGymAgent._classify_failure_type({"status": "error", "error": "timeout contacting server"})
    assert failure_type == FailureType.TIMEOUT


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
