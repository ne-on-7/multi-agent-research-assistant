import { useEffect } from 'react';

export default function Toast({ message, type = 'success', onClose }) {
  useEffect(() => {
    const timer = setTimeout(onClose, 4000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const colors = {
    success: 'border-success/40 bg-success/10 text-success',
    error: 'border-error/40 bg-error/10 text-error',
    warning: 'border-warning/40 bg-warning/10 text-warning',
  };

  return (
    <div className={`fixed top-6 right-6 z-50 animate-fade-in bg-surface px-5 py-3 border ${colors[type]} rounded-lg text-sm font-medium max-w-sm`}>
      {message}
    </div>
  );
}
