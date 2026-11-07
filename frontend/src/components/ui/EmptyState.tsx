import React, { forwardRef } from 'react';
import { Inbox } from 'lucide-react';

export interface EmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  readonly icon?: React.ReactNode;
  readonly title: string;
  readonly description?: string;
  readonly action?: React.ReactNode;
}

export const EmptyState = forwardRef<HTMLDivElement, EmptyStateProps>(
  ({ icon, title, description, action, className = '', ...rest }, ref) => {
    return (
      <div
        ref={ref}
        className={`flex flex-col items-center justify-center p-8 text-center rounded-lg border border-dashed border-line-strong bg-surface/50 max-w-md mx-auto ${className}`}
        {...rest}
      >
        <div className="p-3 rounded-full bg-elevated text-text-muted mb-3 border border-line-subtle">
          {icon || <Inbox className="w-8 h-8" aria-hidden="true" />}
        </div>
        <h3 className="font-display font-semibold text-base text-text-primary mb-1">
          {title}
        </h3>
        {description && (
          <p className="font-sans text-xs text-text-muted max-w-sm mb-4 leading-relaxed">
            {description}
          </p>
        )}
        {action && <div className="mt-1">{action}</div>}
      </div>
    );
  }
);

EmptyState.displayName = 'EmptyState';
