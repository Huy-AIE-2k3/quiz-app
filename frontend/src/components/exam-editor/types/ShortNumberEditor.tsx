/**
 * Short Number (Điền số) Question Configuration Editor.
 *
 * Rules:
 * - 1 to 10 parseable numeric target values (e.g. '1.5', '3/2', '1.5e-3')
 * - Tolerance >= 0, type 'abs' | 'rel'
 * - TC-4.4-10: Live test box for teachers to enter test inputs ('1,5', '3/2', etc.) and see real-time evaluation.
 */

import React, { useState } from 'react';
import { Plus, Trash2, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import { evaluateShortNumberTest } from '../latexUtils';

interface ShortNumberEditorProps {
  values: string[];
  tolerance: number;
  toleranceType: 'abs' | 'rel';
  onChangeValues: (vals: string[]) => void;
  onChangeTolerance: (tol: number) => void;
  onChangeToleranceType: (tt: 'abs' | 'rel') => void;
  disabled?: boolean;
}

export const ShortNumberEditor: React.FC<ShortNumberEditorProps> = ({
  values = [],
  tolerance = 0.01,
  toleranceType = 'abs',
  onChangeValues,
  onChangeTolerance,
  onChangeToleranceType,
  disabled = false,
}) => {
  const [newValue, setNewValue] = useState('');
  const [testInput, setTestInput] = useState('');

  const handleAdd = () => {
    const trimmed = newValue.trim();
    if (!trimmed || values.length >= 10 || values.includes(trimmed) || disabled) return;
    onChangeValues([...values, trimmed]);
    setNewValue('');
  };

  const handleRemove = (index: number) => {
    if (disabled) return;
    onChangeValues(values.filter((_, idx) => idx !== index));
  };

  // Run live test box evaluation (TC-4.4-10)
  const testResult = evaluateShortNumberTest(testInput, values, tolerance, toleranceType);

  return (
    <div className="space-y-4">
      {/* Target values + Tolerance controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 rounded-xl bg-surface border border-border-subtle">
        {/* Target values */}
        <div className="space-y-2">
          <label className="block text-xs font-bold text-text-secondary uppercase tracking-wider font-mono">
            Giá trị đúng (1-10 giá trị, số/phân số):
          </label>
          {!disabled && (
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={newValue}
                onChange={(e) => setNewValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAdd();
                  }
                }}
                placeholder="Ví dụ: 1.5 hoặc 3/2 hoặc -0.75..."
                className="flex-1 bg-canvas border border-border-subtle rounded-md px-3 py-1.5 text-xs text-text-primary placeholder:text-text-muted focus:border-brand focus:outline-none"
              />
              <button
                type="button"
                onClick={handleAdd}
                disabled={!newValue.trim() || values.length >= 10}
                className="h-8 px-3 rounded-md bg-brand hover:bg-brand-hover text-canvas font-semibold text-xs flex items-center gap-1 transition-colors disabled:opacity-50"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Thêm</span>
              </button>
            </div>
          )}

          {/* Chips list */}
          <div className="flex flex-wrap gap-2 pt-1">
            {values.length === 0 ? (
              <span className="text-xs text-status-flagged font-mono">
                ⚠️ Cần ít nhất 1 giá trị số mục tiêu.
              </span>
            ) : (
              values.map((val, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md bg-elevated border border-border-strong text-xs font-mono text-brand font-bold"
                >
                  <span>{val}</span>
                  {!disabled && (
                    <button
                      type="button"
                      onClick={() => handleRemove(idx)}
                      className="text-text-muted hover:text-status-wrong transition-colors"
                      title="Xóa giá trị này"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  )}
                </span>
              ))
            )}
          </div>
        </div>

        {/* Tolerance config */}
        <div className="space-y-2">
          <label className="block text-xs font-bold text-text-secondary uppercase tracking-wider font-mono">
            Sai số cho phép:
          </label>
          <div className="flex items-center gap-3">
            <input
              type="number"
              step="0.001"
              min="0"
              disabled={disabled}
              value={tolerance}
              onChange={(e) => onChangeTolerance(parseFloat(e.target.value) || 0)}
              className="w-28 h-8 px-2.5 bg-canvas border border-border-subtle rounded-md text-xs font-mono font-semibold text-text-primary text-right focus:border-brand focus:outline-none"
            />
            <select
              value={toleranceType}
              disabled={disabled}
              onChange={(e) => onChangeToleranceType(e.target.value as 'abs' | 'rel')}
              className="h-8 px-2.5 bg-canvas border border-border-subtle rounded-md text-xs font-mono text-text-primary focus:border-brand focus:outline-none"
            >
              <option value="abs">Tuyệt đối (± Δ)</option>
              <option value="rel">Tương đối (± %)</option>
            </select>
          </div>
          <p className="text-[11px] text-text-muted">
            Ví dụ: Sai số 0.01 tuyệt đối cho phép kết quả từ 1.49 đến 1.51.
          </p>
        </div>
      </div>

      {/* TC-4.4-10: Live Quick-Test Box for Teachers */}
      <div className="p-3.5 rounded-xl bg-canvas border border-border-strong/70 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono font-semibold text-text-secondary flex items-center gap-1.5">
            <span>🧪</span>
            <span>Khung thử nghiệm chấm số trực tiếp (Quick Test):</span>
          </span>
          <span className="text-[10px] text-text-muted font-mono">
            Hỗ trợ thử dấu phẩy (1,5) và phân số (3/2)
          </span>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center gap-3">
          <input
            type="text"
            value={testInput}
            onChange={(e) => setTestInput(e.target.value)}
            placeholder="Nhập giá trị học sinh có thể gõ (ví dụ: 1,5 hoặc 3/2)..."
            className="flex-1 bg-surface border border-border-subtle rounded-md px-3 py-1.5 text-xs font-mono text-text-primary focus:border-brand focus:outline-none"
          />

          {/* Test Status Badge */}
          {testInput.trim() ? (
            <div className="flex items-center gap-2 shrink-0">
              {testResult.isCorrect ? (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-brand/10 border border-brand/40 text-brand text-xs font-mono font-semibold">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>
                    Chính xác! (≈ {testResult.parsedNumber}, khớp '{testResult.matchedTarget}')
                  </span>
                </span>
              ) : testResult.isValidNumber ? (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-status-wrong/10 border border-status-wrong/40 text-status-wrong text-xs font-mono font-semibold">
                  <XCircle className="w-3.5 h-3.5" />
                  <span>
                    Sai! (≈ {testResult.parsedNumber}, lệch ngoài sai số cho phép)
                  </span>
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-status-flagged/10 border border-status-flagged/40 text-status-flagged text-xs font-mono">
                  <AlertCircle className="w-3.5 h-3.5" />
                  <span>Không phân tích được định dạng số</span>
                </span>
              )}
            </div>
          ) : (
            <span className="text-[11px] text-text-muted font-mono shrink-0">
              Nhập số ở ô bên trái để kiểm tra ngay
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

