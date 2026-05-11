from pydantic import BaseModel


class IngestRequest(BaseModel):
    repo_url: str


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class AskRequest(BaseModel):
    query: str
    top_k: int = 5