/**
 * True/False (TF) Question Configuration Editor.
 *
 * Rules:
 * - 1 to 8 statements with IDs 's1' to 's8'
 * - True/False key per statement
 * - Scoring modes: 'thpt' (standard 4 statements), 'proportional', 'all_or_nothing'
 */

import React from 'react';
import { Plus, Trash2, AlertTriangle } from 'lucide-react';

interface TfStatement {
  id: string;
  statement: string;
}

interface TfEditorProps {
  statements: TfStatement[];
  answerKey: Record<string, boolean>;
  scoringMode: 'thpt' | 'proportional' | 'all_or_nothing';
  onChangeStatements: (stmts: TfStatement[]) => void;
  onChangeAnswerKey: (key: Record<string, boolean>) => void;
  onChangeScoringMode: (mode: 'thpt' | 'proportional' | 'all_or_nothing') => void;
  disabled?: boolean;
}

export const TfEditor: React.FC<TfEditorProps> = ({
  statements = [],
  answerKey = {},
  scoringMode = 'thpt',
  onChangeStatements,
  onChangeAnswerKey,
  onChangeScoringMode,
  disabled = false,
}) => {
  const currentStatements: TfStatement[] =
    statements.length >= 1
      ? statements
      : [
          { id: 's1', statement: '' },
          { id: 's2', statement: '' },
          { id: 's3', statement: '' },
          { id: 's4', statement: '' },
        ];

  const handleStatementChange = (index: number, text: string) => {
    const updated = [...currentStatements];
    updated[index] = { ...updated[index], statement: text };
    onChangeStatements(updated);
  };

  const handleToggleAnswer = (id: string, value: boolean) => {
    if (disabled) return;
    onChangeAnswerKey({ ...answerKey, [id]: value });
  };

  const handleAddStatement = () => {
    if (currentStatements.length >= 8 || disabled) return;
    const nextIdx = currentStatements.length + 1;
    const newStmt: TfStatement = { id: `s${nextIdx}`, statement: '' };
    const updated = [...currentStatements, newStmt];
    onChangeStatements(updated);
    onChangeAnswerKey({ ...answerKey, [newStmt.id]: true });

    if (scoringMode === 'thpt' && updated.length !== 4) {
      onChangeScoringMode('proportional');
    }
  };

  const handleRemoveStatement = (index: number) => {
    if (currentStatements.length <= 1 || disabled) return;
    const filtered = currentStatements.filter((_, idx) => idx !== index);
    const renumbered = filtered.map((s, idx) => ({ ...s, id: `s${idx + 1}` }));
    onChangeStatements(renumbered);

    // Rebuild answer keys
    const newKey: Record<string, boolean> = {};
    renumbered.forEach((s) => {
      newKey[s.id] = answerKey[s.id] ?? true;
    });
    onChangeAnswerKey(newKey);

    if (scoringMode === 'thpt' && renumbered.length !== 4) {
      onChangeScoringMode('proportional');
    }
  };

  const isThptInvalid = scoringMode === 'thpt' && currentStatements.length !== 4;

  return (
    <div className="space-y-4">
      {/* Scoring Mode & Add Button */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border-subtle pb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-text-secondary">Chế độ chấm:</span>
          <select
            value={scoringMode}
            disabled={disabled}
            onChange={(e) =>
              onChangeScoringMode(e.target.value as 'thpt' | 'proportional' | 'all_or_nothing')
            }
            className="h-8 px-2.5 bg-canvas border border-border-subtle rounded-md text-xs font-mono text-text-primary focus:border-brand focus:outline-none"
          >
            <option value="thpt">Quy chuẩn THPT (0.1, 0.25, 0.5, 1.0)</option>
            <option value="proportional">Tỉ lệ thuận số ý đúng (Đều điểm)</option>
            <option value="all_or_nothing">Đúng tất cả mới có điểm</option>
          </select>
        </div>

        {currentStatements.length < 8 && !disabled && (
          <button
            type="button"
            onClick={handleAddStatement}
            className="flex items-center gap-1 text-xs text-brand hover:text-brand-hover font-medium transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Thêm mệnh đề</span>
          </button>
        )}
      </div>

      {isThptInvalid && (
        <div className="p-2.5 rounded-lg bg-status-flagged/10 border border-status-flagged/30 text-status-flagged text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>
            Quy chuẩn THPT yêu cầu đúng 4 mệnh đề (hiện có {currentStatements.length} mệnh đề). Hệ thống sẽ tự động chấm theo tỉ lệ.
          </span>
        </div>
      )}

      {/* List of Statements */}
      <div className="space-y-3">
        {currentStatements.map((stmt, idx) => {
          const letter = String.fromCharCode(97 + idx); // a, b, c, d...
          const isTrue = answerKey[stmt.id] ?? true;

          return (
            <div
              key={stmt.id}
              className="p-3 rounded-lg border border-border-subtle bg-surface hover:border-border-strong flex flex-col sm:flex-row sm:items-center gap-3 transition-colors"
            >
              <div className="flex items-center gap-2 shrink-0">
                <span className="w-6 h-6 rounded bg-elevated border border-border-strong text-text-primary font-bold font-mono text-xs flex items-center justify-center">
                  {letter})
                </span>
                <span className="text-xs text-text-muted font-mono">{stmt.id}</span>
              </div>

              {/* Statement input */}
              <input
                type="text"
                disabled={disabled}
                value={stmt.statement}
                onChange={(e) => handleStatementChange(idx, e.target.value)}
                placeholder={`Nội dung mệnh đề ${letter}) (hỗ trợ $f'(x) > 0$)...`}
                className="flex-1 bg-canvas border border-border-subtle rounded-md px-3 py-1.5 text-xs text-text-primary placeholder:text-text-muted focus:border-brand focus:outline-none"
              />

              {/* True/False Buttons */}
              <div className="flex items-center gap-1.5 shrink-0 self-end sm:self-auto">
                <button
                  type="button"
                  disabled={disabled}
                  onClick={() => handleToggleAnswer(stmt.id, true)}
                  className={`px-3 py-1 rounded-md text-xs font-mono font-semibold transition-colors ${
                    isTrue
                      ? 'bg-brand text-canvas shadow-sm'
                      : 'bg-elevated border border-border-subtle text-text-secondary hover:text-text-primary'
                  }`}
                >
                  Đúng
                </button>
                <button
                  type="button"
                  disabled={disabled}
                  onClick={() => handleToggleAnswer(stmt.id, false)}
                  className={`px-3 py-1 rounded-md text-xs font-mono font-semibold transition-colors ${
                    !isTrue
                      ? 'bg-status-wrong text-white shadow-sm'
                      : 'bg-elevated border border-border-subtle text-text-secondary hover:text-text-primary'
                  }`}
                >
                  Sai
                </button>

                {currentStatements.length > 1 && !disabled && (
                  <button
                    type="button"
                    onClick={() => handleRemoveStatement(idx)}
                    title="Xóa mệnh đề này"
                    className="p-1 ml-1 text-text-muted hover:text-status-wrong transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

