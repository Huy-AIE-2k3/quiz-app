import React, { forwardRef } from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from './Button';

export interface ErrorStateProps extends React.HTMLAttributes<HTMLDivElement> {
  readonly title?: string;
  readonly message: string;
  readonly onRetry?: () => void;
  readonly retryText?: string;
}

export const ErrorState = forwardRef<HTMLDivElement, ErrorStateProps>(
  (
    {
      title = 'Đã có lỗi xảy ra',
      message,
      onRetry,
      retryText = 'Thử lại',
      className = '',
      ...rest
    },
    ref
  ) => {
    return (
      <div
        ref={ref}
        role="alert"
        className={`flex flex-col items-center justify-center p-6 text-center rounded-lg border border-status-wrong-border bg-status-wrong-bg/20 max-w-md mx-auto ${className}`}
        {...rest}
      >
        <div className="p-3 rounded-full bg-status-wrong-bg text-status-wrong-text mb-3 border border-status-wrong-border">
          <AlertCircle className="w-8 h-8" aria-hidden="true" />
        </div>
        <h3 className="font-display font-semibold text-base text-text-primary mb-1">
          {title}
        </h3>
        <p className="font-sans text-xs text-text-secondary max-w-sm mb-4 leading-relaxed">
          {message}
        </p>
        {onRetry && (
          <Button
            variant="outline"
            size="sm"
            onClick={onRetry}
            iconLeft={<RefreshCw className="w-3.5 h-3.5" />}
          >
            {retryText}
          </Button>
        )}
      </div>
    );
  }
);

ErrorState.displayName = 'ErrorState';

