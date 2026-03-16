import { useState } from 'react';

export default function QueryInput({ onSubmit, disabled }) {
  const [query, setQuery] = useState('');

  const handleSubmit = () => {
    if (query.trim() && !disabled) {
      onSubmit(query.trim());
    }
  };

  return (
    <div className="max-w-3xl mx-auto w-full">
      <div className="flex items-center bg-surface border border-border rounded-lg overflow-hidden focus-within:border-accent/50 transition-colors">
        <svg
          className="ml-4 shrink-0 text-text-muted"
          width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
        >
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>

        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          placeholder="Ask a research question..."
          disabled={disabled}
          className="flex-1 bg-transparent px-4 py-3.5 text-text placeholder-text-muted text-sm
            focus:outline-none disabled:opacity-50"
        />

        <button
          onClick={handleSubmit}
          disabled={!query.trim() || disabled}
          className="mr-2 px-5 py-2 rounded-md bg-accent text-white text-sm font-medium
            hover:bg-accent-hover
            disabled:opacity-30 disabled:hover:bg-accent
            transition-colors duration-150 cursor-pointer disabled:cursor-not-allowed shrink-0"
        >
          {disabled ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Researching
            </span>
          ) : (
            'Research'
          )}
        </button>
      </div>
    </div>
  );
}
