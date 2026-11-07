import React from 'react';
import { Modal } from './Modal';
import { Button } from './Button';
import { AlertTriangle } from 'lucide-react';

export interface ConfirmDialogProps {
  readonly isOpen: boolean;
  readonly onClose: () => void;
  readonly onConfirm: () => void | Promise<void>;
  readonly title: string;
  readonly description: string;
  readonly confirmText?: string;
  readonly cancelText?: string;
  readonly variant?: 'danger' | 'brand';
  readonly loading?: boolean;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  description,
  confirmText = 'Xác nhận',
  cancelText = 'Hủy bỏ',
  variant = 'brand',
  loading = false,
}) => {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      size="sm"
      footer={
        <>
          <Button variant="ghost" size="sm" onClick={onClose} disabled={loading}>
            {cancelText}
          </Button>
          <Button
            variant={variant === 'danger' ? 'danger' : 'primary'}
            size="sm"
            onClick={onConfirm}
            loading={loading}
          >
            {confirmText}
          </Button>
        </>
      }
    >
      <div className="flex items-start gap-3 py-2">
        <div
          className={`p-2 rounded-full shrink-0 ${
            variant === 'danger'
              ? 'bg-status-wrong-bg text-status-wrong-text border border-status-wrong-border'
              : 'bg-status-correct-bg text-status-correct-text border border-status-correct-border'
          }`}
        >
          <AlertTriangle className="w-5 h-5" aria-hidden="true" />
        </div>
        <div className="flex flex-col gap-1 text-left">
          <h3 className="font-display font-semibold text-base text-text-primary leading-tight">
            {title}
          </h3>
          <p className="text-xs font-sans text-text-secondary leading-relaxed">
            {description}
          </p>
        </div>
      </div>
    </Modal>
  );
};

