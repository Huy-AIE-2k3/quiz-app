import React, { forwardRef, useId, useState } from 'react';

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  readonly label?: string;
  readonly error?: string;
  readonly helperText?: string;
  readonly showCount?: boolean;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      label,
      error,
      helperText,
      showCount = false,
      maxLength,
      id: customId,
      disabled,
      required,
      value,
      defaultValue,
      onChange,
      className = '',
      rows = 4,
      ...rest
    },
    ref
  ) => {
    const generatedId = useId();
    const id = customId || generatedId;
    const errorId = `${id}-error`;
    const helperId = `${id}-helper`;

    const [currentLength, setCurrentLength] = useState<number>(() => {
      if (typeof value === 'string') return value.length;
      if (typeof defaultValue === 'string') return defaultValue.length;
      return 0;
    });

    const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setCurrentLength(e.target.value.length);
      onChange?.(e);
    };

    return (
      <div className="w-full flex flex-col gap-1.5 text-left">
        <div className="flex items-center justify-between">
          {label && (
            <label htmlFor={id} className="text-xs font-mono font-medium text-text-secondary">
              {label}
              {required && <span className="text-status-wrong-text ml-1">*</span>}
            </label>
          )}

          {showCount && maxLength && (
            <span className="text-xs font-mono text-text-muted">
              {currentLength} / {maxLength}
            </span>
          )}
        </div>

        <textarea
          ref={ref}
          id={id}
          rows={rows}
          maxLength={maxLength}
          disabled={disabled}
          required={required}
          value={value}
          defaultValue={defaultValue}
          onChange={handleChange}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? errorId : helperText ? helperId : undefined}
          className={`w-full p-3 rounded-md bg-canvas border text-text-primary text-sm font-sans transition-colors placeholder:text-text-muted focus:outline-none focus:ring-1 resize-y ${
            error
              ? 'border-status-wrong-border focus:ring-status-wrong-border focus:border-status-wrong-border'
              : 'border-line-subtle focus:ring-brand focus:border-brand'
          } ${disabled ? 'opacity-50 cursor-not-allowed bg-elevated' : 'hover:border-line-strong'} ${className}`}
          {...rest}
        />

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

Textarea.displayName = 'Textarea';

