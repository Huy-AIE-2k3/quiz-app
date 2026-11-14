/**
 * Teacher Sandbox Preview Page (Step 4.5 & TC-4.5-01).
 *
 * Implements:
 * - Real-time student-faithful exam taking simulation running purely in memory (RAM).
 * - Zero server-side state writes: NO rows written to `attempts` or `answers`, `locked_at` remains unchanged.
 * - Prominent amber sandbox banner: "Chế độ xem trước — Không lưu bài vào hệ thống".
 * - Simulated monotonic countdown timer based on `duration_minutes`.
 * - Question palette navigation and local answer tracking.
 * - Trial submit simulation showing instant feedback summary.
 */

import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Clock,
  Send,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  FileUp,
} from 'lucide-react';
import {
  adminApi,
  ExamPreviewResponse,
  ExamPreviewQuestion,
} from '../../lib/adminApi';
import { MathText } from '../../components/ui/MathText';

export const AdminExamSandboxPreviewPage: React.FC = () => {
  const { examId } = useParams<{ examId: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [examData, setExamData] = useState<ExamPreviewResponse | null>(null);

  // In-memory student answer state (RAM only)
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [activeQuestionIdx, setActiveQuestionIdx] = useState(0);

  // Simulated countdown timer (seconds)
  const [secondsRemaining, setSecondsRemaining] = useState<number>(0);

  // Trial submission modal
  const [showSubmitModal, setShowSubmitModal] = useState(false);

  useEffect(() => {
    if (!examId) return;

    let isMounted = true;
    setLoading(true);
    setError(null);

    adminApi
      .getExamPreview(examId)
      .then((data) => {
        if (!isMounted) return;
        setExamData(data);
        setSecondsRemaining(data.duration_minutes * 60);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err?.message || 'Không thể tải bản xem trước đề thi.');
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [examId]);

  // Simulated timer tick
  useEffect(() => {
    if (loading || secondsRemaining <= 0) return;

    const interval = setInterval(() => {
      setSecondsRemaining((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);

    return () => clearInterval(interval);
  }, [loading, secondsRemaining]);

  if (loading) {
    return (
      <div className="min-h-screen bg-canvas flex items-center justify-center text-xs font-mono text-text-muted">
        <Loader2 className="w-5 h-5 animate-spin mr-2 text-brand" />
        <span>Đang nạp chế độ xem trước học sinh (Sandbox)...</span>
      </div>
    );
  }

  if (error || !examData) {
    return (
      <div className="min-h-screen bg-canvas flex items-center justify-center p-4">
        <div className="bg-surface rounded-xl border border-status-wrong-border p-6 max-w-md w-full text-center space-y-4">
          <p className="text-xs text-status-wrong-text font-mono">{error || 'Không tìm thấy đề thi.'}</p>
          <button
            onClick={() => navigate(-1)}
            className="px-4 py-2 rounded-md bg-surface-elevated text-xs font-semibold text-text-primary hover:bg-border-subtle transition-colors cursor-pointer"
          >
            Quay lại
          </button>
        </div>
      </div>
    );
  }

  const questions = examData.questions;
  const currentQuestion = questions[activeQuestionIdx] as ExamPreviewQuestion | undefined;

  const formatTimer = (totalSeconds: number) => {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSelectMcq = (questionId: string, optionId: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: optionId }));
  };

  const handleSelectTf = (questionId: string, stmtId: string, val: boolean) => {
    setAnswers((prev) => {
      const existing = prev[questionId] || {};
      return {
        ...prev,
        [questionId]: { ...existing, [stmtId]: val },
      };
    });
  };

  const handleTextChange = (questionId: string, val: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: val }));
  };

  const answeredCount = Object.keys(answers).filter((qid) => {
    const val = answers[qid];
    if (val === undefined || val === null || val === '') return false;
    if (typeof val === 'object' && Object.keys(val).length === 0) return false;
    return true;
  }).length;

  return (
    <div className="min-h-screen bg-canvas flex flex-col text-text-primary select-none">
      {/* Top Amber Sandbox Notification Banner (TC-4.5-01) */}
      <div className="bg-status-review-bg border-b border-status-review-border px-4 py-2 text-status-review-text flex items-center justify-between text-xs font-semibold shadow-xs">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-status-review-text shrink-0" />
          <span>
            CHẾ ĐỘ XEM TRƯỚC GIẢ LẬP (SANDBOX) — Đáp án chỉ lưu trên bộ nhớ RAM trình duyệt. Hoàn toàn không tạo lượt thi (attempt) và không khóa đề.
          </span>
        </div>
        <Link
          to={`/a/exams/${examId}/edit`}
          className="text-xs font-mono underline hover:brightness-125 ml-4 shrink-0"
        >
          Quay lại chỉnh sửa &rarr;
        </Link>
      </div>

      {/* Main Student Examination Header */}
      <header className="h-14 border-b border-border-subtle bg-surface px-4 lg:px-8 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <Link
            to={`/a/exams/${examId}/edit`}
            className="p-1.5 rounded-md hover:bg-surface-elevated text-text-secondary hover:text-text-primary transition-colors"
            title="Quay lại trình soạn đề"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="font-display font-bold text-sm text-text-primary line-clamp-1">
              {examData.title}
            </h1>
            <span className="text-[11px] font-mono text-text-muted">
              Môn {examData.subject.toUpperCase()} &bull; {questions.length} câu hỏi
            </span>
          </div>
        </div>

        {/* Monotonic Countdown Timer Box */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1 rounded-md bg-canvas border border-border-subtle font-mono text-xs">
            <Clock className="w-4 h-4 text-brand" />
            <span className="font-bold text-text-primary text-sm">{formatTimer(secondsRemaining)}</span>
          </div>

          <button
            onClick={() => setShowSubmitModal(true)}
            className="px-4 py-1.5 rounded-md bg-brand text-xs font-semibold text-text-on-brand hover:brightness-110 active:brightness-95 transition-all flex items-center gap-1.5 cursor-pointer"
          >
            <Send className="w-3.5 h-3.5" />
            <span>Nộp bài thử</span>
          </button>
        </div>
      </header>

      {/* 2-Column Student Test Taking Interface */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        {/* Left / Top: Question Palette Navigator */}
        <aside className="w-full lg:w-72 border-b lg:border-b-0 lg:border-r border-border-subtle bg-surface/50 p-4 shrink-0 flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold font-mono text-text-secondary uppercase">
              Danh sách câu hỏi
            </span>
            <span className="text-xs font-mono text-text-muted">
              {answeredCount}/{questions.length} đã làm
            </span>
          </div>

          {/* Palette Grid */}
          <div className="grid grid-cols-5 sm:grid-cols-8 lg:grid-cols-5 gap-2 overflow-y-auto max-h-48 lg:max-h-none flex-1">
            {questions.map((q, idx) => {
              const isAnswered =
                answers[q.id] !== undefined &&
                answers[q.id] !== null &&
                answers[q.id] !== '' &&
                Object.keys(answers[q.id] || {}).length > 0;
              const isActive = idx === activeQuestionIdx;

              return (
                <button
                  key={q.id}
                  onClick={() => setActiveQuestionIdx(idx)}
                  className={`h-9 rounded-md font-mono text-xs font-bold transition-all flex items-center justify-center cursor-pointer ${
                    isActive
                      ? 'border-2 border-brand text-text-primary ring-2 ring-brand/20 bg-surface'
                      : isAnswered
                      ? 'bg-brand/15 text-brand border border-brand/30'
                      : 'bg-canvas border border-border-subtle text-text-secondary hover:border-border-strong'
                  }`}
                >
                  {idx + 1}
                </button>
              );
            })}
          </div>

          {/* Legend */}
          <div className="pt-4 border-t border-border-subtle mt-4 flex items-center justify-around text-[11px] font-mono text-text-muted">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-brand/20 border border-brand/40" />
              <span>Đã làm</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-canvas border border-border-subtle" />
              <span>Chưa làm</span>
            </div>
          </div>
        </aside>

        {/* Right / Bottom: Current Question Card */}
        <main className="flex-1 p-6 lg:p-10 overflow-y-auto bg-canvas flex justify-center">
          {currentQuestion ? (
            <div className="w-full max-w-3xl space-y-6">
              {/* Question Header & Point Badge */}
              <div className="flex items-center justify-between pb-3 border-b border-border-subtle">
                <span className="font-display font-bold text-sm text-text-primary">
                  Câu {activeQuestionIdx + 1} trên {questions.length}
                </span>
                <span className="px-2.5 py-0.5 rounded-full bg-surface-elevated border border-border-subtle text-xs font-mono font-semibold text-text-secondary">
                  {currentQuestion.points} điểm
                </span>
              </div>

              {/* Question Content (Markdown + LaTeX) */}
              <div className="text-sm text-text-primary leading-relaxed">
                <MathText content={currentQuestion.content_md} />
              </div>

              {/* Interactive Student Answering Forms (No Answer Leakage) */}
              <div className="pt-4 border-t border-border-subtle space-y-4">
                {/* 1. MCQ */}
                {currentQuestion.type === 'mcq' && (
                  <div className="space-y-2.5">
                    {((currentQuestion.config?.options as any[]) || []).map((opt, idx) => {
                      const letter = String.fromCharCode(65 + idx);
                      const isSelected = answers[currentQuestion.id] === opt.id;

                      return (
                        <div
                          key={opt.id}
                          onClick={() => handleSelectMcq(currentQuestion.id, opt.id)}
                          className={`p-3.5 rounded-lg border flex items-start gap-3 cursor-pointer transition-all ${
                            isSelected
                              ? 'border-brand bg-brand/5 text-text-primary shadow-xs'
                              : 'border-border-subtle bg-surface hover:border-border-strong text-text-secondary'
                          }`}
                        >
                          <span
                            className={`w-6 h-6 rounded-full flex items-center justify-center font-mono text-xs font-bold shrink-0 transition-colors ${
                              isSelected
                                ? 'bg-brand text-text-on-brand'
                                : 'bg-surface-elevated text-text-muted border border-border-subtle'
                            }`}
                          >
                            {letter}
                          </span>
                          <div className="pt-0.5 text-xs text-text-primary flex-1">
                            <MathText content={opt.content_md} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* 2. TF (True/False Statements) */}
                {currentQuestion.type === 'tf' && (
                  <div className="space-y-3">
                    {((currentQuestion.config?.statements as any[]) || []).map((stmt, idx) => {
                      const letter = String.fromCharCode(97 + idx); // a, b, c, d
                      const currentVal = answers[currentQuestion.id]?.[stmt.id];

                      return (
                        <div
                          key={stmt.id}
                          className="p-3 rounded-lg border border-border-subtle bg-surface flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                        >
                          <div className="flex items-start gap-2.5 flex-1">
                            <span className="font-mono font-bold text-xs text-text-muted pt-0.5">
                              {letter})
                            </span>
                            <div className="text-xs text-text-primary">
                              <MathText content={stmt.statement || stmt.content_md} />
                            </div>
                          </div>

                          <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                            <button
                              type="button"
                              onClick={() => handleSelectTf(currentQuestion.id, stmt.id, true)}
                              className={`px-3 py-1 rounded text-xs font-semibold font-mono border transition-all cursor-pointer ${
                                currentVal === true
                                  ? 'bg-brand text-text-on-brand border-brand'
                                  : 'bg-canvas border-border-subtle text-text-secondary hover:border-border-strong'
                              }`}
                            >
                              Đúng
                            </button>
                            <button
                              type="button"
                              onClick={() => handleSelectTf(currentQuestion.id, stmt.id, false)}
                              className={`px-3 py-1 rounded text-xs font-semibold font-mono border transition-all cursor-pointer ${
                                currentVal === false
                                  ? 'bg-status-wrong-bg text-status-wrong-text border-status-wrong-border'
                                  : 'bg-canvas border-border-subtle text-text-secondary hover:border-border-strong'
                              }`}
                            >
                              Sai
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* 3. Short Text & 4. Short Number */}
                {(currentQuestion.type === 'short_text' || currentQuestion.type === 'short_number') && (
                  <div className="space-y-2">
                    <label className="block text-xs font-mono font-semibold text-text-secondary">
                      Nhập câu trả lời của bạn:
                    </label>
                    <input
                      type="text"
                      value={answers[currentQuestion.id] || ''}
                      onChange={(e) => handleTextChange(currentQuestion.id, e.target.value)}
                      placeholder={
                        currentQuestion.type === 'short_number'
                          ? 'Ví dụ: 12.5 hoặc -3/4...'
                          : 'Nhập từ/cụm từ trả lời...'
                      }
                      className="w-full h-10 px-3.5 rounded-lg border border-border-subtle bg-surface text-xs font-mono text-text-primary focus:border-brand focus:outline-none"
                    />
                  </div>
                )}

                {/* 5. File Upload */}
                {currentQuestion.type === 'file_upload' && (
                  <div className="p-6 rounded-lg border-2 border-dashed border-border-subtle bg-surface/50 text-center space-y-2">
                    <FileUp className="w-8 h-8 text-brand mx-auto" />
                    <p className="text-xs font-semibold text-text-primary">
                      Khu vực tải lên tệp bài làm
                    </p>
                    <p className="text-[11px] font-mono text-text-muted">
                      Hỗ trợ tối đa {currentQuestion.config?.max_files || 1} tệp ({currentQuestion.config?.max_mb || 5} MB).
                      Định dạng: {(currentQuestion.config?.allowed_ext || ['pdf']).join(', ')}.
                    </p>
                    <span className="inline-block mt-2 px-3 py-1 rounded text-[11px] font-mono text-text-muted bg-surface-elevated border border-border-subtle">
                      (Mô phỏng — Tệp không tải lên máy chủ trong chế độ xem trước)
                    </span>
                  </div>
                )}
              </div>

              {/* Prev / Next Navigation */}
              <div className="pt-6 border-t border-border-subtle flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => setActiveQuestionIdx((prev) => Math.max(0, prev - 1))}
                  disabled={activeQuestionIdx === 0}
                  className="px-4 py-2 rounded-md border border-border-subtle text-xs font-semibold text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors disabled:opacity-40 cursor-pointer"
                >
                  &larr; Câu trước
                </button>
                <button
                  type="button"
                  onClick={() => setActiveQuestionIdx((prev) => Math.min(questions.length - 1, prev + 1))}
                  disabled={activeQuestionIdx === questions.length - 1}
                  className="px-4 py-2 rounded-md border border-border-subtle text-xs font-semibold text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors disabled:opacity-40 cursor-pointer"
                >
                  Câu tiếp &rarr;
                </button>
              </div>
            </div>
          ) : (
            <div className="text-xs font-mono text-text-muted text-center py-12">
              Đề thi chưa có câu hỏi nào.
            </div>
          )}
        </main>
      </div>

      {/* Trial Submission Simulation Modal */}
      {showSubmitModal && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-overlay-scrim backdrop-blur-xs animate-in fade-in"
        >
          <div className="bg-surface rounded-xl border border-border-subtle shadow-xl w-full max-w-md p-5 space-y-4 animate-in zoom-in-95">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-brand" />
              <h3 className="font-display font-bold text-sm text-text-primary">
                Hoàn tất Bài làm Thử nghiệm
              </h3>
            </div>
            <p className="text-xs text-text-secondary leading-relaxed">
              Bạn đã trả lời được <strong className="font-mono text-text-primary">{answeredCount}</strong> /{' '}
              <strong className="font-mono text-text-primary">{questions.length}</strong> câu hỏi trong chế độ Sandbox.
            </p>
            <div className="p-3 rounded-lg border border-border-subtle bg-surface-elevated/30 text-xs font-mono text-text-muted space-y-1">
              <div>Thời gian làm bài: {formatTimer(examData.duration_minutes * 60 - secondsRemaining)}</div>
              <div>Ghi nhận vào cơ sở dữ liệu: <strong className="text-status-correct-text">Không (0 bytes)</strong></div>
            </div>
            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowSubmitModal(false)}
                className="px-3.5 py-1.5 rounded-md border border-border-subtle text-xs font-semibold text-text-secondary hover:bg-surface-elevated transition-colors"
              >
                Tiếp tục xem thử
              </button>
              <button
                type="button"
                onClick={() => navigate(`/a/exams/${examId}/edit`)}
                className="px-4 py-1.5 rounded-md bg-brand text-xs font-semibold text-text-on-brand hover:brightness-110 transition-colors"
              >
                Quay lại Soạn đề
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
