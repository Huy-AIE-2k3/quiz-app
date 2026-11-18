/**
 * Student Exam Introduction Detail Page (Step 5.1).
 *
 * Implements:
 * - Introduction view displaying title, subject, duration, question count, and total points.
 * - Safe MathText rendering of exam description markdown with asset URLs.
 * - Authoritative start eligibility button (can_start flag from server).
 * - 0% data leakage: never renders answers, internal scoring rules, or other students' data.
 */

import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  Calendar,
  CheckCircle2,
  Clock,
  FileQuestion,
  HelpCircle,
  PlayCircle,
  ShieldCheck,
  Trophy,
} from 'lucide-react';

import { useAuth } from '../../context/AuthContext';
import { studentApi, StudentExamDetail } from '../../lib/studentApi';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { ErrorState } from '../../components/ui/ErrorState';
import { MathText } from '../../components/ui/MathText';
import { Skeleton } from '../../components/ui/Skeleton';
import { useToast } from '../../components/ui/useToast';
import {
  formatDateTime,
  getStateBadgeConfig,
  getSubjectLabel,
} from '../../lib/studentExamUtils';

export const StudentExamDetailPage: React.FC = () => {
  const { examId } = useParams<{ examId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const {
    data: exam,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<StudentExamDetail, Error>({
    queryKey: ['student-exam-detail', examId],
    queryFn: () => {
      if (!examId) throw new Error('Mã đề thi không hợp lệ');
      return studentApi.getExam(examId);
    },
    enabled: Boolean(examId),
  });

  const startMutation = useMutation({
    mutationFn: () => {
      if (!examId) throw new Error('Mã đề thi không hợp lệ');
      return studentApi.startExam(examId);
    },
    onSuccess: (data) => {
      if (data.status === 'submitted') {
        toast.info('Bài thi này đã hoàn thành hoặc đã quá hạn.');
        queryClient.invalidateQueries({ queryKey: ['student-exam-detail', examId] });
      } else {
        navigate(`/s/exams/${examId}/take`);
      }
    },
    onError: (err: { message?: string }) => {
      toast.error(err?.message || 'Không thể bắt đầu làm bài thi.', 'Lỗi');
    },
  });

  return (
    <div className="min-h-screen bg-canvas text-text-primary">
      {/* Top Header */}
      <header className="border-b border-line-subtle bg-surface sticky top-0 z-20">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Button
              variant="outline"
              size="sm"
              iconLeft={<ArrowLeft className="w-4 h-4" />}
              onClick={() => navigate('/s/exams')}
            >
              Quay lại danh sách
            </Button>
          </div>

          <div className="flex items-center space-x-3">
            <span className="text-xs text-text-secondary font-mono hidden sm:inline">
              Thí sinh: {user?.full_name}
            </span>
            <Badge variant="neutral" size="sm">
              HỌC SINH
            </Badge>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        {isLoading ? (
          <div data-testid="detail-loading" className="space-y-6">
            <Skeleton width="100%" height="160px" />
            <Skeleton width="100%" height="240px" />
            <Skeleton width="100%" height="120px" />
          </div>
        ) : isError ? (
          <div data-testid="detail-error" className="py-12">
            <ErrorState
              title="Không tìm thấy bài thi"
              message={
                error?.message ||
                'Bài thi không tồn tại, chưa được giao cho lớp của bạn hoặc tạm thời không khả dụng.'
              }
              onRetry={() => refetch()}
            />
          </div>
        ) : !exam ? null : (
          <div className="space-y-6">
            {/* Exam Hero Card */}
            <Card className="p-6 sm:p-8 space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-text-muted uppercase tracking-wider">
                      {getSubjectLabel(exam.subject)}
                    </span>
                    <span className="text-text-muted text-xs">•</span>
                    <Badge
                      variant={getStateBadgeConfig(exam.state).variant}
                      dot={getStateBadgeConfig(exam.state).dot}
                      size="sm"
                    >
                      {getStateBadgeConfig(exam.state).label}
                    </Badge>
                  </div>

                  <h1 className="text-2xl sm:text-3xl font-display font-bold text-text-primary tracking-tight">
                    {exam.title}
                  </h1>
                </div>
              </div>

              {/* Specs Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-lg bg-elevated border border-line-subtle font-mono text-xs">
                <div className="space-y-1">
                  <div className="flex items-center gap-1.5 text-text-muted">
                    <Clock className="w-3.5 h-3.5" />
                    <span>Thời lượng</span>
                  </div>
                  <div className="font-semibold text-text-primary text-sm">
                    {exam.duration_minutes} phút
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="flex items-center gap-1.5 text-text-muted">
                    <FileQuestion className="w-3.5 h-3.5" />
                    <span>Số câu hỏi</span>
                  </div>
                  <div className="font-semibold text-text-primary text-sm">
                    {exam.question_count} câu
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="flex items-center gap-1.5 text-text-muted">
                    <Trophy className="w-3.5 h-3.5" />
                    <span>Tổng điểm</span>
                  </div>
                  <div className="font-semibold text-text-primary text-sm">
                    {exam.total_points} điểm
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="flex items-center gap-1.5 text-text-muted">
                    <Calendar className="w-3.5 h-3.5" />
                    <span>Thời gian mở</span>
                  </div>
                  <div className="font-semibold text-text-primary text-xs truncate">
                    {formatDateTime(exam.open_at)}
                  </div>
                </div>
              </div>

              {/* Close Time Notice */}
              {exam.close_at && (
                <div className="flex items-center gap-2 p-3 rounded bg-subtle-accent border border-line-accent text-xs text-brand font-mono">
                  <Calendar className="w-4 h-4 shrink-0" />
                  <span>Hạn chót đóng đề thi: {formatDateTime(exam.close_at)}</span>
                </div>
              )}
            </Card>

            {/* Description / Instructions */}
            <Card className="p-6 sm:p-8 space-y-4">
              <div className="flex items-center gap-2 text-text-primary font-display font-semibold text-base border-b border-line-subtle pb-3">
                <HelpCircle className="w-4 h-4 text-brand" />
                <h2>Hướng dẫn làm bài thi</h2>
              </div>

              {exam.description_md ? (
                <div className="prose prose-sm max-w-none text-text-secondary leading-relaxed">
                  <MathText content={exam.description_md} />
                </div>
              ) : (
                <p className="text-xs text-text-muted italic">
                  Không có hướng dẫn bổ sung cho đề thi này. Hãy đọc kỹ từng câu hỏi trước khi trả lời.
                </p>
              )}
            </Card>

            {/* Rules & Requirements */}
            <Card className="p-6 sm:p-8 space-y-4 bg-surface/50 border-line-subtle">
              <div className="flex items-center gap-2 text-text-primary font-display font-semibold text-base border-b border-line-subtle pb-3">
                <ShieldCheck className="w-4 h-4 text-brand" />
                <h2>Quy chế và Lưu ý phòng thi</h2>
              </div>

              <ul className="space-y-2 text-xs text-text-secondary">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-brand shrink-0 mt-0.5" />
                  <span>
                    <strong>Đồng hồ tính giờ:</strong> Thời gian làm bài sẽ bắt đầu đếm ngược ngay khi bạn bấm nút &quot;Bắt đầu làm bài&quot;.
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-brand shrink-0 mt-0.5" />
                  <span>
                    <strong>Tự động lưu bài:</strong> Hệ thống tự động ghi nhận câu trả lời sau mỗi thao tác. Trong trường hợp mất mạng hoặc vô tình đóng trình duyệt, đáp án đã chọn vẫn được bảo toàn.
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-brand shrink-0 mt-0.5" />
                  <span>
                    <strong>Thời hạn nộp bài:</strong> Khi hết thời gian làm bài, hệ thống sẽ tự động thu bài và khóa quyền chỉnh sửa câu trả lời.
                  </span>
                </li>
              </ul>
            </Card>

            {/* Bottom Action Section */}
            <Card className="p-6 flex flex-col sm:flex-row items-center justify-between gap-4 bg-elevated">
              <div className="text-center sm:text-left space-y-1">
                <div className="font-display font-semibold text-sm text-text-primary">
                  {exam.can_start
                    ? exam.state === 'in_progress'
                      ? 'Bạn đang có bài thi làm dở'
                      : 'Sẵn sàng làm bài thi?'
                    : exam.state === 'upcoming'
                    ? 'Bài thi chưa mở'
                    : exam.state === 'submitted'
                    ? 'Bài thi đã hoàn thành'
                    : 'Bài thi đã đóng'}
                </div>
                <div className="text-xs text-text-muted">
                  {exam.can_start
                    ? 'Hãy chắc chắn rằng bạn có không gian yên tĩnh và mạng internet ổn định.'
                    : exam.state === 'submitted'
                    ? 'Bạn đã nộp bài làm cho đề thi này. Kết quả sẽ được công bố theo kế hoạch của giáo viên.'
                    : 'Bài thi hiện không tiếp nhận thêm lượt làm mới.'}
                </div>
              </div>

              <div>
                {exam.can_start ? (
                  <Button
                    variant="primary"
                    size="lg"
                    className="w-full sm:w-auto px-8"
                    iconLeft={<PlayCircle className="w-5 h-5" />}
                    disabled={startMutation.isPending}
                    loading={startMutation.isPending}
                    onClick={() => startMutation.mutate()}
                  >
                    {exam.state === 'in_progress' ? 'Tiếp tục làm bài' : 'Bắt đầu làm bài'}
                  </Button>
                ) : exam.state === 'upcoming' ? (
                  <Button variant="outline" size="lg" disabled className="w-full sm:w-auto opacity-60">
                    Chưa mở đề thi
                  </Button>
                ) : exam.state === 'result_available' ? (
                  <Button
                    variant="outline"
                    size="lg"
                    className="w-full sm:w-auto"
                    onClick={() => navigate(`/s/exams/${exam.id}/result`)}
                  >
                    Xem kết quả bài thi
                  </Button>
                ) : (
                  <Button variant="outline" size="lg" disabled className="w-full sm:w-auto opacity-60">
                    {exam.state === 'submitted' ? 'Đã nộp bài' : 'Đã kết thúc'}
                  </Button>
                )}
              </div>
            </Card>
          </div>
        )}
      </main>
    </div>
  );
};
