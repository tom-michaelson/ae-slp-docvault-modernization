from pydantic import BaseModel


class GeneratedStory(BaseModel):
    title: str
    description: str
