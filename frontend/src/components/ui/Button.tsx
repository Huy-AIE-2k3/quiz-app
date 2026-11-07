import React, { useState, forwardRef } from 'react';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  readonly variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  readonly size?: 'sm' | 'md' | 'lg';
  readonly loading?: boolean;
  readonly loadingText?: string;
  readonly iconLeft?: React.ReactNode;
  readonly iconRight?: React.ReactNode;
  readonly preventDoubleClick?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      loading = false,
      loadingText,
      iconLeft,
      iconRight,
      preventDoubleClick = true,
      disabled,
      className = '',
      children,
      onClick,
      type = 'button',
      ...rest
    },
    ref
  ) => {
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleClick = async (e: React.MouseEvent<HTMLButtonElement>) => {
      if (loading || isSubmitting || disabled) {
        e.preventDefault();
        return;
      }

      if (!onClick) return;

      if (type === 'submit' || preventDoubleClick) {
        setIsSubmitting(true);
        try {
          const result: unknown = onClick(e);
          if (result != null && typeof (result as { then?: unknown }).then === 'function') {
            await (result as Promise<unknown>);
          }
        } finally {
          setIsSubmitting(false);
        }
      } else {
        onClick(e);
      }
    };

    const isBusy = loading || isSubmitting;
    const isDisabled = disabled || isBusy;

    const baseStyles =
      'inline-flex items-center justify-center font-display font-semibold transition-all duration-150 rounded-md focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 focus:ring-offset-canvas active:scale-[0.98] select-none';

    const sizeStyles = {
      sm: 'h-8 px-3 text-xs gap-1.5',
      md: 'h-10 px-4 text-sm gap-2',
      lg: 'h-12 px-6 text-base gap-2.5',
    };

    const variantStyles = {
      primary:
        'bg-brand text-canvas hover:bg-brand-hover shadow-sm active:bg-brand-hover disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100',
      secondary:
        'bg-elevated text-text-primary border border-line-subtle hover:bg-surface hover:border-line-strong disabled:opacity-50 disabled:cursor-not-allowed',
      outline:
        'bg-transparent text-text-primary border border-line-strong hover:bg-elevated disabled:opacity-50 disabled:cursor-not-allowed',
      ghost:
        'bg-transparent text-text-secondary hover:text-text-primary hover:bg-surface disabled:opacity-50 disabled:cursor-not-allowed',
      danger:
        'bg-status-wrong-bg text-status-wrong-text border border-status-wrong-border hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed',
    };

    return (
      <button
        ref={ref}
        type={type}
        disabled={isDisabled}
        aria-busy={isBusy ? 'true' : undefined}
        onClick={handleClick}
        className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
        {...rest}
      >
        {isBusy ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" data-testid="button-spinner" />
            <span>{loadingText || children}</span>
          </>
        ) : (
          <>
            {iconLeft && <span className="inline-flex shrink-0">{iconLeft}</span>}
            <span>{children}</span>
            {iconRight && <span className="inline-flex shrink-0">{iconRight}</span>}
          </>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';
