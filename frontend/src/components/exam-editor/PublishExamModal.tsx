/**
 * Publish Exam Modal Component (Step 4.5).
 *
 * Implements:
 * - Pre-publish validation report display (blocking errors vs non-blocking warnings)
 * - Exam summary: Question count, total points, duration, assigned classes, affected students
 * - KaTeX formula error detection across all questions (TC-4.5-05)
 * - Blocking errors disable publish action with direct question indicators (TC-4.5-03)
 * - Formula warning bypass requiring explicit confirmation checkbox
 * - Exam re-opening confirmation (requires re-typing exam title if previously closed)
 * - Safe concurrent publish handling (TC-4.5-06)
 */

import React, { useState, useEffect } from 'react';
import {
  X,
  Send,
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
  Users,
  Clock,
  HelpCircle,
  Award,
  Layers,
  Loader2,
} from 'lucide-react';
import {
  adminApi,
  AdminQuestionItem,
  ExamDetailItem,
  ExamValidationResult,
} from '../../lib/adminApi';
import { validateLatexFormulas } from './latexUtils';

export interface PublishExamModalProps {
  readonly isOpen: boolean;
  readonly exam: ExamDetailItem;
  readonly questions: AdminQuestionItem[];
  readonly onClose: () => void;
  readonly onPublished: (updatedExam: ExamDetailItem) => void;
}

