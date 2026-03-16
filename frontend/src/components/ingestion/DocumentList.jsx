import Button from '../shared/Button';

const typeIcons = {
  pdf: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  ),
  url: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
    </svg>
  ),
  github: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" />
    </svg>
  ),
};

export default function DocumentList({ documents, onClear }) {
  return (
    <div className="space-y-3">
      <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wide">
        Ingested Documents
      </h3>

      {documents.length === 0 ? (
        <p className="text-xs text-text-muted italic">No documents ingested yet.</p>
      ) : (
        <div className="space-y-1.5 max-h-48 overflow-y-auto">
          {documents.map((doc, i) => (
            <div
              key={i}
              className="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-surface/50 text-xs group"
            >
              <span className="text-text-muted shrink-0">
                {typeIcons[doc.type] || typeIcons.url}
              </span>
              <span className="text-text-secondary truncate flex-1">
                {doc.name}
              </span>
              <span className="text-text-muted shrink-0">
                {doc.chunks}
              </span>
            </div>
          ))}
        </div>
      )}

      {documents.length > 0 && (
        <Button variant="danger" onClick={onClear} className="w-full text-xs">
          Clear All Documents
        </Button>
      )}
    </div>
  );
}
