import React, { useEffect, useRef, useId } from 'react';
import { X } from 'lucide-react';

export interface ModalProps {
  readonly isOpen: boolean;
  readonly onClose: () => void;
  readonly title?: React.ReactNode;
  readonly description?: React.ReactNode;
  readonly children: React.ReactNode;
  readonly footer?: React.ReactNode;
  readonly size?: 'sm' | 'md' | 'lg' | 'xl';
  readonly className?: string;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  footer,
  size = 'md',
  className = '',
}) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const previousActiveElementRef = useRef<HTMLElement | null>(null);
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;
  const titleId = useId();
  const descId = useId();

  // Focus trap, Escape key, and body scroll lock
  useEffect(() => {
    if (!isOpen) {
      if (previousActiveElementRef.current) {
        previousActiveElementRef.current.focus?.();
        previousActiveElementRef.current = null;
      }
      return;
    }

    previousActiveElementRef.current = document.activeElement as HTMLElement | null;
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onCloseRef.current();
        return;
      }

      if (e.key === 'Tab' && modalRef.current) {
        const focusableElements = modalRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [href], input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"]):not([disabled])'
        );
        if (focusableElements.length === 0) return;

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (e.shiftKey && document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        } else if (!e.shiftKey && document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    // Initial focus on open: prioritize form inputs or explicit autofocus over the close button
    const timer = setTimeout(() => {
      if (!modalRef.current) return;
      // Never steal focus if user is already typing or interacting inside the modal
      if (modalRef.current.contains(document.activeElement)) return;

      // 1. Explicit autofocus attribute
      const explicitAutoFocus = modalRef.current.querySelector<HTMLElement>(
        '[autofocus], [data-autofocus]'
      );
      if (explicitAutoFocus) {
        explicitAutoFocus.focus();
        return;
      }

      // 2. First editable form input / textarea / select
      const firstInput = modalRef.current.querySelector<HTMLElement>(
        'input:not([type="hidden"]):not([disabled]), textarea:not([disabled]), select:not([disabled])'
      );
      if (firstInput) {
        firstInput.focus();
        return;
      }

      // 3. Main action button in footer (excluding close button)
      const actionButton = modalRef.current.querySelector<HTMLElement>(
        'button:not([aria-label="Đóng hộp thoại"]):not([disabled])'
      );
      if (actionButton) {
        actionButton.focus();
        return;
      }

      // 4. Fallback to any focusable element
      const firstFocusable = modalRef.current.querySelector<HTMLElement>(
        'button:not([disabled]), [href], [tabindex]:not([tabindex="-1"])'
      );
      firstFocusable?.focus();
    }, 50);

    return () => {
      document.body.style.overflow = originalOverflow;
      window.removeEventListener('keydown', handleKeyDown);
      clearTimeout(timer);
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-2xl',
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? titleId : undefined}
      aria-describedby={description ? descId : undefined}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-canvas/80 backdrop-blur-xs animate-in fade-in duration-150"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={modalRef}
        className={`w-full ${sizeClasses[size]} bg-surface border border-line-subtle rounded-lg shadow-xl text-text-primary p-6 relative flex flex-col gap-4 text-left ${className}`}
      >
        <button
          type="button"
          onClick={onClose}
          aria-label="Đóng hộp thoại"
          className="absolute right-4 top-4 p-1 rounded-md text-text-muted hover:text-text-primary hover:bg-elevated transition-colors focus:outline-none focus:ring-1 focus:ring-brand"
        >
          <X className="w-4 h-4" />
        </button>

        {(title || description) && (
          <div className="flex flex-col gap-1 pr-6 border-b border-line-subtle pb-3">
            {title && (
              <h2 id={titleId} className="font-display font-semibold text-lg text-text-primary leading-tight">
                {title}
              </h2>
            )}
            {description && (
              <p id={descId} className="text-xs font-sans text-text-muted leading-relaxed">
                {description}
              </p>
            )}
          </div>
        )}

        <div className="flex-1 overflow-y-auto max-h-[70vh] py-1">{children}</div>

        {footer && <div className="flex items-center justify-end gap-3 pt-3 border-t border-line-subtle">{footer}</div>}
      </div>
    </div>
  );
};

