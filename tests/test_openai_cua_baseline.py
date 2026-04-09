from __future__ import annotations

from qitos import Action, Decision, RunSpec

from examples.real.openai_cua_agent import DesktopGroundingCritic, OpenAICUAState, configure_runtime_for_task


def test_desktop_grounding_critic_retries_ungrounded_click() -> None:
    critic = DesktopGroundingCritic()
    state = OpenAICUAState(task="desktop", last_grounding_quality="weak")
    decision = Decision.act(actions=[Action(name="click", args={})], rationale="click it")
    out = critic.evaluate(state, decision, [])
    assert out["action"] == "retry"
    assert out["details"]["failure_tag"] == "grounding_failure"


def test_configure_runtime_for_task_keeps_family_first_protocol() -> None:
    spec = RunSpec.infer(
        model_name="qwen-plus",
        prompt_protocol="desktop_actions_json_v1",
        parser_name="JsonDecisionParser",
    )
    runtime = configure_runtime_for_task(run_spec=spec, smoke=True)
    assert runtime["model_family"] == "qwen"
    assert runtime["protocol"]
    assert runtime["harness"].family_preset.id == "qwen"
