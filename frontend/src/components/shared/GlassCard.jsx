import { forwardRef } from 'react';

const Card = forwardRef(function Card({ children, className = '', accent, ...props }, ref) {
  const accentStyle = accent
    ? { borderTopColor: accent, borderTopWidth: '2px' }
    : {};

  return (
    <div
      ref={ref}
      className={`card p-5 transition-colors duration-200 ${className}`}
      style={accentStyle}
      {...props}
    >
      {children}
    </div>
  );
});

export default Card;
