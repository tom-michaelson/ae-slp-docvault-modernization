from pydantic import BaseModel


class WorkflowTestCase(BaseModel):
    workflow_name: str
    input_data: BaseModel
    custom_text_assertions: list[str] | None
