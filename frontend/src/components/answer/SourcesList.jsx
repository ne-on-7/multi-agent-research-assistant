import Card from '../shared/GlassCard';

export default function SourcesList({ sources }) {
  if (!sources || sources.length === 0) return null;

  return (
    <Card className="animate-fade-in">
      <h2 className="text-base font-semibold text-text mb-4 flex items-center gap-2">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
        </svg>
        Sources
        <span className="text-xs font-normal text-text-muted ml-1">({sources.length})</span>
      </h2>

      <div className="space-y-2">
        {sources.map((source, i) => {
          const title = source.title || 'Unknown Source';
          const url = source.url;
          const page = source.page;
          const snippet = source.snippet;

          return (
            <div
              key={i}
              className="flex gap-3 p-3 rounded-lg bg-surface-hover/50 hover:bg-surface-hover transition-colors"
            >
              <span className="text-xs font-semibold text-accent shrink-0 mt-0.5 w-6 h-6 flex items-center justify-center rounded bg-accent/10">
                {i + 1}
              </span>
              <div className="min-w-0 flex-1">
                {url ? (
                  <a
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm font-medium text-accent hover:text-accent-hover hover:underline block truncate"
                  >
                    {title}
                  </a>
                ) : (
                  <span className="text-sm font-medium text-text block truncate">
                    {title}
                    {page != null && (
                      <span className="text-text-muted font-normal"> — Page {page}</span>
                    )}
                  </span>
                )}
                {snippet && (
                  <p className="text-xs text-text-muted mt-1 line-clamp-2">
                    {snippet.length > 150 ? snippet.slice(0, 150) + '...' : snippet}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
