import { useState } from 'react';
import { ingestUrl } from '../../api/client';
import Button from '../shared/Button';

export default function UrlIngestion({ onSuccess, onToast }) {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!url.trim()) return;
    setLoading(true);
    try {
      const data = await ingestUrl(url.trim());
      onToast(`Added ${data.chunks_added} chunks from URL`, 'success');
      setUrl('');
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
        Web URL
      </label>
      <input
        type="url"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        placeholder="https://example.com/article"
        className="w-full bg-surface border border-border rounded-lg px-3.5 py-2.5 text-sm text-text placeholder-text-muted
          focus:outline-none focus:border-accent/50 transition-colors"
        onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
      />
      {url.trim() && (
        <Button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full text-xs"
        >
          {loading ? 'Fetching...' : 'Ingest URL'}
        </Button>
      )}
    </div>
  );
}
