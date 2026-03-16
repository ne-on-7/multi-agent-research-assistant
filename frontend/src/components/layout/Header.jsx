import { useState, useEffect } from 'react';
import { checkHealth } from '../../api/client';

export default function Header({ onToggleSidebar, sidebarOpen }) {
  const [healthy, setHealthy] = useState(null);

  useEffect(() => {
    const check = async () => {
      try {
        setHealthy(await checkHealth());
      } catch {
        setHealthy(false);
      }
    };
    check();
    const interval = setInterval(check, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-border bg-bg sticky top-0 z-40">
      <div className="flex items-center gap-4">
        <button
          onClick={onToggleSidebar}
          className="lg:hidden p-2 rounded-lg hover:bg-surface-hover transition-colors cursor-pointer"
          aria-label="Toggle sidebar"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            {sidebarOpen ? (
              <path d="M18 6L6 18M6 6l12 12" />
            ) : (
              <>
                <path d="M3 6h18M3 12h18M3 18h18" />
              </>
            )}
          </svg>
        </button>
        <div>
          <h1 className="text-lg font-semibold text-text tracking-tight">
            Multi-Agent Research Assistant
          </h1>
          <p className="text-xs text-text-muted mt-0.5 hidden sm:block">
            Three AI agents collaborate to find answers from your documents and the web
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <span
          className={`w-2 h-2 rounded-full ${
            healthy === null
              ? 'bg-text-muted'
              : healthy
              ? 'bg-success'
              : 'bg-error'
          }`}
        />
        <span className="text-xs text-text-muted hidden sm:inline">
          {healthy === null ? 'Checking...' : healthy ? 'Connected' : 'Offline'}
        </span>
      </div>
    </header>
  );
}
