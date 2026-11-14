/**
 * Multiple Choice (MCQ) Question Configuration Editor.
 *
 * Rules:
 * - 2 to 8 options with IDs 'o1' to 'o8'
 * - Radio button to pick correct answer
 */

import React from 'react';
import { Plus, Trash2, CheckCircle2 } from 'lucide-react';

interface McqOption {
  id: string;
  content_md: string;
}

interface McqEditorProps {
  options: McqOption[];
  correctOptionId: string;
  onChangeOptions: (opts: McqOption[]) => void;
  onChangeCorrect: (correctId: string) => void;
  disabled?: boolean;
}

export const McqEditor: React.FC<McqEditorProps> = ({
  options = [],
  correctOptionId,
  onChangeOptions,
  onChangeCorrect,
  disabled = false,
}) => {
  const currentOptions: McqOption[] =
    options.length >= 2
      ? options
      : [
          { id: 'o1', content_md: '' },
          { id: 'o2', content_md: '' },
          { id: 'o3', content_md: '' },
          { id: 'o4', content_md: '' },
        ];

  const handleContentChange = (index: number, content: string) => {
    const updated = [...currentOptions];
    updated[index] = { ...updated[index], content_md: content };
    onChangeOptions(updated);
  };

  const handleAddOption = () => {
    if (currentOptions.length >= 8 || disabled) return;
    const nextIdx = currentOptions.length + 1;
    const newOption: McqOption = { id: `o${nextIdx}`, content_md: '' };
    onChangeOptions([...currentOptions, newOption]);
  };

  const handleRemoveOption = (index: number) => {
    if (currentOptions.length <= 2 || disabled) return;
    const toRemove = currentOptions[index];
    const filtered = currentOptions.filter((_, idx) => idx !== index);
    // Renumber option IDs sequentially o1..on
    const renumbered = filtered.map((opt, idx) => ({ ...opt, id: `o${idx + 1}` }));
    onChangeOptions(renumbered);

    if (correctOptionId === toRemove.id) {
      onChangeCorrect(renumbered[0]?.id || 'o1');
    } else {
      // Find new ID of previous correct
      const oldIndex = currentOptions.findIndex((o) => o.id === correctOptionId);
      if (oldIndex !== -1 && oldIndex < renumbered.length) {
        onChangeCorrect(renumbered[oldIndex].id);
      }
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="block text-xs font-bold text-text-secondary uppercase tracking-wider font-mono">
          Các phương án lựa chọn (Chọn 1 đáp án đúng):
        </label>
        {currentOptions.length < 8 && !disabled && (
          <button
            type="button"
            onClick={handleAddOption}
            className="flex items-center gap-1 text-xs text-brand hover:text-brand-hover font-medium transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Thêm phương án</span>
          </button>
        )}
      </div>

      <div className="space-y-2.5">
        {currentOptions.map((opt, idx) => {
          const isCorrect = correctOptionId === opt.id;
          const letter = String.fromCharCode(65 + idx); // A, B, C, D...

          return (
            <div
              key={opt.id}
              className={`p-2.5 rounded-lg border transition-all flex items-center gap-3 ${
                isCorrect
                  ? 'border-brand/60 bg-brand/5 shadow-sm'
                  : 'border-border-subtle bg-surface hover:border-border-strong'
              }`}
            >
              {/* Radio button for correct answer */}
              <button
                type="button"
                disabled={disabled}
                onClick={() => onChangeCorrect(opt.id)}
                title={`Đặt phương án ${letter} làm đáp án đúng`}
                className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs shrink-0 transition-all ${
                  isCorrect
                    ? 'bg-brand text-canvas ring-2 ring-brand/30 shadow'
                    : 'bg-elevated border border-border-strong text-text-secondary hover:border-brand hover:text-brand'
                }`}
              >
                {isCorrect ? <CheckCircle2 className="w-4 h-4" /> : letter}
              </button>

              {/* Option content input */}
              <input
                type="text"
                disabled={disabled}
                value={opt.content_md}
                onChange={(e) => handleContentChange(idx, e.target.value)}
                placeholder={`Nội dung phương án ${letter} (hỗ trợ $x^2$)...`}
                className="flex-1 bg-canvas border border-border-subtle rounded-md px-3 py-1.5 text-xs text-text-primary placeholder:text-text-muted focus:border-brand focus:outline-none"
              />

              {/* Remove button (when > 2 options) */}
              {currentOptions.length > 2 && !disabled && (
                <button
                  type="button"
                  onClick={() => handleRemoveOption(idx)}
                  title="Xóa phương án này"
                  className="p-1 text-text-muted hover:text-status-wrong transition-colors shrink-0"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
