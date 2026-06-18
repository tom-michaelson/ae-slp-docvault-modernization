from pydantic import BaseModel


class FigmaPage(BaseModel):
    name: str
    file_key: str
    node_id: str


class FigmaToStoriesWorkflowInput(BaseModel):
    pages: list[FigmaPage]


class ImageToStoryWorkflowInput(BaseModel):
    image_path: str | None = None
    jira_project_id: str | None = None
