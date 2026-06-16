from pydantic import BaseModel


class CodeSummaryResult(BaseModel):
    code_file_path: str
    code_file_content: str
    code_summary: str
