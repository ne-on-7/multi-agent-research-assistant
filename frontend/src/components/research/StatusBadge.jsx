const statusConfig = {
  idle: { label: 'Idle', color: 'bg-text-muted', textColor: 'text-text-muted', pulse: false },
  thinking: { label: 'Thinking', color: 'bg-accent', textColor: 'text-accent', pulse: true },
  searching: { label: 'Searching', color: 'bg-accent', textColor: 'text-accent', pulse: true },
  generating: { label: 'Generating', color: 'bg-warning', textColor: 'text-warning', pulse: true },
  done: { label: 'Complete', color: 'bg-success', textColor: 'text-success', pulse: false },
  error: { label: 'Error', color: 'bg-error', textColor: 'text-error', pulse: false },
};

export default function StatusBadge({ status }) {
  const config = statusConfig[status] || statusConfig.idle;

  return (
    <div className="flex items-center gap-2">
      <span
        className={`w-1.5 h-1.5 rounded-full ${config.color} ${config.pulse ? 'animate-pulse-dot' : ''}`}
      />
      <span className={`text-xs font-medium uppercase tracking-wide ${config.textColor}`}>
        {config.label}
      </span>
    </div>
  );
}
