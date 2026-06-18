from pydantic import BaseModel


class ReadDirectoryResult(BaseModel):
    file: str
    content: str
