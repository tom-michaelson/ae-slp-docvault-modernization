from pydantic import BaseModel


class BamlImageInputParams(BaseModel):
    name: str
    base64_str: str
    mime_type: str
