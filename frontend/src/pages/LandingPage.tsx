/**
 * Public Landing Page (Guest accessible).
 *
 * Displays platform overview and sign-in call to action.
 * Strict Guest privacy: no system metrics or internal data exposed.
 */

import React from 'react';
import { Link, Navigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Card } from '../components/ui/Card';
import { useAuth } from '../context/AuthContext';
import { VI } from '../lib/i18n/vi';

export const LandingPage: React.FC = () => {
  const { isAuthenticated, role } = useAuth();

  // If already logged in, redirect to user's home
  if (isAuthenticated) {
    return <Navigate to={role === 'admin' ? '/a/classes' : '/s/exams'} replace />;
  }

  return (
    <div className="min-h-screen bg-canvas text-text-primary flex flex-col selection:bg-brand selection:text-white">
      {/* Header */}
      <header className="border-b border-line-subtle bg-surface/50 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="w-3.5 h-3.5 rounded-full bg-brand shadow-sm shadow-brand/50 inline-block" />
            <span className="text-xl font-bold font-display tracking-tight">Quiz Toán - Tin</span>
            <Badge variant="brand" size="sm">
              MATHRIX
            </Badge>
          </div>

          <nav className="flex items-center space-x-4">
            <Link to="/login">
              <Button variant="primary" size="sm">
                {VI.auth.signIn}
              </Button>
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col items-center justify-center p-6 text-center max-w-4xl mx-auto">
        <div className="space-y-6">
          <Badge variant="neutral" size="sm" className="px-3 py-1 font-mono">
            Hệ thống kiểm tra trực tuyến nội bộ dành cho học sinh Toán &amp; Tin học
          </Badge>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold font-display tracking-tight text-balance">
            Nền tảng Đánh giá Năng lực <br />
            <span className="text-brand">Toán học &amp; Tin học</span>
          </h1>

          <p className="max-w-2xl mx-auto text-base sm:text-lg text-text-secondary leading-relaxed font-sans">
            Thiết kế chuyên biệt cho học sinh với định dạng công thức LaTeX trực quan, chấm điểm tự
            động theo chuẩn THPT và cơ chế tự lưu bài làm an toàn chống gián đoạn mạng.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
            <Link to="/login">
              <Button size="lg" variant="primary" className="px-8 shadow-md">
                Bắt đầu làm bài &rarr;
              </Button>
            </Link>
            <Link to="/dev/components">
              <Button size="lg" variant="outline">
                Design System Preview
              </Button>
            </Link>
          </div>
        </div>

        {/* Feature Grid */}
        <section aria-label="Tính năng nổi bật" className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full mt-16 text-left">
          <Card className="p-6 space-y-3">
            <div className="text-brand font-mono text-sm font-semibold">01 / TOÁN &amp; TIN</div>
            <h2 className="font-bold text-base font-display">5 Dạng Câu Hỏi Toàn Diện</h2>
            <p className="text-xs text-text-secondary leading-relaxed">
              Trắc nghiệm 1 lựa chọn, Đúng/Sai theo chuẩn Bộ GD&amp;ĐT, Trả lời ngắn số/chữ, và Tải file
              mã nguồn bài làm.
            </p>
          </Card>

          <Card className="p-6 space-y-3">
            <div className="text-brand font-mono text-sm font-semibold">02 / CHỐNG RỦI RO</div>
            <h2 className="font-bold text-base font-display">Tự Lưu Bài Làm Tức Thì</h2>
            <p className="text-xs text-text-secondary leading-relaxed">
              Cơ chế hàng đợi lưu đệm (Outbox) trên trình duyệt đảm bảo bài làm không bị mất kể cả khi
              mạng Internet mất kết nối đột ngột.
            </p>
          </Card>

          <Card className="p-6 space-y-3">
            <div className="text-brand font-mono text-sm font-semibold">03 / CHUẨN XÁC</div>
            <h2 className="font-bold text-base font-display">Đồng Hồ Máy Chủ Độc Lập</h2>
            <p className="text-xs text-text-secondary leading-relaxed">
              Thời gian làm bài được đồng bộ theo máy chủ chuẩn (UTC), tự động nộp bài khi hết giờ mà
              không phụ thuộc giờ thiết bị học sinh.
            </p>
          </Card>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-line-subtle py-6 text-center text-xs text-text-muted">
        <p>&copy; 2026 Mathrix Quiz. Thiết kế &amp; vận hành nội bộ phục vụ học tập.</p>
      </footer>
    </div>
  );
};
