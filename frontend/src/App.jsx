import { useState, useCallback } from 'react';
import Header from './components/layout/Header';
import Sidebar from './components/layout/Sidebar';
import QueryInput from './components/research/QueryInput';
import AgentPanelGrid from './components/research/AgentPanelGrid';
import AnswerDisplay from './components/answer/AnswerDisplay';
import SourcesList from './components/answer/SourcesList';
import Toast from './components/shared/Toast';
import { useDocuments } from './hooks/useDocuments';
import { useSSEQuery } from './hooks/useSSEQuery';

const suggestions = [
  'What are the key findings in the uploaded research paper?',
  'Summarize the main architecture decisions in this codebase',
  'Compare recent developments in transformer architectures',
];

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [toast, setToast] = useState(null);
  const { documents, refresh, clearAll } = useDocuments();
  const { agents, answer, sources, isStreaming, error, runQuery } = useSSEQuery();

  const hasResults = answer || isStreaming;

  const handleToast = useCallback((message, type = 'success') => {
    setToast({ message, type });
  }, []);

  const handleQuery = useCallback((query) => {
    setSidebarOpen(false);
    runQuery(query);
  }, [runQuery]);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        open={sidebarOpen}
        documents={documents}
        onRefresh={refresh}
        onClearAll={clearAll}
        onToast={handleToast}
      />

      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        <Header
          onToggleSidebar={() => setSidebarOpen((o) => !o)}
          sidebarOpen={sidebarOpen}
        />

        <main className="flex-1 overflow-y-auto">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-8">
            {/* Hero section when no results */}
            {!hasResults && (
              <div className="text-center pt-16 pb-8 animate-fade-in">
                <h2 className="text-3xl sm:text-4xl font-bold text-text mb-3 tracking-tight">
                  Research anything with
                  <br />
                  three AI agents
                </h2>
                <p className="text-text-secondary text-sm max-w-md mx-auto leading-relaxed">
                  Upload documents, paste URLs, or link GitHub repos. Our agents search your sources
                  and the web to synthesize comprehensive answers.
                </p>
              </div>
            )}

            {/* Query input */}
            <QueryInput onSubmit={handleQuery} disabled={isStreaming} />

            {/* Suggestion chips when idle */}
            {!hasResults && (
              <div className="flex flex-wrap justify-center gap-2 animate-fade-in">
                {suggestions.map((s) => (
                  <button
                    key={s}
                    onClick={() => handleQuery(s)}
                    className="px-3.5 py-2 rounded-lg text-xs text-text-muted border border-border
                      hover:border-border-hover hover:text-text-secondary hover:bg-surface-hover
                      transition-colors cursor-pointer"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}

            {/* Agent panels */}
            {hasResults && (
              <AgentPanelGrid agents={agents} isActive={isStreaming} />
            )}

            {/* Error display */}
            {error && (
              <div className="bg-surface border border-error/30 p-4 rounded-lg text-sm text-error animate-fade-in">
                {error}
              </div>
            )}

            {/* Answer */}
            <AnswerDisplay answer={answer} isStreaming={isStreaming} />

            {/* Sources */}
            {!isStreaming && <SourcesList sources={sources} />}

            {/* Footer */}
            <footer className="text-center py-6 border-t border-border">
              <p className="text-xs text-text-muted">
                Built with FastAPI, FAISS, Claude AI & Gemini &mdash; Multi-Agent Architecture with Real-Time Streaming
              </p>
            </footer>
          </div>
        </main>
      </div>

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}
