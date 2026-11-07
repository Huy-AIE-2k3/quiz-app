import React, { useRef, useState, useId } from 'react';
import { UploadCloud, File, X, AlertCircle } from 'lucide-react';

export interface FileDropzoneProps {
  readonly accept?: string;
  readonly maxSizeMb?: number;
  readonly onFileSelect: (file: File | null) => void;
  readonly currentFile?: File | null;
  readonly label?: string;
  readonly helperText?: string;
  readonly disabled?: boolean;
  readonly error?: string;
  readonly className?: string;
}

export const FileDropzone: React.FC<FileDropzoneProps> = ({
  accept,
  maxSizeMb = 10,
  onFileSelect,
  currentFile,
  label,
  helperText,
  disabled = false,
  error: externalError,
  className = '',
}) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [internalError, setInternalError] = useState<string | null>(null);
  const inputId = useId();

  const maxSizeBytes = maxSizeMb * 1024 * 1024;
  const error = externalError || internalError;

  const validateAndSelect = (file: File) => {
    setInternalError(null);
    if (file.size > maxSizeBytes) {
      setInternalError(`Dung lượng file vượt quá giới hạn cho phép (${maxSizeMb} MB)`);
      return;
    }

    if (accept) {
      const allowedExts = accept
        .split(',')
        .map((ext) => ext.trim().toLowerCase().replace('.', ''));
      const fileExt = file.name.split('.').pop()?.toLowerCase() || '';

      const isAllowed = allowedExts.some(
        (ext) => ext === fileExt || file.type.includes(ext)
      );

      if (!isAllowed) {
        setInternalError(`Định dạng file không được hỗ trợ (Cho phép: ${accept})`);
        return;
      }
    }

    onFileSelect(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (disabled) return;
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (disabled) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSelect(e.dataTransfer.files[0]);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSelect(e.target.files[0]);
    }
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (inputRef.current) inputRef.current.value = '';
    setInternalError(null);
    onFileSelect(null);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className={`w-full flex flex-col gap-1.5 text-left ${className}`}>
      {label && (
        <label htmlFor={inputId} className="text-xs font-mono font-medium text-text-secondary">
          {label}
        </label>
      )}

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        className={`relative flex flex-col items-center justify-center p-6 border-2 border-dashed rounded-lg transition-colors cursor-pointer select-none text-center ${
          disabled
            ? 'opacity-50 cursor-not-allowed bg-elevated border-line-subtle'
            : isDragOver
            ? 'border-brand bg-subtle-accent/30'
            : error
            ? 'border-status-wrong-border bg-status-wrong-bg/10 hover:border-status-wrong-text'
            : 'border-line-strong bg-surface hover:border-brand'
        }`}
      >
        <input
          ref={inputRef}
          id={inputId}
          type="file"
          accept={accept}
          disabled={disabled}
          onChange={handleInputChange}
          className="sr-only"
        />

        {currentFile ? (
          <div className="flex items-center justify-between gap-3 w-full max-w-sm p-3 rounded-md bg-canvas border border-line-subtle">
            <div className="flex items-center gap-2.5 overflow-hidden">
              <File className="w-5 h-5 text-brand shrink-0" aria-hidden="true" />
              <div className="flex flex-col text-left overflow-hidden">
                <span className="text-xs font-mono font-semibold text-text-primary truncate">
                  {currentFile.name}
                </span>
                <span className="text-[11px] font-mono text-text-muted">
                  {formatFileSize(currentFile.size)}
                </span>
              </div>
            </div>

            <button
              type="button"
              onClick={handleClear}
              aria-label="Xóa file đã chọn"
              className="p-1 rounded text-text-muted hover:text-status-wrong-text hover:bg-elevated transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <div className="p-3 rounded-full bg-elevated text-brand border border-line-subtle">
              <UploadCloud className="w-6 h-6" aria-hidden="true" />
            </div>
            <div className="flex flex-col gap-0.5">
              <p className="text-xs font-sans font-medium text-text-primary">
                Kéo thả file vào đây hoặc <span className="text-brand underline">chọn từ máy tính</span>
              </p>
              <p className="text-[11px] font-mono text-text-muted">
                {helperText || `Tối đa ${maxSizeMb} MB${accept ? ` • Định dạng: ${accept}` : ''}`}
              </p>
            </div>
          </div>
        )}
      </div>

      {error && (
        <p className="text-xs text-status-wrong-text font-sans flex items-center gap-1 mt-0.5">
          <AlertCircle className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
          <span>{error}</span>
        </p>
      )}
    </div>
  );
};

