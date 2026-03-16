const variants = {
  primary:
    'bg-accent text-white hover:bg-accent-hover disabled:opacity-40 disabled:hover:bg-accent',
  secondary:
    'border border-border text-text-secondary hover:border-border-hover hover:text-text hover:bg-surface-hover',
  danger:
    'border border-error/30 text-error hover:bg-error/10 hover:border-error/50',
  ghost:
    'text-text-secondary hover:text-text hover:bg-surface-hover',
};

export default function Button({
  children,
  variant = 'primary',
  className = '',
  ...props
}) {
  return (
    <button
      className={`px-4 py-2.5 rounded-lg font-medium text-sm cursor-pointer transition-colors duration-150 disabled:cursor-not-allowed ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
