/**
 * Version Conflict (409) Resolution Modal.
 *
 * Implements Step 4.4 & TC-4.4-07:
 * - Alerts teacher that another tab/user updated the question
 * - Allows copying pending local content to clipboard before reloading
 * - Allows reloading latest version or forcing overwrite
 */

import React, { useState } from 'react';
import { AlertTriangle, Copy, RefreshCw, Check } from 'lucide-react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';

interface VersionConflictModalProps {
  isOpen: boolean;
  localContent: string;
  onReload: () => void;
  onOverwrite: () => void;
  onClose: () => void;
}

export const VersionConflictModal: React.FC<VersionConflictModalProps> = ({
  isOpen,
  localContent,
  onReload,
  onOverwrite,
  onClose,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(localContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Xung đột phiên bản dữ liệu (409 Conflict)"
    >
      <div className="space-y-4 text-xs font-sans text-text-primary">
        <div className="p-3.5 rounded-lg bg-status-wrong/10 border border-status-wrong/30 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-status-wrong shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-bold text-status-wrong text-sm block">
              Phát hiện thay đổi từ phiên làm việc khác!
            </span>
            <p className="text-text-secondary leading-relaxed">
              Câu hỏi này vừa được lưu từ một tab hoặc quản trị viên khác. Để tránh mất dữ liệu ngoài ý muốn, bạn có thể sao chép nội dung vừa gõ vào bộ nhớ tạm trước khi tải lại.
            </p>
          </div>
        </div>

        {/* Copy current content section */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="font-mono text-text-muted text-[11px]">Nội dung bạn vừa soạn:</span>
            <button
              type="button"
              onClick={handleCopy}
              className="flex items-center gap-1 text-brand hover:text-brand-hover font-mono text-[11px] font-semibold transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Đã sao chép!' : 'Sao chép vào Clipboard'}</span>
            </button>
          </div>
          <pre className="p-3 rounded-lg bg-canvas border border-border-subtle font-mono text-[11px] text-text-secondary max-h-32 overflow-y-auto whitespace-pre-wrap">
            {localContent || '(Chưa có nội dung)'}
          </pre>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row items-center justify-end gap-2 pt-2 border-t border-border-subtle">
          <Button variant="secondary" onClick={onReload} className="w-full sm:w-auto">
            <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
            <span>Tải lại bản mới nhất</span>
          </Button>
          <Button variant="danger" onClick={onOverwrite} className="w-full sm:w-auto">
            <span>Ghi đè bằng nội dung này</span>
          </Button>
        </div>
      </div>
    </Modal>
  );
};
