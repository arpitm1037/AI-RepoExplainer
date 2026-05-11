from pydantic import BaseModel


class CodeChunk(BaseModel):
    chunk_id: str

    content: str

    file_path: str

    start_line: int
    end_line: int

    chunk_type: str | None = None

    symbol_name: str | None = None

    chunk_index: int = 0