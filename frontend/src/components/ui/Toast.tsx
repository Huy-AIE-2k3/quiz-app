import React, { useState, useCallback, ReactNode } from 'react';
import { CheckCircle2, AlertTriangle, AlertCircle, Info, X } from 'lucide-react';
import { ToastContext, ToastItem } from './ToastContext';

export interface ToastProviderProps {
  readonly children: ReactNode;
}

export const ToastProvider: React.FC<ToastProviderProps> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback(
    ({ type, title, message, duration = 4000 }: Omit<ToastItem, 'id'>) => {
      const id = `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
      setToasts((prev) => [...prev, { id, type, title, message, duration }]);

      if (duration > 0) {
        setTimeout(() => {
          removeToast(id);
        }, duration);
      }

      return id;
    },
    [removeToast]
  );

  const toast = {
    success: (message: string, title?: string) => showToast({ type: 'success', message, title }),
    error: (message: string, title?: string) => showToast({ type: 'error', message, title }),
    warning: (message: string, title?: string) => showToast({ type: 'warning', message, title }),
    info: (message: string, title?: string) => showToast({ type: 'info', message, title }),
  };

  return (
    <ToastContext.Provider value={{ showToast, removeToast, toast }}>
      {children}
      <div
        aria-live="polite"
        className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none"
      >
        {toasts.map((t) => (
          <div
            key={t.id}
            role="status"
            className={`pointer-events-auto p-3.5 rounded-lg border shadow-lg flex items-start gap-3 bg-surface text-text-primary transition-all duration-200 animate-in slide-in-from-bottom-2 ${
              t.type === 'success'
                ? 'border-status-correct-border bg-status-correct-bg/10'
                : t.type === 'error'
                ? 'border-status-wrong-border bg-status-wrong-bg/10'
                : t.type === 'warning'
                ? 'border-status-flag-border bg-status-flag-bg/10'
                : 'border-line-accent bg-subtle-accent/20'
            }`}
          >
            <div className="shrink-0 mt-0.5">
              {t.type === 'success' && (
                <CheckCircle2 className="w-4 h-4 text-status-correct-text" aria-hidden="true" />
              )}
              {t.type === 'error' && (
                <AlertCircle className="w-4 h-4 text-status-wrong-text" aria-hidden="true" />
              )}
              {t.type === 'warning' && (
                <AlertTriangle className="w-4 h-4 text-status-flag-text" aria-hidden="true" />
              )}
              {t.type === 'info' && <Info className="w-4 h-4 text-brand" aria-hidden="true" />}
            </div>

            <div className="flex-1 text-left">
              {t.title && (
                <h4 className="font-display font-semibold text-xs text-text-primary mb-0.5">
                  {t.title}
                </h4>
              )}
              <p className="font-sans text-xs text-text-secondary leading-relaxed">{t.message}</p>
            </div>

            <button
              type="button"
              onClick={() => removeToast(t.id)}
              aria-label="Đóng thông báo"
              className="text-text-muted hover:text-text-primary p-0.5 rounded transition-colors focus:outline-none focus:ring-1 focus:ring-brand"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};
