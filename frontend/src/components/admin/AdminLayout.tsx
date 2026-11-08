import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { BookOpen, Users, LogOut } from 'lucide-react';

interface AdminLayoutProps {
  children: React.ReactNode;
  title?: string;
  action?: React.ReactNode;
}

export const AdminLayout: React.FC<AdminLayoutProps> = ({ children, title, action }) => {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-canvas text-text-primary flex flex-col">
      {/* Top Navigation Bar */}
      <header className="border-b border-line-subtle bg-surface sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo and Nav Links */}
            <div className="flex items-center gap-8">
              <div className="flex items-center gap-3">
                <span className="w-3 h-3 rounded-full bg-brand" aria-hidden="true" />
                <span className="text-lg font-bold font-display tracking-tight">MATHRIX ADMIN</span>
                <Badge variant="brand" size="sm">
                  QUẢN TRỊ
                </Badge>
              </div>

              <nav className="flex items-center gap-1">
                <NavLink
                  to="/a/classes"
                  className={({ isActive }) =>
                    `flex items-center gap-2 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                      isActive
                        ? 'bg-brand/10 text-brand font-semibold'
                        : 'text-text-secondary hover:text-text-primary hover:bg-surface-raised'
                    }`
                  }
                >
                  <BookOpen className="w-4 h-4" />
                  Lớp học
                </NavLink>

                <NavLink
                  to="/a/students"
                  className={({ isActive }) =>
                    `flex items-center gap-2 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                      isActive
                        ? 'bg-brand/10 text-brand font-semibold'
                        : 'text-text-secondary hover:text-text-primary hover:bg-surface-raised'
                    }`
                  }
                >
                  <Users className="w-4 h-4" />
                  Học sinh
                </NavLink>
              </nav>
            </div>

            {/* User Profile & Logout */}
            <div className="flex items-center gap-4">
              <span className="text-xs text-text-secondary font-mono hidden sm:inline-block">
                {user?.full_name} ({user?.username})
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => logout()}
                className="text-text-secondary hover:text-status-wrong-text flex items-center gap-1.5"
                title="Đăng xuất khỏi hệ thống"
              >
                <LogOut className="w-4 h-4" />
                <span className="hidden sm:inline">Đăng xuất</span>
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Page Header (Optional title and action button) */}
      {title && (
        <div className="bg-surface border-b border-line-subtle py-4 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <h1 className="text-xl font-bold font-display tracking-tight text-text-primary">{title}</h1>
            {action && <div className="flex items-center gap-2">{action}</div>}
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">{children}</main>
    </div>
  );
};
