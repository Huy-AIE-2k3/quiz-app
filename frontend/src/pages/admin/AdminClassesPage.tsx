/**
 * Admin Classes Dashboard Placeholder (Route /a/classes).
 */

import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Card } from '../../components/ui/Card';

export const AdminClassesPage: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-canvas text-text-primary p-6">
      <header className="max-w-6xl mx-auto flex items-center justify-between pb-6 border-b border-line-subtle">
        <div className="flex items-center space-x-3">
          <span className="w-3 h-3 rounded-full bg-brand inline-block" />
          <h1 className="text-xl font-bold font-display">Bảng Quản Trị — Lớp Học</h1>
          <Badge variant="brand" size="sm">
            ADMIN
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
          <h2 className="text-base font-semibold font-display">Khu vực Quản lý Lớp &amp; Học sinh</h2>
          <p className="text-xs text-text-muted">
            Tính năng CRUD Lớp học và Nhập học sinh qua CSV sẽ được xây dựng trong Giai đoạn 3 (Bước 3.1 &amp; 3.2).
          </p>
        </Card>
      </main>
    </div>
  );
};
