from pydantic import BaseModel, Field, HttpUrl


class URLRequest(BaseModel):
    url: HttpUrl


class GitHubRequest(BaseModel):
    repo_url: str
    branch: str = ""


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)


class IngestResponse(BaseModel):
    status: str
    chunks_added: int
    document_name: str


class DocumentInfo(BaseModel):
    name: str
    type: str
    chunks: int
