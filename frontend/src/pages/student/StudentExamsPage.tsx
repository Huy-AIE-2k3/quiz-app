/**
 * Student Exams Catalog Page (Step 5.1).
 *
 * Implements:
 * - Dynamic real-time state badge (upcoming, open, in_progress, submitted, result_available, closed).
 * - Categorized filter tabs (Tất cả, Đang mở / Đang làm, Đã nộp, Khác).
 * - Retryable ErrorState on transient failure (never false empty list).
 * - Safe allow-list presentation: zero score or answer key leakage.
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  BookOpen,
  Calendar,
  Clock,
  FileText,
  LogOut,
  PlayCircle,
  RotateCcw,
} from 'lucide-react';

import { useAuth } from '../../context/AuthContext';
import { studentApi, StudentExamListItem } from '../../lib/studentApi';
import {
  formatDateTime,
  getStateBadgeConfig,
  getSubjectLabel,
} from '../../lib/studentExamUtils';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorState } from '../../components/ui/ErrorState';
import { Skeleton } from '../../components/ui/Skeleton';
import { Tabs, TabList, TabTrigger } from '../../components/ui/Tabs';

type FilterTab = 'all' | 'active' | 'submitted' | 'other';

export const StudentExamsPage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<FilterTab>('all');

  const {
    data: exams,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useQuery<StudentExamListItem[], Error>({
    queryKey: ['student-exams'],
    queryFn: studentApi.listExams,
    staleTime: 10 * 1000,
  });

  const filteredExams = React.useMemo(() => {
    if (!exams) return [];
    if (activeTab === 'all') return exams;
    if (activeTab === 'active') {
      return exams.filter((e) => e.state === 'open' || e.state === 'in_progress');
    }
    if (activeTab === 'submitted') {
      return exams.filter((e) => e.state === 'submitted' || e.state === 'result_available');
    }
    if (activeTab === 'other') {
      return exams.filter((e) => e.state === 'upcoming' || e.state === 'closed');
    }
    return exams;
  }, [exams, activeTab]);

  return (
    <div className="min-h-screen bg-canvas text-text-primary">
      {/* Top Navigation Bar */}
      <header className="border-b border-line-subtle bg-surface sticky top-0 z-20">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="w-2.5 h-2.5 rounded-full bg-brand animate-pulse" />
            <span className="font-display font-bold text-lg tracking-tight">MATHRIX</span>
            <span className="text-text-muted text-xs font-mono">/</span>
            <span className="text-xs font-medium text-text-secondary">Cổng thi trực tuyến</span>
          </div>

          <div className="flex items-center space-x-4">
            <div className="hidden sm:flex items-center space-x-2 text-right">
              <span className="text-xs font-medium text-text-primary">{user?.full_name}</span>
              <Badge variant="neutral" size="sm">
                HỌC SINH
              </Badge>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => logout()}
              iconLeft={<LogOut className="w-3.5 h-3.5" />}
              title="Đăng xuất"
            >
              <span className="hidden sm:inline">Đăng xuất</span>
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        {/* Page Hero Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold font-display tracking-tight text-text-primary">
              Danh Sách Bài Thi
            </h1>
            <p className="text-xs text-text-secondary mt-1">
              Xem danh sách các đề thi được giao cho lớp học của bạn và vào phòng thi.
            </p>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
            iconLeft={<RotateCcw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin' : ''}`} />}
          >
            Làm mới
          </Button>
        </div>

        {/* Filter Tabs */}
        <Tabs defaultValue="all" value={activeTab} onValueChange={(val) => setActiveTab(val as FilterTab)}>
          <TabList ariaLabel="Bộ lọc đề thi">
            <TabTrigger value="all">Tất cả</TabTrigger>
            <TabTrigger value="active">Đang mở / Đang làm</TabTrigger>
            <TabTrigger value="submitted">Đã nộp bài</TabTrigger>
            <TabTrigger value="other">Khác</TabTrigger>
          </TabList>
        </Tabs>

        {/* Content Area: Loading / Error / Empty / Grid */}
        {isLoading ? (
          <div
            data-testid="exams-loading"
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <Card key={i} className="p-5 space-y-4">
                <div className="flex justify-between items-center">
                  <Skeleton width="60px" height="18px" />
                  <Skeleton width="75px" height="18px" />
                </div>
                <Skeleton width="85%" height="22px" />
                <div className="space-y-2 pt-2">
                  <Skeleton width="60%" height="14px" />
                  <Skeleton width="45%" height="14px" />
                </div>
                <div className="pt-4 border-t border-line-subtle">
                  <Skeleton width="100%" height="36px" />
                </div>
              </Card>
            ))}
          </div>
        ) : isError ? (
          <div data-testid="exams-error" className="py-12">
            <ErrorState
              title="Không thể tải danh sách bài thi"
              message={
                error?.message ||
                'Dịch vụ cơ sở dữ liệu tạm thời gián đoạn. Vui lòng thử lại sau giây lát.'
              }
              onRetry={() => refetch()}
            />
          </div>
        ) : filteredExams.length === 0 ? (
          <div data-testid="exams-empty" className="py-12">
            <EmptyState
              icon={<BookOpen className="w-8 h-8" />}
              title="Chưa có bài thi nào"
              description={
                activeTab === 'all'
                  ? 'Hiện chưa có bài thi nào được giao cho các lớp bạn tham gia.'
                  : 'Không có bài thi nào phù hợp với bộ lọc đã chọn.'
              }
            />
          </div>
        ) : (
          <div
            data-testid="exams-grid"
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            {filteredExams.map((exam) => {
              const badge = getStateBadgeConfig(exam.state);
              const subjectText = getSubjectLabel(exam.subject);

              return (
                <Card
                  key={exam.id}
                  data-testid={`exam-card-${exam.id}`}
                  className="flex flex-col justify-between p-5 hover:border-line-strong transition-all duration-200"
                >
                  <div className="space-y-3">
                    {/* Header: Subject + State Badge */}
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[11px] font-mono text-text-muted uppercase tracking-wider">
                        {subjectText}
                      </span>
                      <Badge variant={badge.variant} dot={badge.dot} size="sm">
                        {badge.label}
                      </Badge>
                    </div>

                    {/* Title */}
                    <h3 className="font-display font-semibold text-base text-text-primary line-clamp-2">
                      {exam.title}
                    </h3>

                    {/* Meta info */}
                    <div className="space-y-1.5 pt-1 text-xs text-text-secondary font-mono">
                      <div className="flex items-center gap-2">
                        <Clock className="w-3.5 h-3.5 text-text-muted shrink-0" />
                        <span>{exam.duration_minutes} phút</span>
                        <span className="text-text-muted">•</span>
                        <FileText className="w-3.5 h-3.5 text-text-muted shrink-0" />
                        <span>{exam.question_count} câu hỏi</span>
                      </div>

                      {exam.open_at && (
                        <div className="flex items-center gap-2 text-[11px] text-text-muted">
                          <Calendar className="w-3.5 h-3.5 shrink-0" />
                          <span>Mở: {formatDateTime(exam.open_at)}</span>
                        </div>
                      )}

                      {exam.close_at && (
                        <div className="flex items-center gap-2 text-[11px] text-text-muted">
                          <Calendar className="w-3.5 h-3.5 shrink-0" />
                          <span>Đóng: {formatDateTime(exam.close_at)}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Actions Footer */}
                  <div className="pt-5 mt-4 border-t border-line-subtle">
                    {exam.state === 'in_progress' ? (
                      <Button
                        variant="primary"
                        size="sm"
                        className="w-full"
                        iconLeft={<PlayCircle className="w-4 h-4" />}
                        onClick={() => navigate(`/s/exams/${exam.id}`)}
                      >
                        Tiếp tục làm bài
                      </Button>
                    ) : exam.state === 'open' ? (
                      <Button
                        variant="primary"
                        size="sm"
                        className="w-full"
                        iconLeft={<PlayCircle className="w-4 h-4" />}
                        onClick={() => navigate(`/s/exams/${exam.id}`)}
                      >
                        Vào làm bài
                      </Button>
                    ) : exam.state === 'upcoming' ? (
                      <Button variant="outline" size="sm" className="w-full opacity-60" disabled>
                        Chưa mở đề thi
                      </Button>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full"
                        onClick={() => navigate(`/s/exams/${exam.id}`)}
                      >
                        Xem thông tin đề
                      </Button>
                    )}
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
};
