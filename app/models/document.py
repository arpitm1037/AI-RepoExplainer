from pydantic import BaseModel


class CodeDocument(BaseModel):
    content: str

    file_path: str

    extension: str

    size: int

    dependencies: list[str] = []