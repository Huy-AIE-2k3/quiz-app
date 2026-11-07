import React, { forwardRef, useId } from 'react';

export interface RadioProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  readonly label?: React.ReactNode;
  readonly description?: string;
}

export const Radio = forwardRef<HTMLInputElement, RadioProps>(
  (
    {
      label,
      description,
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

    return (
      <label
        htmlFor={id}
        className={`inline-flex items-start gap-2.5 select-none ${
          disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'
        } ${className}`}
      >
        <div className="relative flex items-center justify-center mt-0.5">
          <input
            ref={ref}
            id={id}
            type="radio"
            checked={checked}
            disabled={disabled}
            onChange={onChange}
            className="peer sr-only"
            {...rest}
          />
          <div
            className={`w-4 h-4 rounded-full border transition-colors flex items-center justify-center peer-focus-visible:ring-2 peer-focus-visible:ring-brand peer-focus-visible:ring-offset-2 peer-focus-visible:ring-offset-canvas ${
              checked
                ? 'border-brand bg-canvas'
                : 'border-line-strong bg-canvas hover:border-brand'
            } ${disabled ? 'bg-elevated border-line-subtle' : ''}`}
          >
            {checked && <div className="w-2 h-2 rounded-full bg-brand" />}
          </div>
        </div>

        {(label || description) && (
          <div className="flex flex-col text-left">
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
    );
  }
);

Radio.displayName = 'Radio';
