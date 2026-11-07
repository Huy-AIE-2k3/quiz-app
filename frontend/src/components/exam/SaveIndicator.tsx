import React from 'react';
import { Check, Loader2, WifiOff, AlertCircle } from 'lucide-react';

export type SaveStatus = 'saved' | 'saving' | 'offline' | 'error';

export interface SaveIndicatorProps {
  readonly status: SaveStatus;
  readonly lastSavedAt?: Date | string;
  readonly onRetry?: () => void;
  readonly className?: string;
}

export const SaveIndicator: React.FC<SaveIndicatorProps> = ({
  status,
  lastSavedAt,
  onRetry,
  className = '',
}) => {
  const configs = {
    saved: {
      icon: <Check className="w-3.5 h-3.5 text-status-correct-text" aria-hidden="true" />,
      text: 'Đã lưu',
      colorClass: 'text-text-secondary',
      srText: 'Bài làm đã được lưu an toàn',
    },
    saving: {
      icon: <Loader2 className="w-3.5 h-3.5 text-brand animate-spin" aria-hidden="true" />,
      text: 'Đang lưu...',
      colorClass: 'text-brand',
      srText: 'Đang đồng bộ câu trả lời...',
    },
    offline: {
      icon: <WifiOff className="w-3.5 h-3.5 text-status-flag-text" aria-hidden="true" />,
      text: 'Đã lưu cục bộ (Mất mạng)',
      colorClass: 'text-status-flag-text',
      srText: 'Đang mất kết nối, bài làm đã lưu tạm trong trình duyệt',
    },
    error: {
      icon: <AlertCircle className="w-3.5 h-3.5 text-status-wrong-text" aria-hidden="true" />,
      text: 'Lỗi lưu',
      colorClass: 'text-status-wrong-text',
      srText: 'Lỗi đồng bộ bài làm lên máy chủ',
    },
  };

  const current = configs[status];

  return (
    <div
      data-testid="save-indicator"
      data-save-status={status}
      className={`inline-flex items-center gap-2 text-xs font-mono select-none ${current.colorClass} ${className}`}
    >
      <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-canvas border border-line-subtle">
        {current.icon}
        <span>{current.text}</span>
      </div>

      {status === 'error' && onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="text-xs text-status-wrong-text underline hover:opacity-80 focus:outline-none"
        >
          Thử lại
        </button>
      )}

      {lastSavedAt && status === 'saved' && (
        <span className="text-[11px] text-text-muted hidden sm:inline">
          {typeof lastSavedAt === 'string'
            ? lastSavedAt
            : lastSavedAt.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
        </span>
      )}

      <span aria-live="polite" className="sr-only">
        {current.srText}
      </span>
    </div>
  );
};
