/**
 * Role-Based Route Guard (RequireAuth).
 *
 * Enforces:
 * - Unauthenticated users are redirected to /login?returnTo=...
 * - Authenticated users with invalid role are redirected to their default role dashboard:
 *   - Student -> /s/exams
 *   - Admin -> /a/classes
 * - Zero flash of forbidden content: renders skeleton while loading user session.
 */

import React from 'react';
import { Navigate, useLocation, Outlet } from 'react-router-dom';
import { useAuth, UserRole } from '../../context/AuthContext';
import { Skeleton } from '../ui/Skeleton';

interface RequireAuthProps {
  allowedRoles?: UserRole[];
  children?: React.ReactNode;
}

export const RequireAuth: React.FC<RequireAuthProps> = ({ allowedRoles, children }) => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-canvas flex flex-col items-center justify-center p-6 space-y-4">
        <Skeleton variant="rect" className="w-64 h-8" />
        <Skeleton variant="rect" className="w-80 h-32" />
        <span className="text-xs font-mono text-text-muted">Đang kiểm tra quyền truy cập...</span>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    const returnTo = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/login?returnTo=${returnTo}`} replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    // Redirect to default home for their role
    const target = user.role === 'admin' ? '/a/classes' : '/s/exams';
    return <Navigate to={target} replace />;
  }

  return children ? <>{children}</> : <Outlet />;
};
