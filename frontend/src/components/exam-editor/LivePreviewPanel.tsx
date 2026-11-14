/**
 * Live Preview Panel for Exam Editor.
 *
 * Implements Step 4.4:
 * - Real-time student-faithful rendering using MathText
 * - TC-4.4-02: Student view never leaks correct answers
 * - TC-4.4-08: KaTeX formula syntax error detection with inline banner and error counter
 */

import React, { useMemo } from 'react';
import { MathText } from '../ui/MathText';
import { AdminQuestionItem } from '../../lib/adminApi';
import { validateLatexFormulas } from './latexUtils';
import { AlertTriangle, Eye } from 'lucide-react';

interface LivePreviewPanelProps {
  question: AdminQuestionItem | null;
  positionNumber: number;
  onFormulaErrorsChange?: (count: number) => void;
}

export const LivePreviewPanel: React.FC<LivePreviewPanelProps> = ({
  question,
  positionNumber,
  onFormulaErrorsChange,
}) => {
  // Aggregate text for KaTeX validation
  const allTextToValidate = useMemo(() => {
    if (!question) return '';
    let text = question.content_md || '';
    if (question.explanation_md) text += `\n${question.explanation_md}`;

    if (question.type === 'mcq' && Array.isArray(question.config?.options)) {
      question.config.options.forEach((o: any) => {
        text += `\n${o.content_md || ''}`;
      });
    } else if (question.type === 'tf' && Array.isArray(question.config?.statements)) {
      question.config.statements.forEach((s: any) => {
        text += `\n${s.statement || ''}`;
      });
    }
    return text;
  }, [question]);

  // KaTeX syntax error detection (TC-4.4-08)
  const validationResult = useMemo(() => {
    return validateLatexFormulas(allTextToValidate);
  }, [allTextToValidate]);

  // Report error count to parent
  React.useEffect(() => {
    onFormulaErrorsChange?.(validationResult.count);
  }, [validationResult.count, onFormulaErrorsChange]);

  if (!question) {
    return (
      <aside className="w-80 lg:w-96 border-l border-border-subtle bg-surface/30 p-6 flex flex-col items-center justify-center text-center text-text-muted text-xs font-mono">
        <Eye className="w-8 h-8 mb-2 opacity-40" />
        <span>Chọn một câu hỏi ở danh sách bên trái để xem trước giao diện học sinh.</span>
      </aside>
    );
  }

  const options = question.config?.options || [];
  const statements = question.config?.statements || [];

  return (
    <aside className="w-80 lg:w-[420px] border-l border-border-subtle bg-surface/30 flex flex-col shrink-0 h-full overflow-hidden select-none">
      {/* Header */}
      <div className="p-3 border-b border-border-subtle flex items-center justify-between bg-surface">
        <div className="flex items-center gap-2">
          <Eye className="w-3.5 h-3.5 text-brand" />
          <span className="font-display text-xs font-bold text-text-primary uppercase tracking-wider">
            Xem trước (Góc nhìn học sinh)
          </span>
        </div>
        <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-brand/10 text-brand font-semibold">
          {question.points} điểm
        </span>
      </div>

      {/* KaTeX Syntax Warning Banner (TC-4.4-08) */}
      {validationResult.count > 0 && (
        <div className="p-3 bg-status-wrong/10 border-b border-status-wrong/30 text-xs text-status-wrong space-y-1">
          <div className="flex items-center gap-1.5 font-bold font-mono">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>Phát hiện {validationResult.count} lỗi cú pháp công thức KaTeX:</span>
          </div>
          <ul className="list-disc list-inside space-y-0.5 font-mono text-[11px] opacity-90">
            {validationResult.errors.map((err, idx) => (
              <li key={idx} className="truncate">
                <code>${err.formula}$</code>: {err.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Main Preview Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 font-sans text-xs">
        {/* Question Header & Content */}
        <div className="p-4 rounded-xl bg-canvas border border-border-subtle space-y-3">
          <div className="flex items-center gap-2 font-mono font-bold text-xs text-brand">
            <span>Câu {String(positionNumber).padStart(2, '0')}:</span>
            <span className="text-text-muted font-normal">
              ({question.points} điểm)
            </span>
          </div>

          {/* Rendered Question Markdown & Math (TC-4.4-02: exact same renderer) */}
          <div className="text-text-primary leading-relaxed">
            {question.content_md ? (
              <MathText content={question.content_md} />
            ) : (
              <span className="text-text-muted italic">Đang nhập nội dung đề bài...</span>
            )}
          </div>
        </div>

        {/* Options / Statements Preview (Faithful to Student View, TC-4.4-02: NO ANSWERS LEAKED) */}
        {question.type === 'mcq' && (
          <div className="space-y-2">
            <span className="block font-mono text-[11px] text-text-muted uppercase">
              Chọn một đáp án đúng:
            </span>
            <div className="space-y-1.5">
              {options.map((opt: any, idx: number) => {
                const letter = String.fromCharCode(65 + idx);
                return (
                  <div
                    key={opt.id || idx}
                    className="p-3 rounded-lg border border-border-subtle bg-canvas hover:border-brand/40 flex items-start gap-3 transition-colors"
                  >
                    <span className="w-5 h-5 rounded-full border border-border-strong bg-elevated text-text-secondary font-mono font-bold flex items-center justify-center text-[10px] shrink-0 mt-0.5">
                      {letter}
                    </span>
                    <div className="flex-1 text-text-primary leading-relaxed">
                      {opt.content_md ? (
                        <MathText content={opt.content_md} />
                      ) : (
                        <span className="text-text-muted italic font-mono">[Phương án {letter}]</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {question.type === 'tf' && (
          <div className="space-y-2">
            <span className="block font-mono text-[11px] text-text-muted uppercase">
              Xác định tính Đúng / Sai của từng mệnh đề:
            </span>
            <div className="space-y-2">
              {statements.map((stmt: any, idx: number) => {
                const letter = String.fromCharCode(97 + idx);
                return (
                  <div
                    key={stmt.id || idx}
                    className="p-3 rounded-lg border border-border-subtle bg-canvas flex flex-col sm:flex-row sm:items-center justify-between gap-2"
                  >
                    <div className="flex items-start gap-2 flex-1">
                      <span className="font-mono font-bold text-text-secondary shrink-0">
                        {letter})
                      </span>
                      <div className="text-text-primary leading-relaxed">
                        {stmt.statement ? (
                          <MathText content={stmt.statement} />
                        ) : (
                          <span className="text-text-muted italic font-mono">[Mệnh đề {letter}]</span>
                        )}
                      </div>
                    </div>
                    {/* Read-only True/False buttons as seen by student */}
                    <div className="flex items-center gap-1.5 shrink-0 self-end sm:self-auto opacity-70">
                      <span className="px-2.5 py-0.5 rounded border border-border-subtle bg-elevated text-[11px] font-mono text-text-secondary">
                        Đúng
                      </span>
                      <span className="px-2.5 py-0.5 rounded border border-border-subtle bg-elevated text-[11px] font-mono text-text-secondary">
                        Sai
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {question.type === 'short_number' && (
          <div className="space-y-2">
            <span className="block font-mono text-[11px] text-text-muted uppercase">
              Điền kết quả số:
            </span>
            <div className="p-3 rounded-lg border border-border-subtle bg-canvas">
              <input
                type="text"
                readOnly
                placeholder="Học sinh nhập đáp án số (ví dụ: 1.5)..."
                className="w-full bg-elevated border border-border-strong rounded-md px-3 py-2 text-xs font-mono text-text-muted cursor-not-allowed"
              />
            </div>
          </div>
        )}

        {question.type === 'short_text' && (
          <div className="space-y-2">
            <span className="block font-mono text-[11px] text-text-muted uppercase">
              Trả lời ngắn:
            </span>
            <div className="p-3 rounded-lg border border-border-subtle bg-canvas">
              <input
                type="text"
                readOnly
                placeholder="Học sinh nhập câu trả lời văn bản ngắn..."
                className="w-full bg-elevated border border-border-strong rounded-md px-3 py-2 text-xs text-text-muted cursor-not-allowed"
              />
            </div>
          </div>
        )}

        {question.type === 'file_upload' && (
          <div className="space-y-2">
            <span className="block font-mono text-[11px] text-text-muted uppercase">
              Khu vực nộp tệp bài làm:
            </span>
            <div className="p-6 rounded-lg border border-dashed border-border-strong bg-canvas text-center space-y-2">
              <span className="text-text-muted font-mono text-[11px] block">
                Kéo thả hoặc chọn tệp để nộp (Tối đa {question.config?.max_files || 1} tệp,{' '}
                {question.config?.max_mb || 5} MB)
              </span>
              <span className="inline-block px-3 py-1 rounded bg-elevated text-text-secondary text-[11px] font-mono">
                Định dạng: {(question.config?.allowed_ext || ['pdf', 'png']).join(', ')}
              </span>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};
