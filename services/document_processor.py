import re

import httpx
import pdfplumber
from bs4 import BeautifulSoup

from config.settings import settings
from services.vector_store import DocumentChunk


class DocumentProcessor:
    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ):
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

    async def process_pdf(self, file_path: str) -> list[DocumentChunk]:
        chunks = []
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                if text.strip():
                    chunks.extend(
                        self._chunk_text(text, {"source": file_path, "page": page_num, "type": "pdf"})
                    )
        return chunks

    async def process_url(self, url: str) -> list[DocumentChunk]:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            resp = await client.get(url)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return self._chunk_text(text, {"source": url, "type": "url"})

    async def process_github_repo(self, repo_url: str, branch: str = "main") -> list[DocumentChunk]:
        # Extract owner/repo from URL
        parts = repo_url.rstrip("/").split("/")
        owner, repo = parts[-2], parts[-1]
        api_base = f"https://api.github.com/repos/{owner}/{repo}"

        async with httpx.AsyncClient(timeout=30) as client:
            # Get repo tree
            tree_resp = await client.get(f"{api_base}/git/trees/{branch}?recursive=1")
            tree_resp.raise_for_status()
            tree = tree_resp.json()

            chunks = []
            allowed_extensions = {".py", ".md", ".txt", ".rst", ".js", ".ts", ".tsx", ".jsx"}

            for item in tree.get("tree", []):
                if item["type"] != "blob":
                    continue
                path = item["path"]
                if not any(path.endswith(ext) for ext in allowed_extensions):
                    continue
                # Skip large files and vendor dirs
                if any(skip in path for skip in ["node_modules/", "vendor/", ".min."]):
                    continue

                file_resp = await client.get(
                    f"{api_base}/contents/{path}?ref={branch}",
                    headers={"Accept": "application/vnd.github.raw+json"},
                )
                if file_resp.status_code == 200:
                    text = file_resp.text
                    if text.strip():
                        chunks.extend(
                            self._chunk_text(text, {"source": f"{repo_url}/{path}", "file": path, "type": "github"})
                        )

        return chunks

    def _chunk_text(self, text: str, metadata: dict) -> list[DocumentChunk]:
        chunks = []
        start = 0
        idx = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]
            if chunk_text.strip():
                chunks.append(DocumentChunk(text=chunk_text, metadata={**metadata, "chunk_index": idx}))
                idx += 1
            start += self.chunk_size - self.chunk_overlap
        return chunks
