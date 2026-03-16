const BASE = '/api';

export async function checkHealth() {
  const resp = await fetch(`${BASE}/health`);
  return resp.ok;
}

export async function ingestPdf(file) {
  const form = new FormData();
  form.append('file', file);
  const resp = await fetch(`${BASE}/ingest/pdf`, { method: 'POST', body: form });
  if (!resp.ok) throw new Error(await resp.text());
  return resp.json();
}

export async function ingestUrl(url) {
  const resp = await fetch(`${BASE}/ingest/url`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  });
  if (!resp.ok) throw new Error(await resp.text());
  return resp.json();
}

export async function ingestGithub(repoUrl, branch) {
  const resp = await fetch(`${BASE}/ingest/github`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_url: repoUrl, branch: branch || undefined }),
  });
  if (!resp.ok) throw new Error(await resp.text());
  return resp.json();
}

export async function getDocuments() {
  const resp = await fetch(`${BASE}/documents`);
  if (!resp.ok) throw new Error(await resp.text());
  return resp.json();
}

export async function clearDocuments() {
  const resp = await fetch(`${BASE}/documents`, { method: 'DELETE' });
  if (!resp.ok) throw new Error(await resp.text());
  return true;
}