export const PublishExamModal: React.FC<PublishExamModalProps> = ({
  isOpen,
  exam,
  questions,
  onClose,
  onPublished,
}) => {
  const [loading, setLoading] = useState(true);
  const [publishing, setPublishing] = useState(false);
  const [validation, setValidation] = useState<ExamValidationResult | null>(null);
  const [formulaWarnings, setFormulaWarnings] = useState<{ questionNumber: number; count: number }[]>([]);
  const [confirmedWarnings, setConfirmedWarnings] = useState(false);
  const [confirmTitleInput, setConfirmTitleInput] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const isReopening = exam.status === 'closed';

  useEffect(() => {
    if (!isOpen) return;

    let isMounted = true;
    setLoading(true);
    setErrorMessage(null);
    setConfirmedWarnings(false);
    setConfirmTitleInput('');

    // 1. Client-side KaTeX scan across all questions (TC-4.5-05)
    const detectedWarnings: { questionNumber: number; count: number }[] = [];
    questions.forEach((q, idx) => {
      const res = validateLatexFormulas(q.content_md || '');
      if (res.count > 0) {
        detectedWarnings.push({ questionNumber: idx + 1, count: res.count });
      }
    });
    setFormulaWarnings(detectedWarnings);

    // 2. Server-side validation
    adminApi
      .validateExam(exam.id)
      .then((data) => {
        if (!isMounted) return;
        setValidation(data);
      })
      .catch((err) => {
        if (!isMounted) return;
        setErrorMessage(err?.message || 'Không thể kiểm tra tính hợp lệ của đề thi.');
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [isOpen, exam.id, questions]);

  if (!isOpen) return null;

  const blockingErrors = validation?.errors || [];
  const hasBlockingErrors = blockingErrors.length > 0;
  const hasFormulaWarnings = formulaWarnings.length > 0;
  const isTitleConfirmValid = !isReopening || confirmTitleInput.trim() === exam.title.trim();

  // Publish button is disabled when blocking errors exist, warnings not confirmed, or title mismatch
  const canPublish =
    !loading &&
    !publishing &&
    !hasBlockingErrors &&
    (!hasFormulaWarnings || confirmedWarnings) &&
    isTitleConfirmValid;

  const handlePublish = async () => {
    if (!canPublish) return;

    setPublishing(true);
    setErrorMessage(null);
    try {
      const updated = await adminApi.transitionExamStatus(exam.id, 'published', exam.version);
      onPublished(updated);
      onClose();
    } catch (err: any) {
      if (err?.code === 'exam_validation_failed') {
        setErrorMessage(err.message || 'Đề thi chưa đáp ứng điều kiện xuất bản.');
      } else if (err?.status === 409) {
        setErrorMessage('Dữ liệu đề thi đã bị thay đổi bởi người khác. Vui lòng tải lại.');
      } else {
        setErrorMessage(err?.message || 'Có lỗi xảy ra khi xuất bản đề thi.');
      }
    } finally {
      setPublishing(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="publish-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-overlay-scrim backdrop-blur-xs animate-in fade-in duration-200"
    >
      <div className="bg-surface rounded-xl border border-border-subtle shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="p-4 border-b border-border-subtle flex items-center justify-between bg-surface-elevated/40">
          <div className="flex items-center gap-2">
            <Send className="w-5 h-5 text-brand" />
            <h2 id="publish-modal-title" className="font-display font-bold text-sm text-text-primary">
              Xuất bản Đề thi &amp; Phổ biến cho Học sinh
            </h2>
          </div>
          <button
            onClick={onClose}
            disabled={publishing}
            className="p-1 rounded-md text-text-muted hover:text-text-primary hover:bg-surface-elevated transition-colors"
            title="Đóng hộp thoại"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="p-5 overflow-y-auto space-y-5 flex-1">
          {loading ? (
            <div className="flex items-center justify-center py-12 text-xs font-mono text-text-muted">
              <Loader2 className="w-5 h-5 animate-spin mr-2 text-brand" />
              <span>Đang kiểm tra tính toàn vẹn và thông số đề thi...</span>
            </div>
          ) : (
            <>
              {/* Summary Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 rounded-lg border border-border-subtle bg-surface-elevated/20 flex flex-col">
                  <div className="flex items-center gap-1.5 text-text-secondary text-xs mb-1">
                    <HelpCircle className="w-3.5 h-3.5 text-brand" />
                    <span>Số câu hỏi</span>
                  </div>
                  <span className="text-base font-bold font-mono text-text-primary">
                    {validation?.summary?.question_count ?? questions.length}
                  </span>
                </div>

                <div className="p-3 rounded-lg border border-border-subtle bg-surface-elevated/20 flex flex-col">
                  <div className="flex items-center gap-1.5 text-text-secondary text-xs mb-1">
                    <Award className="w-3.5 h-3.5 text-brand" />
                    <span>Tổng điểm</span>
                  </div>
                  <span className="text-base font-bold font-mono text-text-primary">
                    {validation?.summary?.total_points ?? '0.00'}
                  </span>
                </div>

                <div className="p-3 rounded-lg border border-border-subtle bg-surface-elevated/20 flex flex-col">
                  <div className="flex items-center gap-1.5 text-text-secondary text-xs mb-1">
                    <Clock className="w-3.5 h-3.5 text-brand" />
                    <span>Thời lượng</span>
                  </div>
                  <span className="text-base font-bold font-mono text-text-primary">
                    {exam.duration_minutes} phút
                  </span>
                </div>

                <div className="p-3 rounded-lg border border-border-subtle bg-surface-elevated/20 flex flex-col">
                  <div className="flex items-center gap-1.5 text-text-secondary text-xs mb-1">
                    <Users className="w-3.5 h-3.5 text-brand" />
                    <span>Học sinh tác động</span>
                  </div>
                  <span className="text-base font-bold font-mono text-brand">
                    {validation?.summary?.student_count ?? 0} em
                  </span>
                </div>
              </div>

              {/* Assigned Classes Preview */}
              <div className="p-3 rounded-lg border border-border-subtle bg-surface-elevated/10">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-text-secondary uppercase tracking-wider font-mono flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-brand" />
                    Lớp học được giao:
                  </span>
                  <span className="text-xs font-mono text-text-muted">
                    {exam.assigned_classes?.length || 0} lớp
                  </span>
                </div>
                {exam.assigned_classes && exam.assigned_classes.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {exam.assigned_classes.map((cls) => (
                      <span
                        key={cls.id}
                        className="px-2 py-0.5 rounded text-xs font-mono font-semibold bg-brand/10 text-brand border border-brand/20"
                      >
                        {cls.name} ({cls.code})
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-status-wrong-text font-mono">
                    Chưa phân công lớp nào cho đề thi này. Cần giao lớp trước khi xuất bản.
                  </p>
                )}
              </div>

              {/* Blocking Errors (TC-4.5-03) */}
              {hasBlockingErrors && (
                <div
                  role="alert"
                  className="p-3.5 rounded-lg border border-status-wrong-border bg-status-wrong-bg text-status-wrong-text space-y-1.5"
                >
                  <div className="flex items-center gap-2 font-bold text-xs">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    <span>Không thể xuất bản — Phát hiện {blockingErrors.length} điều kiện chưa đạt:</span>
                  </div>
                  <ul className="list-disc list-inside text-xs space-y-1 pl-1 font-mono">
                    {blockingErrors.map((err, i) => (
                      <li key={i}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* KaTeX Formula Warnings (TC-4.5-05) */}
              {hasFormulaWarnings && (
                <div className="p-3.5 rounded-lg border border-status-review-border bg-status-review-bg text-status-review-text space-y-2">
                  <div className="flex items-center gap-2 font-bold text-xs">
                    <AlertTriangle className="w-4 h-4 shrink-0" />
                    <span>Cảnh báo công thức toán LaTeX ({formulaWarnings.length} câu có thể lỗi hiển thị):</span>
                  </div>
                  <ul className="list-disc list-inside text-xs space-y-1 pl-1 font-mono">
                    {formulaWarnings.map((fw) => (
                      <li key={fw.questionNumber}>
                        Câu {fw.questionNumber}: Phát hiện {fw.count} công thức có dấu hiệu sai cú pháp KaTeX.
                      </li>
                    ))}
                  </ul>
                  <label className="flex items-start gap-2 pt-1 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={confirmedWarnings}
                      onChange={(e) => setConfirmedWarnings(e.target.checked)}
                      className="mt-0.5 rounded border-border-subtle text-brand focus:ring-brand"
                    />
                    <span className="text-xs font-semibold">
                      Tôi đã kiểm tra và chấp nhận xuất bản đề thi dù có cảnh báo cú pháp công thức.
                    </span>
                  </label>
                </div>
              )}

              {/* Re-opening Confirmation */}
              {isReopening && (
                <div className="p-3.5 rounded-lg border border-border-subtle bg-surface-elevated/30 space-y-2">
                  <span className="block text-xs font-bold text-text-primary">
                    Xác nhận mở lại đề thi đã đóng:
                  </span>
                  <p className="text-xs text-text-secondary">
                    Vui lòng gõ lại chính xác tiêu đề đề thi <strong className="font-mono text-text-primary">"{exam.title}"</strong> để xác nhận:
                  </p>
                  <input
                    type="text"
                    value={confirmTitleInput}
                    onChange={(e) => setConfirmTitleInput(e.target.value)}
                    placeholder="Nhập tiêu đề đề thi..."
                    className="w-full h-8 px-3 rounded border border-border-subtle bg-canvas text-xs font-mono text-text-primary focus:border-brand focus:outline-none"
                  />
                </div>
              )}

              {/* General error message */}
              {errorMessage && (
                <div className="p-3 rounded-lg border border-status-wrong-border bg-status-wrong-bg text-status-wrong-text text-xs font-mono flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{errorMessage}</span>
                </div>
              )}

              {/* Ready notice */}
              {!hasBlockingErrors && (!hasFormulaWarnings || confirmedWarnings) && (
                <div className="p-3 rounded-lg border border-status-correct-border bg-status-correct-bg text-status-correct-text text-xs flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  <span>Đề thi đã sẵn sàng xuất bản! Sau khi xuất bản, học sinh thuộc lớp được giao sẽ nhìn thấy đề thi.</span>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-border-subtle bg-surface-elevated/40 flex items-center justify-end gap-2.5">
          <button
            type="button"
            onClick={onClose}
            disabled={publishing}
            className="px-4 py-2 rounded-md border border-border-subtle text-xs font-semibold text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors disabled:opacity-50"
          >
            Hủy bỏ
          </button>
          <button
            type="button"
            onClick={handlePublish}
            disabled={!canPublish}
            className="px-4 py-2 rounded-md bg-brand text-xs font-semibold text-text-on-brand hover:brightness-110 active:brightness-95 transition-all flex items-center gap-1.5 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
          >
            {publishing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Đang xuất bản...</span>
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                <span>Xác nhận Xuất bản</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
