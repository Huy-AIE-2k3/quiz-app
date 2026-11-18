/**
 * Student Active Exam Taking Page (Step 5.3).
 *
 * Implements:
 * - Load/resume exam attempt with deterministic question/option shuffling.
 * - Client-rendered A/B/C/D labels preserving opaque option IDs.
 * - Restores prior saved answers and client_seq.
 * - Remaining time countdown tracking.
 * - Corrupt question fault tolerance (unavailable: true displayed safely).
 * - Submitted state handling.
 */

import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Clock,
  AlertCircle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Send,
} from 'lucide-react';

import { studentApi, StudentAttemptDetail, StudentQuestionItem } from '../../lib/studentApi';
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

  // Local answers state mapped by question_id: { value, client_seq }
  const [localAnswers, setLocalAnswers] = useState<
    Record<string, { value: Record<string, unknown>; client_seq: number }>
  >({});
  const [secondsRemaining, setSecondsRemaining] = useState<number>(0);

  // Fetch or resolve attempt
  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    const loadAttemptData = async () => {
      try {
        let targetAttemptId = (location.state as { attemptId?: string } | undefined)?.attemptId;

        if (!targetAttemptId && examId) {
          // Look up attempt_id from exam detail
          const examDetail = await studentApi.getExam(examId);
          if (examDetail.attempt_id) {
            targetAttemptId = examDetail.attempt_id;
          } else {
            // Start attempt if not started yet
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
        setSecondsRemaining(data.remaining_seconds);

        // Restore saved answers from attempt
        const restored: Record<string, { value: Record<string, unknown>; client_seq: number }> = {};
        for (const [qId, ans] of Object.entries(data.answers || {})) {
          restored[qId] = {
            value: ans.value || {},
            client_seq: ans.client_seq || 0,
          };
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

  // Countdown timer
  useEffect(() => {
    if (secondsRemaining <= 0 || attempt?.status === 'submitted') return;

    const timer = setInterval(() => {
      setSecondsRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [secondsRemaining, attempt?.status]);

  const questions = useMemo(() => attempt?.questions || [], [attempt?.questions]);
  const currentQuestion: StudentQuestionItem | undefined = questions[activeQuestionIdx];

  const formatTimer = (totalSeconds: number) => {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const answeredCount = useMemo(() => {
    return Object.keys(localAnswers).length;
  }, [localAnswers]);

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

  const isSubmitted = attempt.status === 'submitted';

  return (
    <div className="min-h-screen bg-canvas text-text-primary flex flex-col">
      {/* Top Navbar */}
      <header className="sticky top-0 z-30 bg-surface border-b border-line-subtle px-4 sm:px-6 h-16 flex items-center justify-between shadow-sm">
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
                <div className="text-xs font-mono text-text-secondary">
                  {currentQuestion.points} điểm
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

              {/* Question Options / Answer area */}
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
                          onClick={() => {
                            if (isSubmitted) return;
                            setLocalAnswers((prev) => ({
                              ...prev,
                              [currentQuestion.id]: {
                                value: { selected: opt.id },
                                client_seq: (prev[currentQuestion.id]?.client_seq || 0) + 1,
                              },
                            }));
                          }}
                          className={`p-4 rounded-lg border flex items-start space-x-3 cursor-pointer transition-colors ${
                            isSelected
                              ? 'bg-subtle-accent border-line-accent shadow-sm'
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
                const isAnswered = Boolean(localAnswers[q.id]?.value);

                return (
                  <button
                    key={q.id}
                    onClick={() => setActiveQuestionIdx(idx)}
                    className={`h-9 rounded font-mono text-xs font-semibold transition-all ${
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
                    alert('Chức năng nộp bài chính thức sẽ kích hoạt ở Bước 5.8.');
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
    </div>
  );
};
