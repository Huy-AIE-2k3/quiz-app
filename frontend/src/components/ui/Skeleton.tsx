import React, { forwardRef } from 'react';

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  readonly variant?: 'text' | 'rect' | 'circle';
  readonly width?: string | number;
  readonly height?: string | number;
}

export const Skeleton = forwardRef<HTMLDivElement, SkeletonProps>(
  ({ variant = 'text', width, height, className = '', style, ...rest }, ref) => {
    const variantStyles = {
      text: 'h-4 w-full rounded-sm',
      rect: 'w-full h-24 rounded-md',
      circle: 'w-10 h-10 rounded-full',
    };

    const inlineStyle: React.CSSProperties = {
      ...(width !== undefined ? { width } : {}),
      ...(height !== undefined ? { height } : {}),
      ...style,
    };

    return (
      <div
        ref={ref}
        aria-hidden="true"
        style={inlineStyle}
        className={`animate-pulse bg-elevated/70 border border-line-subtle/50 ${variantStyles[variant]} ${className}`}
        {...rest}
      />
    );
  }
);

Skeleton.displayName = 'Skeleton';
