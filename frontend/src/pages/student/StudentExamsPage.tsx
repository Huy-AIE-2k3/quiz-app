/**
 * Student Exams Dashboard Placeholder (Route /s/exams).
 */

import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Card } from '../../components/ui/Card';

export const StudentExamsPage: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-canvas text-text-primary p-6">
      <header className="max-w-6xl mx-auto flex items-center justify-between pb-6 border-b border-line-subtle">
        <div className="flex items-center space-x-3">
          <span className="w-3 h-3 rounded-full bg-blue-500 inline-block" />
          <h1 className="text-xl font-bold font-display">Danh Sách Đề Thi — Học Sinh</h1>
          <Badge variant="neutral" size="sm">
            HỌC SINH
          </Badge>
        </div>

        <div className="flex items-center space-x-4">
          <span className="text-xs text-text-secondary font-mono">{user?.full_name}</span>
          <Button variant="outline" size="sm" onClick={() => logout()}>
            Đăng xuất
          </Button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto py-8">
        <Card className="p-8 text-center space-y-3">
          <h2 className="text-base font-semibold font-display">Danh sách Đề thi của Lớp</h2>
          <p className="text-xs text-text-muted">
            Danh sách đề thi và quy trình làm bài thi sẽ được xây dựng trong Giai đoạn 5 (Bước 5.1).
          </p>
        </Card>
      </main>
    </div>
  );
};
