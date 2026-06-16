from pydantic import BaseModel


class CalculatorInput(BaseModel):
    a: float
    b: float


class NPXStdioFilesystemInput(BaseModel):
    directory_path: str = "."


class UVXStdioTimeInput(BaseModel):
    source_timezone: str = "America/New_York"
    target_timezone: str = "Asia/Tokyo"
    time: str = "16:30"
