import re

import httpx
import pdfplumber
from bs4 import BeautifulSoup

from config.settings import settings
from services.vector_store import DocumentChunk

MAX_CHUNKS = 10_000


class DocumentProcessor:
    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ):
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if self.chunk_overlap < 0 or self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be >= 0 and < chunk_size")

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
            html = resp.text

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return self._chunk_text(text, {"source": url, "type": "url"})

    async def process_github_repo(self, repo_url: str, branch: str = "") -> list[DocumentChunk]:
        # Extract owner/repo from URL path
        from urllib.parse import urlparse

        parsed = urlparse(repo_url if "://" in repo_url else f"https://{repo_url}")
        path_parts = [p for p in parsed.path.strip("/").removesuffix(".git").split("/") if p]
        if len(path_parts) < 2:
            raise ValueError("GitHub URL must include owner and repo, e.g. https://github.com/owner/repo")
        owner, repo = path_parts[0], path_parts[1]
        api_base = f"https://api.github.com/repos/{owner}/{repo}"
        headers = {"User-Agent": "multi-agent-research-assistant"}

        async with httpx.AsyncClient(timeout=30, headers=headers) as client:
            # Auto-detect default branch if not specified
            if not branch:
                repo_resp = await client.get(api_base)
                if repo_resp.status_code == 404:
                    raise ValueError(f"Repository not found: {owner}/{repo}")
                repo_resp.raise_for_status()
                branch = repo_resp.json().get("default_branch", "main")

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
        step = self.chunk_size - self.chunk_overlap
        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]
            if chunk_text.strip():
                chunks.append(DocumentChunk(text=chunk_text, metadata={**metadata, "chunk_index": idx}))
                idx += 1
                if idx >= MAX_CHUNKS:
                    break
            start += step
        return chunks
