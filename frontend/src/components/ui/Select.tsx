import React, { forwardRef, useId } from 'react';
import { ChevronDown } from 'lucide-react';

export interface SelectOption {
  readonly value: string;
  readonly label: string;
  readonly disabled?: boolean;
}

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  readonly label?: string;
  readonly error?: string;
  readonly helperText?: string;
  readonly placeholder?: string;
  readonly options: readonly SelectOption[];
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  (
    {
      label,
      error,
      helperText,
      placeholder,
      options,
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

    return (
      <div className="w-full flex flex-col gap-1.5 text-left">
        {label && (
          <label htmlFor={id} className="text-xs font-mono font-medium text-text-secondary">
            {label}
            {required && <span className="text-status-wrong-text ml-1">*</span>}
          </label>
        )}

        <div className="relative flex items-center">
          <select
            ref={ref}
            id={id}
            disabled={disabled}
            required={required}
            aria-invalid={Boolean(error)}
            aria-describedby={error ? errorId : helperText ? helperId : undefined}
            className={`w-full h-10 pl-3.5 pr-10 rounded-md bg-canvas border text-text-primary text-sm font-sans transition-colors appearance-none focus:outline-none focus:ring-1 ${
              error
                ? 'border-status-wrong-border focus:ring-status-wrong-border focus:border-status-wrong-border'
                : 'border-line-subtle focus:ring-brand focus:border-brand'
            } ${disabled ? 'opacity-50 cursor-not-allowed bg-elevated' : 'hover:border-line-strong cursor-pointer'} ${className}`}
            {...rest}
          >
            {placeholder && (
              <option value="" disabled className="bg-surface text-text-muted">
                {placeholder}
              </option>
            )}
            {options.map((opt) => (
              <option key={opt.value} value={opt.value} disabled={opt.disabled} className="bg-surface text-text-primary">
                {opt.label}
              </option>
            ))}
          </select>

          <ChevronDown
            className="w-4 h-4 text-text-muted absolute right-3 pointer-events-none"
            aria-hidden="true"
          />
        </div>

        {error && (
          <p id={errorId} className="text-xs text-status-wrong-text font-sans">
            {error}
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

Select.displayName = 'Select';

