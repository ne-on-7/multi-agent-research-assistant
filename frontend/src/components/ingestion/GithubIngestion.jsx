import { useState } from 'react';
import { ingestGithub } from '../../api/client';
import Button from '../shared/Button';

export default function GithubIngestion({ onSuccess, onToast }) {
  const [repoUrl, setRepoUrl] = useState('');
  const [branch, setBranch] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!repoUrl.trim()) return;
    setLoading(true);
    try {
      const data = await ingestGithub(repoUrl.trim(), branch.trim());
      onToast(`Added ${data.chunks_added} chunks from repo`, 'success');
      setRepoUrl('');
      setBranch('');
      onSuccess();
    } catch (err) {
      onToast(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-2.5">
      <label className="text-xs font-semibold text-text-secondary uppercase tracking-wide">
        GitHub Repository
      </label>
      <input
        type="url"
        value={repoUrl}
        onChange={(e) => setRepoUrl(e.target.value)}
        placeholder="https://github.com/owner/repo"
        className="w-full bg-surface border border-border rounded-lg px-3.5 py-2.5 text-sm text-text placeholder-text-muted
          focus:outline-none focus:border-accent/50 transition-colors"
      />
      <input
        type="text"
        value={branch}
        onChange={(e) => setBranch(e.target.value)}
        placeholder="Branch (auto-detect)"
        className="w-full bg-surface border border-border rounded-lg px-3.5 py-2.5 text-sm text-text placeholder-text-muted
          focus:outline-none focus:border-accent/50 transition-colors"
      />
      {repoUrl.trim() && (
        <Button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full text-xs"
        >
          {loading ? 'Processing...' : 'Ingest Repo'}
        </Button>
      )}
    </div>
  );
}
