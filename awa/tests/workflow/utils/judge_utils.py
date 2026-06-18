from pathlib import Path

from awa.baml_client.sync_client import b
from awa.baml_client.types import DefineCriteriaResult, JudgeOutputResult
from tests.workflow.utils.baml_utils import get_baml_prompt


def define_criteria(prompt_name: str) -> DefineCriteriaResult:
    prompt = get_baml_prompt(prompt_name)
    return b.Define_Criteria(prompt=prompt)


def judge_output(generated: str, prompt_name: str) -> JudgeOutputResult:
    criteria = define_criteria(prompt_name)
    return b.Judge_Output(generated=generated, criteria=criteria.criteria)


def read_generated_output(output_path: str) -> str:
    with Path(output_path).open(encoding="utf-8") as f:
        return f.read()
