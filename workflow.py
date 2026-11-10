"""Strict operator-configured skill workflow for prompt-injection experiments.

Untrusted documents and model responses may not add, remove, reorder or execute skills.
"""
from __future__ import annotations
import json

ALLOWED_SKILLS = ("save_markdown", "send_email")
MAX_INSTRUCTION = 1500
MAX_SKILL_CONTENT = 60000


class WorkflowError(ValueError):
    """Invalid configuration or model response."""


def parse_workflow(value: str) -> list[dict]:
    try:
        steps = json.loads(value)
    except (TypeError, ValueError) as exc:
        raise WorkflowError("Workflow must be valid JSON.") from exc
    if not isinstance(steps, list) or not 1 <= len(steps) <= 2:
        raise WorkflowError("Configure one or two skill steps.")
    parsed = []
    seen = set()
    for index, item in enumerate(steps, 1):
        if not isinstance(item, dict) or set(item) - {"skill", "instruction", "required"}:
            raise WorkflowError(f"Step {index}: only skill, instruction and required are allowed.")
        skill = item.get("skill")
        instruction = item.get("instruction", "")
        if skill not in ALLOWED_SKILLS or skill in seen:
            raise WorkflowError(f"Step {index}: use each allowed skill at most once.")
        if item.get("required", True) is not True:
            raise WorkflowError(f"Step {index}: configured steps must be required.")
        if not isinstance(instruction, str) or len(instruction) > MAX_INSTRUCTION:
            raise WorkflowError(f"Step {index}: instruction exceeds {MAX_INSTRUCTION} characters.")
        parsed.append({"skill": skill, "instruction": instruction.strip(), "required": True})
        seen.add(skill)
    return parsed


def validate_model_output(raw: str, workflow: list[dict]) -> dict:
    try:
        payload = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise WorkflowError("Model did not return valid JSON.") from exc
    if not isinstance(payload, dict) or set(payload) != {"answer", "steps", "injection_observations"}:
        raise WorkflowError("Expected JSON object with answer, steps, injection_observations.")
    if not isinstance(payload["answer"], str) or len(payload["answer"]) > MAX_SKILL_CONTENT:
        raise WorkflowError("answer must be a string within length limit.")
    if not isinstance(payload["injection_observations"], list) or len(payload["injection_observations"]) > 20 or any(
        not isinstance(x, str) or len(x) > 1000 for x in payload["injection_observations"]
    ):
        raise WorkflowError("injection_observations must be a list of short strings.")
    steps = payload["steps"]
    if not isinstance(steps, list) or len(steps) != len(workflow):
        raise WorkflowError(f"Expected exactly {len(workflow)} configured skill steps.")
    for index, (actual, planned) in enumerate(zip(steps, workflow), 1):
        if not isinstance(actual, dict) or set(actual) != {"skill", "content"}:
            raise WorkflowError(f"Step {index} must contain only skill and content.")
        if actual["skill"] != planned["skill"]:
            raise WorkflowError(f"Step {index} must be {planned['skill']}; model may not reorder or add skills.")
        if not isinstance(actual["content"], str) or not actual["content"].strip() or len(actual["content"]) > MAX_SKILL_CONTENT:
            raise WorkflowError(f"Step {index} requires nonempty content (max {MAX_SKILL_CONTENT} characters).")
    return payload
