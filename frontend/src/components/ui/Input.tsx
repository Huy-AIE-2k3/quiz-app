import React, { forwardRef, useState, useId } from 'react';
import { Eye, EyeOff } from 'lucide-react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  readonly label?: string;
  readonly error?: string;
  readonly helperText?: string;
  readonly iconLeft?: React.ReactNode;
  readonly iconRight?: React.ReactNode;
  readonly isPasswordToggle?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      helperText,
      iconLeft,
      iconRight,
      isPasswordToggle = false,
      type = 'text',
      id: customId,
      disabled,
      required,
      className = '',
      ...rest
    },
    ref
  ) => {
    const generatedId = useId();
    const id = customId || generatedId;
    const errorId = `${id}-error`;
    const helperId = `${id}-helper`;
    const [showPassword, setShowPassword] = useState(false);

    const actualType = isPasswordToggle ? (showPassword ? 'text' : 'password') : type;

    return (
      <div className="w-full flex flex-col gap-1.5 text-left">
        {label && (
          <label htmlFor={id} className="text-xs font-mono font-medium text-text-secondary">
            {label}
            {required && <span className="text-status-wrong-text ml-1">*</span>}
          </label>
        )}

        <div className="relative flex items-center">
          {iconLeft && (
            <div className="absolute left-3 text-text-muted pointer-events-none flex items-center">
              {iconLeft}
            </div>
          )}

          <input
            ref={ref}
            id={id}
            type={actualType}
            disabled={disabled}
            required={required}
            aria-invalid={Boolean(error)}
            aria-describedby={error ? errorId : helperText ? helperId : undefined}
            className={`w-full h-10 px-3.5 rounded-md bg-canvas border text-text-primary text-sm font-sans transition-colors placeholder:text-text-muted focus:outline-none focus:ring-1 ${
              error
                ? 'border-status-wrong-border focus:ring-status-wrong-border focus:border-status-wrong-border'
                : 'border-line-subtle focus:ring-brand focus:border-brand'
            } ${disabled ? 'opacity-50 cursor-not-allowed bg-elevated' : 'hover:border-line-strong'} ${
              iconLeft ? 'pl-10' : ''
            } ${iconRight || isPasswordToggle ? 'pr-10' : ''} ${className}`}
            {...rest}
          />

          {isPasswordToggle ? (
            <button
              type="button"
              onClick={() => setShowPassword((prev) => !prev)}
              aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
              className="absolute right-3 text-text-muted hover:text-text-primary transition-colors focus:outline-none"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          ) : (
            iconRight && (
              <div className="absolute right-3 text-text-muted pointer-events-none flex items-center">
                {iconRight}
              </div>
            )
          )}
        </div>

        {error && (
          <p id={errorId} className="text-xs text-status-wrong-text font-sans flex items-center gap-1">
            <span>{error}</span>
          </p>
        )}

        {!error && helperText && (
          <p id={helperId} className="text-xs text-text-muted font-sans">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
