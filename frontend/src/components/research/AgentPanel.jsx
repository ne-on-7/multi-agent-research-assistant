import Card from '../shared/GlassCard';
import StatusBadge from './StatusBadge';

const agentMeta = {
  Retriever: {
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
      </svg>
    ),
    description: 'Searches your uploaded documents',
    color: '#3b82f6',
  },
  'Web Researcher': {
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <line x1="2" y1="12" x2="22" y2="12" />
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
      </svg>
    ),
    description: 'Searches the web for context',
    color: '#14b8a6',
  },
  Synthesizer: {
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
      </svg>
    ),
    description: 'Combines all findings',
    color: '#f59e0b',
  },
};

export default function AgentPanel({ name, agentState, isActive }) {
  const meta = agentMeta[name] || agentMeta.Retriever;
  const { status, events } = agentState;

  return (
    <Card
      accent={isActive ? meta.color : undefined}
      className={`flex flex-col gap-3 ${isActive ? 'animate-fade-in' : ''}`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2.5">
          <div
            className="p-2 rounded-md"
            style={{ background: `${meta.color}15`, color: meta.color }}
          >
            {meta.icon}
          </div>
          <div>
            <h3 className="text-sm font-medium text-text">{name}</h3>
            <p className="text-xs text-text-muted">{meta.description}</p>
          </div>
        </div>
        <StatusBadge status={status} />
      </div>

      {events.length > 0 && (
        <div className="space-y-1 max-h-40 overflow-y-auto">
          {events.filter(e => e.message).map((event, i) => (
            <div
              key={i}
              className="text-xs text-text-secondary py-1 px-2 rounded bg-surface-hover animate-fade-in"
            >
              {event.message}
            </div>
          ))}
        </div>
      )}

      {events.length === 0 && (
        <div className="text-xs text-text-muted py-2">
          Waiting to start...
        </div>
      )}
    </Card>
  );
}
