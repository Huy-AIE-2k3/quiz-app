import React, { forwardRef } from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  readonly variant?: 'default' | 'elevated' | 'subtle' | 'interactive';
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ variant = 'default', className = '', children, ...rest }, ref) => {
    const variantStyles = {
      default: 'bg-surface border-line-subtle',
      elevated: 'bg-elevated border-line-subtle',
      subtle: 'bg-transparent border-line-subtle',
      interactive:
        'bg-surface border-line-subtle hover:border-brand hover:shadow-sm transition-all duration-150 cursor-pointer',
    };

    return (
      <div
        ref={ref}
        className={`rounded-lg border text-text-primary p-5 ${variantStyles[variant]} ${className}`}
        {...rest}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';

export interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {}
export const CardHeader = forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className = '', children, ...rest }, ref) => (
    <div ref={ref} className={`flex flex-col space-y-1.5 pb-4 mb-4 border-b border-line-subtle ${className}`} {...rest}>
      {children}
    </div>
  )
);
CardHeader.displayName = 'CardHeader';

export interface CardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  readonly as?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';
}
export const CardTitle = forwardRef<HTMLHeadingElement, CardTitleProps>(
  ({ as: Tag = 'h3', className = '', children, ...rest }, ref) => (
    <Tag ref={ref} className={`font-display font-semibold text-lg text-text-primary leading-tight ${className}`} {...rest}>
      {children}
    </Tag>
  )
);
CardTitle.displayName = 'CardTitle';

export interface CardDescriptionProps extends React.HTMLAttributes<HTMLParagraphElement> {}
export const CardDescription = forwardRef<HTMLParagraphElement, CardDescriptionProps>(
  ({ className = '', children, ...rest }, ref) => (
    <p ref={ref} className={`text-xs font-sans text-text-muted leading-relaxed ${className}`} {...rest}>
      {children}
    </p>
  )
);
CardDescription.displayName = 'CardDescription';

export interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {}
export const CardContent = forwardRef<HTMLDivElement, CardContentProps>(
  ({ className = '', children, ...rest }, ref) => (
    <div ref={ref} className={`space-y-4 ${className}`} {...rest}>
      {children}
    </div>
  )
);
CardContent.displayName = 'CardContent';

export interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {}
export const CardFooter = forwardRef<HTMLDivElement, CardFooterProps>(
  ({ className = '', children, ...rest }, ref) => (
    <div ref={ref} className={`flex items-center pt-4 mt-4 border-t border-line-subtle ${className}`} {...rest}>
      {children}
    </div>
  )
);
CardFooter.displayName = 'CardFooter';

