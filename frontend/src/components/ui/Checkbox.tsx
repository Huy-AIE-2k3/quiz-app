import React, { forwardRef, useId } from 'react';
import { Check } from 'lucide-react';

export interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  readonly label?: React.ReactNode;
  readonly description?: string;
  readonly error?: string;
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  (
    {
      label,
      description,
      error,
      id: customId,
      checked,
      disabled,
      className = '',
      onChange,
      ...rest
    },
    ref
  ) => {
    const generatedId = useId();
    const id = customId || generatedId;
    const errorId = `${id}-error`;

    return (
      <div className={`flex flex-col gap-1 text-left ${className}`}>
        <label htmlFor={id} className={`inline-flex items-start gap-2.5 select-none ${disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}>
          <div className="relative flex items-center justify-center mt-0.5">
            <input
              ref={ref}
              id={id}
              type="checkbox"
              checked={checked}
              disabled={disabled}
              onChange={onChange}
              aria-invalid={Boolean(error)}
              aria-describedby={error ? errorId : undefined}
              className="peer sr-only"
              {...rest}
            />
            <div
              className={`w-4 h-4 rounded border transition-colors flex items-center justify-center peer-focus-visible:ring-2 peer-focus-visible:ring-brand peer-focus-visible:ring-offset-2 peer-focus-visible:ring-offset-canvas ${
                checked
                  ? 'bg-brand border-brand text-canvas'
                  : error
                  ? 'border-status-wrong-border bg-canvas hover:border-status-wrong-text'
                  : 'border-line-strong bg-canvas hover:border-brand'
              } ${disabled ? 'bg-elevated border-line-subtle' : ''}`}
            >
              {checked && <Check className="w-3 h-3 stroke-[3]" aria-hidden="true" />}
            </div>
          </div>

          {(label || description) && (
            <div className="flex flex-col">
              {label && (
                <span className="text-sm font-sans font-medium text-text-primary leading-tight">
                  {label}
                </span>
              )}
              {description && (
                <span className="text-xs font-sans text-text-muted mt-0.5">
                  {description}
                </span>
              )}
            </div>
          )}
        </label>

        {error && (
          <p id={errorId} className="text-xs text-status-wrong-text font-sans pl-6">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Checkbox.displayName = 'Checkbox';
