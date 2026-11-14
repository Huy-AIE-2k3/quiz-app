/**
 * Short Text (Trả lời ngắn) Question Configuration Editor.
 *
 * Rules:
 * - 1 to 20 accepted string answers (for auto-grading)
 * - Grading mode: 'auto' | 'manual'
 * - Toggles: case_sensitive, ignore_accents, review_wrong
 */

import React, { useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';

interface ShortTextEditorProps {
  accepted: string[];
  grading: 'auto' | 'manual';
  caseSensitive: boolean;
  ignoreAccents: boolean;
  reviewWrong: boolean;
  onChangeAccepted: (acc: string[]) => void;
  onChangeGrading: (g: 'auto' | 'manual') => void;
  onChangeCaseSensitive: (cs: boolean) => void;
  onChangeIgnoreAccents: (ia: boolean) => void;
  onChangeReviewWrong: (rw: boolean) => void;
  disabled?: boolean;
}

export const ShortTextEditor: React.FC<ShortTextEditorProps> = ({
  accepted = [],
  grading = 'auto',
  caseSensitive = false,
  ignoreAccents = false,
  reviewWrong = false,
  onChangeAccepted,
  onChangeGrading,
  onChangeCaseSensitive,
  onChangeIgnoreAccents,
  onChangeReviewWrong,
  disabled = false,
}) => {
  const [newText, setNewText] = useState('');

  const handleAdd = () => {
    const trimmed = newText.trim();
    if (!trimmed || accepted.length >= 20 || accepted.includes(trimmed) || disabled) return;
    onChangeAccepted([...accepted, trimmed]);
    setNewText('');
  };

  const handleRemove = (index: number) => {
    if (disabled) return;
    onChangeAccepted(accepted.filter((_, idx) => idx !== index));
  };

  return (
    <div className="space-y-4">
      {/* Grading mode toggle */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-3 rounded-lg bg-surface border border-border-subtle">
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-text-secondary">Phương thức chấm:</span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={disabled}
              onClick={() => onChangeGrading('auto')}
              className={`px-3 py-1 rounded text-xs font-mono font-medium transition-colors ${
                grading === 'auto'
                  ? 'bg-brand text-canvas font-bold'
                  : 'bg-canvas text-text-secondary hover:text-text-primary'
              }`}
            >
              Tự động khớp chuỗi
            </button>
            <button
              type="button"
              disabled={disabled}
              onClick={() => onChangeGrading('manual')}
              className={`px-3 py-1 rounded text-xs font-mono font-medium transition-colors ${
                grading === 'manual'
                  ? 'bg-brand text-canvas font-bold'
                  : 'bg-canvas text-text-secondary hover:text-text-primary'
              }`}
            >
              Giáo viên chấm tay
            </button>
          </div>
        </div>

        {/* Option toggles */}
        <div className="flex flex-wrap items-center gap-4 text-xs">
          <label className="flex items-center gap-1.5 cursor-pointer text-text-secondary">
            <input
              type="checkbox"
              disabled={disabled}
              checked={caseSensitive}
              onChange={(e) => onChangeCaseSensitive(e.target.value === 'on' ? e.target.checked : false)}
              className="accent-emerald-500 rounded"
            />
            <span>Phân biệt hoa/thường</span>
          </label>

          <label className="flex items-center gap-1.5 cursor-pointer text-text-secondary">
            <input
              type="checkbox"
              disabled={disabled}
              checked={ignoreAccents}
              onChange={(e) => onChangeIgnoreAccents(e.target.checked)}
              className="accent-emerald-500 rounded"
            />
            <span>Bỏ qua dấu tiếng Việt</span>
          </label>

          <label className="flex items-center gap-1.5 cursor-pointer text-text-secondary">
            <input
              type="checkbox"
              disabled={disabled}
              checked={reviewWrong}
              onChange={(e) => onChangeReviewWrong(e.target.checked)}
              className="accent-emerald-500 rounded"
            />
            <span>Đánh dấu cần xem lại nếu sai</span>
          </label>
        </div>
      </div>

      {/* Accepted answers list (only if auto grading) */}
      {grading === 'auto' && (
        <div className="space-y-3">
          <label className="block text-xs font-bold text-text-secondary uppercase tracking-wider font-mono">
            Danh sách đáp án chấp nhận (Tối đa 20 đáp án):
          </label>

          {/* Add input */}
          {!disabled && (
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={newText}
                onChange={(e) => setNewText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAdd();
                  }
                }}
                placeholder="Nhập đáp án chuẩn và nhấn Enter (ví dụ: Hà Nội, Ha Noi)..."
                className="flex-1 bg-canvas border border-border-subtle rounded-md px-3 py-1.5 text-xs text-text-primary placeholder:text-text-muted focus:border-brand focus:outline-none"
              />
              <button
                type="button"
                onClick={handleAdd}
                disabled={!newText.trim() || accepted.length >= 20}
                className="h-8 px-3 rounded-md bg-brand hover:bg-brand-hover text-canvas font-semibold text-xs flex items-center gap-1 transition-colors disabled:opacity-50"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Thêm</span>
              </button>
            </div>
          )}

          {/* Chips list */}
          <div className="flex flex-wrap gap-2 pt-1">
            {accepted.length === 0 ? (
              <span className="text-xs text-status-flagged font-mono">
                ⚠️ Chưa có đáp án chấp nhận nào. Vui lòng thêm ít nhất 1 đáp án.
              </span>
            ) : (
              accepted.map((item, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md bg-elevated border border-border-strong text-xs font-mono text-text-primary"
                >
                  <span>{item}</span>
                  {!disabled && (
                    <button
                      type="button"
                      onClick={() => handleRemove(idx)}
                      className="text-text-muted hover:text-status-wrong transition-colors"
                      title="Xóa đáp án này"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  )}
                </span>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};
