/**
 * File Upload Question Configuration Editor.
 *
 * Rules:
 * - max_files: 1 to 5
 * - max_mb: 1 to 10 MB
 * - allowed_ext: list of safe extensions
 */

import React from 'react';

const COMMON_EXTENSIONS = ['pdf', 'png', 'jpg', 'jpeg', 'cpp', 'py', 'zip', 'docx'];

interface FileUploadEditorProps {
  maxFiles: number;
  maxMb: number;
  allowedExt: string[];
  onChangeMaxFiles: (mf: number) => void;
  onChangeMaxMb: (mb: number) => void;
  onChangeAllowedExt: (ext: string[]) => void;
  disabled?: boolean;
}

export const FileUploadEditor: React.FC<FileUploadEditorProps> = ({
  maxFiles = 1,
  maxMb = 5,
  allowedExt = ['pdf', 'png', 'jpg'],
  onChangeMaxFiles,
  onChangeMaxMb,
  onChangeAllowedExt,
  disabled = false,
}) => {
  const toggleExt = (ext: string) => {
    if (disabled) return;
    if (allowedExt.includes(ext)) {
      if (allowedExt.length > 1) {
        onChangeAllowedExt(allowedExt.filter((e) => e !== ext));
      }
    } else {
      onChangeAllowedExt([...allowedExt, ext]);
    }
  };

  return (
    <div className="space-y-4 p-4 rounded-xl bg-surface border border-border-subtle">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Max Files */}
        <div className="space-y-1.5">
          <label className="block text-xs font-mono text-text-secondary">
            Số lượng tệp tối đa (1 - 5):
          </label>
          <input
            type="number"
            min="1"
            max="5"
            disabled={disabled}
            value={maxFiles}
            onChange={(e) => onChangeMaxFiles(Math.min(5, Math.max(1, parseInt(e.target.value) || 1)))}
            className="w-full h-8 px-2.5 bg-canvas border border-border-subtle rounded-md text-xs font-mono text-text-primary focus:border-brand focus:outline-none"
          />
        </div>

        {/* Max Size in MB */}
        <div className="space-y-1.5">
          <label className="block text-xs font-mono text-text-secondary">
            Dung lượng mỗi tệp tối đa (1 - 10 MB):
          </label>
          <input
            type="number"
            min="1"
            max="10"
            disabled={disabled}
            value={maxMb}
            onChange={(e) => onChangeMaxMb(Math.min(10, Math.max(1, parseInt(e.target.value) || 1)))}
            className="w-full h-8 px-2.5 bg-canvas border border-border-subtle rounded-md text-xs font-mono text-text-primary focus:border-brand focus:outline-none"
          />
        </div>
      </div>

      {/* Allowed Extensions */}
      <div className="space-y-2">
        <label className="block text-xs font-mono text-text-secondary">
          Định dạng tệp cho phép nộp:
        </label>
        <div className="flex flex-wrap gap-3">
          {COMMON_EXTENSIONS.map((ext) => {
            const isChecked = allowedExt.includes(ext);
            return (
              <label
                key={ext}
                className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-md border text-xs font-mono cursor-pointer transition-colors ${
                  isChecked
                    ? 'bg-brand/10 border-brand text-brand font-semibold'
                    : 'bg-canvas border-border-subtle text-text-secondary hover:border-border-strong'
                }`}
              >
                <input
                  type="checkbox"
                  disabled={disabled}
                  checked={isChecked}
                  onChange={() => toggleExt(ext)}
                  className="hidden"
                />
                <span>.{ext}</span>
              </label>
            );
          })}
        </div>
      </div>
    </div>
  );
};

