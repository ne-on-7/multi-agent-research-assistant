from pydantic import BaseModel


class URLRequest(BaseModel):
    url: str


class GitHubRequest(BaseModel):
    repo_url: str
    branch: str = "main"


class QueryRequest(BaseModel):
    query: str


class IngestResponse(BaseModel):
    status: str
    chunks_added: int
    document_name: str


class DocumentInfo(BaseModel):
    name: str
    type: str
    chunks: int
