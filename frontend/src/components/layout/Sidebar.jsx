import PdfUpload from '../ingestion/PdfUpload';
import UrlIngestion from '../ingestion/UrlIngestion';
import GithubIngestion from '../ingestion/GithubIngestion';
import DocumentList from '../ingestion/DocumentList';

export default function Sidebar({ open, documents, onRefresh, onClearAll, onToast }) {
  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div className="fixed inset-0 bg-black/60 z-30 lg:hidden" />
      )}

      <aside
        className={`fixed lg:sticky top-0 left-0 h-screen w-80 border-r border-border bg-bg z-30
          overflow-y-auto transition-transform duration-300 ease-out pt-[65px] lg:pt-0
          ${open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}
      >
        <div className="p-5 space-y-5">
          <div>
            <h2 className="text-sm font-semibold text-text uppercase tracking-wider mb-1">
              Document Sources
            </h2>
            <p className="text-xs text-text-muted">
              Upload documents for the agents to research
            </p>
          </div>

          <PdfUpload onSuccess={onRefresh} onToast={onToast} />
          <UrlIngestion onSuccess={onRefresh} onToast={onToast} />
          <GithubIngestion onSuccess={onRefresh} onToast={onToast} />

          <div className="border-t border-border pt-4">
            <DocumentList
              documents={documents}
              onClear={onClearAll}
            />
          </div>
        </div>
      </aside>
    </>
  );
}
