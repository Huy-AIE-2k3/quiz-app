/**
 * Student Active Exam Taking Page (Step 5.3 & Step 5.4).
 *
 * Implements:
 * - Load/resume exam attempt with deterministic question/option shuffling.
 * - Client-rendered A/B/C/D labels preserving opaque option IDs.
 * - Restores prior saved answers and client_seq.
 * - Auto-saving per question with client_seq serialization (Step 5.4).
 * - Remaining time countdown tracking.
 * - Multi-type question rendering: MCQ, TF, Short Text, Short Number.
 * - Corrupt question fault tolerance (unavailable: true displayed safely).
 * - Submitted state handling.
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Clock,
  AlertCircle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Send,
  Check,
  Loader2,
  WifiOff,
  AlertTriangle,
} from 'lucide-react';

import {
  studentApi,
  StudentAttemptDetail,
  StudentAttemptStatusResponse,
  StudentQuestionItem,
} from '../../lib/studentApi';
import { useMonotonicTimer } from '../../hooks/useMonotonicTimer';
import { useOfflineOutbox } from '../../hooks/useOfflineOutbox';
import { answerStore } from '../../lib/answerStore';
import { ReAuthModal } from '../../components/exam/ReAuthModal';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { ErrorState } from '../../components/ui/ErrorState';
import { MathText } from '../../components/ui/MathText';
import { Skeleton } from '../../components/ui/Skeleton';

export const StudentExamTakePage: React.FC = () => {
  const { examId } = useParams<{ examId: string }>();
  const location = useLocation();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState<StudentAttemptDetail | null>(null);
  const [activeQuestionIdx, setActiveQuestionIdx] = useState(0);
  const [isReAuthOpen, setIsReAuthOpen] = useState(false);

  // Local answers state mapped by question_id: { value, client_seq }
  const [localAnswers, setLocalAnswers] = useState<
    Record<string, { value: Record<string, unknown>; client_seq: number }>
  >({});

  const isSubmitted = attempt?.status === 'submitted';

  const handleTimeUp = useCallback(() => {
    setAttempt((prev) => (prev ? { ...prev, status: 'submitted' } : null));
  }, []);

  const handleStatusSync = useCallback((statusData: StudentAttemptStatusResponse) => {
    if (statusData.status === 'submitted') {
      setAttempt((prev) => (prev ? { ...prev, status: 'submitted' } : null));
    }
  }, []);

  const { secondsRemaining, formatTimer } = useMonotonicTimer({
    attemptId: attempt?.id,
    initialRemainingSeconds: attempt?.remaining_seconds || 0,
    isSubmitted,
    onTimeUp: handleTimeUp,
    onStatusSync: handleStatusSync,
  });

  const {
    outboxCount,
    isOnline,
    isStorageFallback,
    saveStatusMap,
    saveAnswerOptimistic,
    manualRetrySync,
    resumeAfterAuth,
  } = useOfflineOutbox({
    attemptId: attempt?.id,
    isSubmitted,
    onReAuthRequired: () => setIsReAuthOpen(true),
    onAttemptClosed: () => {
      setAttempt((prev) => (prev ? { ...prev, status: 'submitted' } : null));
    },
  });

  // Fetch or resolve attempt
  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    const loadAttemptData = async () => {
      try {
        let targetAttemptId = (location.state as { attemptId?: string } | undefined)?.attemptId;

        if (!targetAttemptId && examId) {
          const examDetail = await studentApi.getExam(examId);
          if (examDetail.attempt_id) {
            targetAttemptId = examDetail.attempt_id;
          } else {
            const startRes = await studentApi.startExam(examId);
            targetAttemptId = startRes.id;
          }
        }

        if (!targetAttemptId) {
          throw new Error('Không tìm thấy lượt làm bài thi.');
        }

        const data = await studentApi.getAttempt(targetAttemptId);
        if (!isMounted) return;

        setAttempt(data);

        // Restore saved answers from attempt
        const restored: Record<string, { value: Record<string, unknown>; client_seq: number }> = {};
        for (const [qId, ans] of Object.entries(data.answers || {})) {
          restored[qId] = {
            value: ans.value || {},
            client_seq: ans.client_seq || 0,
          };
        }

        // Merge any answers pending in local outbox (TC-5.6-03: F5/reload offline preserves answers)
        const offlineItems = answerStore.getOutbox(targetAttemptId);
        for (const item of offlineItems) {
          if (!restored[item.questionId] || item.client_seq >= (restored[item.questionId]?.client_seq || 0)) {
            restored[item.questionId] = {
              value: item.value,
              client_seq: item.client_seq,
            };
          }
        }

        setLocalAnswers(restored);
      } catch (err: unknown) {
        if (!isMounted) return;
        const msg = err instanceof Error ? err.message : 'Không thể tải nội dung bài thi.';
        setError(msg);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    void loadAttemptData();

    return () => {
      isMounted = false;
    };
  }, [examId, location.state]);

  const questions = useMemo(() => attempt?.questions || [], [attempt?.questions]);
  const currentQuestion: StudentQuestionItem | undefined = questions[activeQuestionIdx];

  const answeredCount = useMemo(() => {
    return Object.values(localAnswers).filter(
      (ans) => ans.value && Object.keys(ans.value).length > 0
    ).length;
  }, [localAnswers]);

  // Handle saving an answer via Offline Outbox (Step 5.6)
  const handleSaveAnswer = (questionId: string, value: Record<string, unknown>) => {
    if (!attempt || attempt.status === 'submitted') return;

    const nextSeq = (localAnswers[questionId]?.client_seq || 0) + 1;
    setLocalAnswers((prev) => ({
      ...prev,
      [questionId]: {
        value,
        client_seq: nextSeq,
      },
    }));

    saveAnswerOptimistic(questionId, value, nextSeq);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-canvas text-text-primary p-6">
        <div className="max-w-5xl mx-auto space-y-6">
          <Skeleton width="100%" height="60px" />
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="md:col-span-3 space-y-4">
              <Skeleton width="100%" height="280px" />
              <Skeleton width="100%" height="180px" />
            </div>
            <div className="md:col-span-1">
              <Skeleton width="100%" height="320px" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !attempt) {
    return (
      <div className="min-h-screen bg-canvas text-text-primary p-6">
        <div className="max-w-2xl mx-auto pt-16">
          <ErrorState
            title="Lỗi tải bài làm"
            message={error || 'Không tìm thấy thông tin lượt làm bài.'}
            onRetry={() => navigate('/s/exams')}
          />
        </div>
      </div>
    );
  }

  const currentSaveStatus = currentQuestion ? saveStatusMap[currentQuestion.id] : undefined;

  return (
    <div className="min-h-screen bg-canvas text-text-primary flex flex-col">
      {/* ================= OFFLINE ALERT BANNER (SC-04-VAR-OFFLINE) ================= */}
      {(!isOnline || outboxCount > 0) && (
        <div
          role="status"
          className="w-full bg-status-wrong-bg border-b border-status-wrong-border px-4 sm:px-6 py-2.5 flex flex-wrap items-center justify-between text-xs text-status-wrong-text font-medium gap-2"
        >
          <div className="flex items-center gap-2">
            <WifiOff className="w-4 h-4 shrink-0" />
            <span>
              {!isOnline
                ? 'MẤT KẾT NỐI MẠNG - Đáp án đang được lưu an toàn trong máy. Vui lòng không tải lại trang!'
                : 'Đang kết nối lại - Có đáp án chưa đồng bộ với máy chủ.'}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 font-mono text-[11px]">
              <span className="w-2 h-2 rounded-full bg-status-wrong-border animate-ping shrink-0" />
              <span>Outbox: {outboxCount} câu chờ gửi</span>
            </div>
            <button
              type="button"
              onClick={manualRetrySync}
              className="underline hover:text-text-primary transition-colors cursor-pointer"
            >
              Thử đồng bộ lại ngay
            </button>
          </div>
        </div>
      )}

      {/* ================= STORAGE FALLBACK WARNING BANNER (TC-5.6-06) ================= */}
      {isStorageFallback && (
        <div
          role="alert"
          className="w-full bg-status-flag-bg border-b border-status-flag-border px-4 sm:px-6 py-2 flex items-center justify-between text-xs text-status-flag-text font-medium"
        >
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>
              Cảnh báo: Bộ nhớ trình duyệt bị hạn chế hoặc đã đầy. Bài thi đang được lưu tạm trên RAM. Vui lòng không tải lại trang hoặc đóng trình duyệt!
            </span>
          </div>
        </div>
      )}

      {/* Top Navbar */}
      <header className="sticky top-0 z-30 bg-surface border-b border-line-subtle px-4 sm:px-6 h-16 flex items-center justify-between shadow-xs">
        <div className="flex items-center space-x-3 overflow-hidden">
          <Button
            variant="ghost"
            size="sm"
            iconLeft={<ArrowLeft className="w-4 h-4" />}
            onClick={() => navigate('/s/exams')}
            className="shrink-0"
          >
            Quay lại
          </Button>
          <div className="truncate">
            <h1 className="text-sm sm:text-base font-display font-bold text-text-primary truncate">
              {attempt.exam_title}
            </h1>
          </div>
        </div>

        <div className="flex items-center space-x-4 shrink-0 font-mono">
          {/* Countdown Clock */}
          <div
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border font-bold text-sm ${
              isSubmitted
                ? 'bg-elevated border-line-subtle text-text-muted'
                : secondsRemaining < 300
                ? 'bg-status-wrong-bg border-status-wrong-border text-status-wrong-text animate-pulse'
                : 'bg-subtle-accent border-line-accent text-brand'
            }`}
          >
            <Clock className="w-4 h-4" />
            <span>{isSubmitted ? 'Đã thu bài' : formatTimer(secondsRemaining)}</span>
          </div>

          <Badge variant={isSubmitted ? 'neutral' : 'brand'} size="sm">
            {isSubmitted ? 'ĐÃ NỘP' : 'ĐANG THI'}
          </Badge>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Column: Active Question */}
        <main className="lg:col-span-3 space-y-6">
          {isSubmitted && (
            <Card className="p-4 bg-status-info-bg border-status-info-border text-status-info-text text-sm flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 shrink-0" />
              <span>
                Bài thi này đã hoàn thành hoặc hết thời gian làm bài. Toàn bộ đáp án đã được hệ thống ghi nhận.
              </span>
            </Card>
          )}

          {currentQuestion ? (
            <Card className="p-6 sm:p-8 space-y-6">
              {/* Question Header */}
              <div className="flex items-center justify-between border-b border-line-subtle pb-4">
                <div className="flex items-center space-x-3">
                  <span className="text-base sm:text-lg font-display font-bold text-brand">
                    Câu {activeQuestionIdx + 1}
                  </span>
                  <span className="text-xs text-text-muted">/ {questions.length} câu</span>
                  {currentQuestion.unavailable && (
                    <Badge variant="danger" size="sm">
                      KHÔNG KHẢ DỤNG
                    </Badge>
                  )}
                </div>

                <div className="flex items-center space-x-3">
                  {currentSaveStatus === 'saving' && (
                    <span className="text-xs text-text-muted flex items-center gap-1 font-mono">
                      <Loader2 className="w-3.5 h-3.5 animate-spin" /> Đang lưu...
                    </span>
                  )}
                  {currentSaveStatus === 'saved' && (
                    <span className="text-xs text-brand flex items-center gap-1 font-mono">
                      <Check className="w-3.5 h-3.5" /> Đã lưu
                    </span>
                  )}
                  {currentSaveStatus === 'pending' && (
                    <span className="text-xs text-status-flag-text flex items-center gap-1 font-mono">
                      <Clock className="w-3.5 h-3.5" /> Chưa lưu (ngoại tuyến)
                    </span>
                  )}
                  {currentSaveStatus === 'error' && (
                    <span className="text-xs text-status-wrong-text flex items-center gap-1 font-mono">
                      <AlertCircle className="w-3.5 h-3.5" /> Chưa lưu được
                    </span>
                  )}
                  <div className="text-xs font-mono text-text-secondary">
                    {currentQuestion.points} điểm
                  </div>
                </div>
              </div>

              {/* Question Content */}
              {currentQuestion.unavailable ? (
                <div className="p-4 rounded-lg bg-status-wrong-bg border border-status-wrong-border text-status-wrong-text text-sm flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
                  <div>
                    <strong className="font-semibold block mb-1">Câu hỏi tạm thời không khả dụng</strong>
                    Dữ liệu câu hỏi này gặp sự cố trong hệ thống. Câu hỏi này sẽ được tự động bỏ qua và không ảnh hưởng đến quyền lợi của bạn.
                  </div>
                </div>
              ) : (
                <div className="prose prose-sm sm:prose max-w-none text-text-primary">
                  <MathText content={currentQuestion.content_md} />
                </div>
              )}

              {/* 1. MCQ (Single Choice) */}
              {!currentQuestion.unavailable && currentQuestion.type === 'mcq' && (
                <div className="space-y-3 pt-2">
                  {((currentQuestion.config?.options as Array<{ id: string; content_md: string }>) || []).map(
                    (opt, idx) => {
                      const labelLetter = String.fromCharCode(65 + idx);
                      const isSelected =
                        localAnswers[currentQuestion.id]?.value?.selected === opt.id;

                      return (
                        <div
                          key={opt.id}
                          data-testid={`option-${opt.id}`}
                          onClick={() => {
                            if (isSubmitted) return;
                            void handleSaveAnswer(currentQuestion.id, { selected: opt.id });
                          }}
                          className={`p-4 rounded-lg border flex items-start space-x-3 cursor-pointer transition-colors ${
                            isSelected
                              ? 'bg-subtle-accent border-line-accent shadow-xs'
                              : 'bg-surface border-line-subtle hover:bg-elevated'
                          } ${isSubmitted ? 'cursor-not-allowed opacity-80' : ''}`}
                        >
                          <div
                            className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs font-mono shrink-0 transition-colors ${
                              isSelected
                                ? 'bg-brand text-canvas'
                                : 'bg-elevated text-text-secondary border border-line-subtle'
                            }`}
                          >
                            {labelLetter}
                          </div>
                          <div className="flex-1 text-sm text-text-primary pt-0.5">
                            <MathText content={opt.content_md} />
                          </div>
                        </div>
                      );
                    }
                  )}
                </div>
              )}

              {/* 2. TF (True/False Statements) */}
              {!currentQuestion.unavailable && currentQuestion.type === 'tf' && (
                <div className="space-y-3 pt-2">
                  {((currentQuestion.config?.statements as Array<{ id: string; content_md: string }>) || []).map(
                    (stmt, idx) => {
                      const labelLetter = String.fromCharCode(97 + idx);
                      const currentStmts =
                        (localAnswers[currentQuestion.id]?.value?.statements as Record<string, boolean>) ||
                        (localAnswers[currentQuestion.id]?.value as Record<string, boolean>) ||
                        {};
                      const val = currentStmts[stmt.id];

                      return (
                        <div
                          key={stmt.id}
                          className="p-4 rounded-lg border border-line-subtle bg-surface flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                        >
                          <div className="flex items-start gap-3 flex-1">
                            <span className="font-mono font-bold text-xs text-text-muted pt-0.5">
                              {labelLetter})
                            </span>
                            <div className="text-sm text-text-primary">
                              <MathText content={stmt.content_md} />
                            </div>
                          </div>

                          <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                            <button
                              type="button"
                              disabled={isSubmitted}
                              onClick={() => {
                                if (isSubmitted) return;
                                void handleSaveAnswer(currentQuestion.id, {
                                  statements: { ...currentStmts, [stmt.id]: true },
                                });
                              }}
                              className={`px-3 py-1.5 rounded text-xs font-semibold font-mono border transition-all cursor-pointer ${
                                val === true
                                  ? 'bg-brand text-canvas border-brand'
                                  : 'bg-canvas border-line-subtle text-text-secondary hover:bg-elevated'
                              } ${isSubmitted ? 'cursor-not-allowed opacity-80' : ''}`}
                            >
                              Đúng
                            </button>
                            <button
                              type="button"
                              disabled={isSubmitted}
                              onClick={() => {
                                if (isSubmitted) return;
                                void handleSaveAnswer(currentQuestion.id, {
                                  statements: { ...currentStmts, [stmt.id]: false },
                                });
                              }}
                              className={`px-3 py-1.5 rounded text-xs font-semibold font-mono border transition-all cursor-pointer ${
                                val === false
                                  ? 'bg-status-wrong-bg text-status-wrong-text border-status-wrong-border'
                                  : 'bg-canvas border-line-subtle text-text-secondary hover:bg-elevated'
                              } ${isSubmitted ? 'cursor-not-allowed opacity-80' : ''}`}
                            >
                              Sai
                            </button>
                          </div>
                        </div>
                      );
                    }
                  )}
                </div>
              )}

              {/* 3. Short Text and Short Number */}
              {!currentQuestion.unavailable &&
                (currentQuestion.type === 'short_text' || currentQuestion.type === 'short_number') && (
                  <div className="space-y-3 pt-2">
                    <label className="block text-xs font-mono font-semibold text-text-secondary">
                      Nhập câu trả lời của bạn:
                    </label>
                    <input
                      type="text"
                      disabled={isSubmitted}
                      value={
                        String(
                          localAnswers[currentQuestion.id]?.value?.value ??
                          localAnswers[currentQuestion.id]?.value?.text ??
                          ''
                        )
                      }
                      onChange={(e) => {
                        const val = e.target.value;
                        setLocalAnswers((prev) => ({
                          ...prev,
                          [currentQuestion.id]: {
                            value: currentQuestion.type === 'short_text' ? { text: val } : { value: val },
                            client_seq: prev[currentQuestion.id]?.client_seq || 0,
                          },
                        }));
                      }}
                      onBlur={(e) => {
                        if (isSubmitted) return;
                        const val = e.target.value;
                        void handleSaveAnswer(
                          currentQuestion.id,
                          currentQuestion.type === 'short_text' ? { text: val } : { value: val }
                        );
                      }}
                      placeholder={
                        currentQuestion.type === 'short_number'
                          ? 'Nhập giá trị số (vd: 3.14 hoặc 1/2)...'
                          : 'Nhập câu trả lời...'
                      }
                      className="w-full px-3 py-2 rounded-lg bg-surface border border-line-subtle text-text-primary text-sm focus:outline-hidden focus:border-brand font-mono"
                    />
                  </div>
                )}

              {/* Navigation buttons */}
              <div className="flex items-center justify-between pt-6 border-t border-line-subtle">
                <Button
                  variant="outline"
                  size="sm"
                  iconLeft={<ChevronLeft className="w-4 h-4" />}
                  disabled={activeQuestionIdx === 0}
                  onClick={() => setActiveQuestionIdx((prev) => Math.max(0, prev - 1))}
                >
                  Câu trước
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  iconRight={<ChevronRight className="w-4 h-4" />}
                  disabled={activeQuestionIdx === questions.length - 1}
                  onClick={() =>
                    setActiveQuestionIdx((prev) => Math.min(questions.length - 1, prev + 1))
                  }
                >
                  Câu tiếp theo
                </Button>
              </div>
            </Card>
          ) : null}
        </main>

        {/* Right Column: Palette Navigation */}
        <aside className="lg:col-span-1 space-y-4">
          <Card className="p-4 sm:p-5 space-y-4 sticky top-20">
            <div className="flex items-center justify-between border-b border-line-subtle pb-3">
              <span className="font-display font-semibold text-sm text-text-primary">
                Bảng câu hỏi
              </span>
              <span className="text-xs text-text-muted font-mono">
                {answeredCount}/{questions.length} đã chọn
              </span>
            </div>

            {/* Grid of Question Numbers */}
            <div className="grid grid-cols-5 gap-2">
              {questions.map((q, idx) => {
                const isCurrent = idx === activeQuestionIdx;
                const isAnswered = Boolean(
                  localAnswers[q.id]?.value && Object.keys(localAnswers[q.id]?.value).length > 0
                );

                return (
                  <button
                    key={q.id}
                    onClick={() => setActiveQuestionIdx(idx)}
                    className={`h-9 rounded font-mono text-xs font-semibold transition-all cursor-pointer ${
                      isCurrent
                        ? 'ring-2 ring-brand ring-offset-2 ring-offset-canvas'
                        : ''
                    } ${
                      isAnswered
                        ? 'bg-brand text-canvas font-bold'
                        : 'bg-elevated text-text-secondary hover:bg-elevated/80 border border-line-subtle'
                    }`}
                  >
                    {idx + 1}
                  </button>
                );
              })}
            </div>

            {/* Bottom Actions */}
            <div className="pt-4 border-t border-line-subtle space-y-2">
              {!isSubmitted ? (
                <Button
                  variant="primary"
                  size="sm"
                  className="w-full"
                  iconLeft={<Send className="w-4 h-4" />}
                  onClick={() => {
                    alert('Chức năng nộp bài chính thức sẽ kích hoạt ở Bước 5.7.');
                  }}
                >
                  Nộp bài thi
                </Button>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full"
                  onClick={() => navigate('/s/exams')}
                >
                  Quay lại danh sách
                </Button>
              )}
            </div>
          </Card>
        </aside>
      </div>

      {/* In-place Re-authentication Modal (Step 5.6 / TC-5.6-04) */}
      <ReAuthModal
        isOpen={isReAuthOpen}
        username={attempt?.student_name}
        onSuccess={() => {
          setIsReAuthOpen(false);
          resumeAfterAuth();
        }}
      />
    </div>
  );
};
