import React, { forwardRef } from 'react';
import { WifiOff, Server, AlertTriangle, Info, X } from 'lucide-react';

export interface BannerProps extends React.HTMLAttributes<HTMLDivElement> {
  readonly variant?: 'offline' | 'wake' | 'warning' | 'info';
  readonly title?: string;
  readonly message: string;
  readonly onDismiss?: () => void;
}

export const Banner = forwardRef<HTMLDivElement, BannerProps>(
  ({ variant = 'info', title, message, onDismiss, className = '', ...rest }, ref) => {
    const variantStyles = {
      offline: 'bg-status-wrong-bg/30 border-status-wrong-border text-text-primary',
      wake: 'bg-status-flag-bg/25 border-status-flag-border text-text-primary',
      warning: 'bg-status-flag-bg/25 border-status-flag-border text-text-primary',
      info: 'bg-subtle-accent/40 border-line-accent text-text-primary',
    };

    const icons = {
      offline: <WifiOff className="w-4 h-4 text-status-wrong-text shrink-0" aria-hidden="true" />,
      wake: <Server className="w-4 h-4 text-status-flag-text shrink-0 animate-pulse" aria-hidden="true" />,
      warning: <AlertTriangle className="w-4 h-4 text-status-flag-text shrink-0" aria-hidden="true" />,
      info: <Info className="w-4 h-4 text-brand shrink-0" aria-hidden="true" />,
    };

    return (
      <div
        ref={ref}
        role="alert"
        className={`w-full py-2.5 px-4 rounded-md border flex items-center justify-between gap-3 text-left transition-all ${variantStyles[variant]} ${className}`}
        {...rest}
      >
        <div className="flex items-center gap-2.5 overflow-hidden">
          {icons[variant]}
          <div className="flex items-center gap-2 flex-wrap text-xs font-sans">
            {title && <span className="font-semibold">{title}:</span>}
            <span className="text-text-secondary">{message}</span>
          </div>
        </div>

        {onDismiss && (
          <button
            type="button"
            onClick={onDismiss}
            aria-label="Đóng biểu ngữ"
            className="p-1 rounded text-text-muted hover:text-text-primary hover:bg-canvas/40 transition-colors focus:outline-none focus:ring-1 focus:ring-brand"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    );
  }
);

Banner.displayName = 'Banner';

