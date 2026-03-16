import { useState, useRef } from 'react';
import { ingestPdf } from '../../api/client';
import Button from '../shared/Button';

export default function PdfUpload({ onSuccess, onToast }) {
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef();

  const handleFile = (f) => {
    if (f && f.type === 'application/pdf' && f.size <= 50 * 1024 * 1024) {
      setFile(f);
    } else if (f) {
      onToast('Please select a PDF file under 50MB', 'error');
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0]);
  };

  const handleSubmit = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const data = await ingestPdf(file);
      onToast(`Added ${data.chunks_added} chunks from ${data.document_name}`, 'success');
      setFile(null);
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
        PDF Upload
      </label>
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`border border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors duration-150
          ${dragging
            ? 'border-accent bg-accent/5'
            : 'border-border hover:border-border-hover hover:bg-surface-hover'
          }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={(e) => handleFile(e.target.files[0])}
        />
        {file ? (
          <div className="text-sm text-text truncate">{file.name}</div>
        ) : (
          <div className="text-xs text-text-muted">
            <span className="text-accent font-medium">Click to upload</span> or drag & drop
            <br />PDF up to 50MB
          </div>
        )}
      </div>
      {file && (
        <Button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full text-xs"
        >
          {loading ? 'Processing...' : 'Ingest PDF'}
        </Button>
      )}
    </div>
  );
}
