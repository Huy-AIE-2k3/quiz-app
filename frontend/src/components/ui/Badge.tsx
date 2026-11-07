import React, { forwardRef } from 'react';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  readonly variant?: 'neutral' | 'brand' | 'warning' | 'danger' | 'info';
  readonly size?: 'sm' | 'md';
  readonly dot?: boolean;
}

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ variant = 'neutral', size = 'md', dot = false, className = '', children, ...rest }, ref) => {
    const sizeStyles = {
      sm: 'px-2 py-0.5 text-[11px]',
      md: 'px-2.5 py-1 text-xs',
    };

    const variantStyles = {
      neutral: 'bg-elevated text-text-secondary border-line-subtle',
      brand: 'bg-status-correct-bg text-status-correct-text border-status-correct-border',
      warning: 'bg-status-flag-bg text-status-flag-text border-status-flag-border',
      danger: 'bg-status-wrong-bg text-status-wrong-text border-status-wrong-border',
      info: 'bg-subtle-accent text-brand border-line-accent',
    };

    const dotColors = {
      neutral: 'bg-text-muted',
      brand: 'bg-brand',
      warning: 'bg-status-flag-text',
      danger: 'bg-status-wrong-text',
      info: 'bg-brand',
    };

    return (
      <span
        ref={ref}
        className={`inline-flex items-center gap-1.5 font-mono font-medium rounded border ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
        {...rest}
      >
        {dot && <span className={`w-1.5 h-1.5 rounded-full ${dotColors[variant]}`} aria-hidden="true" />}
        <span>{children}</span>
      </span>
    );
  }
);

Badge.displayName = 'Badge';

