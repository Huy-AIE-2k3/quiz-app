/**
 * Main Application Shell & Root Routing.
 *
 * Implements:
 * - QueryClientProvider (TanStack Query)
 * - AuthProvider & Role Guards (RequireAuth)
 * - Global ErrorBoundary & Vite Chunk update handling
 * - Server Wake-up notification Banner & Storage fallback alert
 * - Strict Guest routes (Landing page and Login only)
 */

import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './lib/queryClient';
import { AuthProvider } from './context/AuthContext';
import { ToastProvider } from './components';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { ServerWakeBanner } from './components/common/ServerWakeBanner';
import { StorageWarningBanner } from './components/common/StorageWarningBanner';
import { RequireAuth } from './components/auth/RequireAuth';

import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { AdminClassesPage } from './pages/admin/AdminClassesPage';
import { AdminClassDetailPage } from './pages/admin/AdminClassDetailPage';
import { AdminStudentsPage } from './pages/admin/AdminStudentsPage';
import { AdminExamEditorPage } from './pages/admin/AdminExamEditorPage';
import { StudentExamsPage } from './pages/student/StudentExamsPage';

// Code-splitting for dev showroom to keep production bundle minimal
const DevComponentsPage = lazy(() =>
  import('./pages/DevComponentsPage').then((m) => ({ default: m.DevComponentsPage }))
);

const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public routes for Guests */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/dev/components" element={<DevComponentsPage />} />

      {/* Protected Admin Routes */}
      <Route element={<RequireAuth allowedRoles={['admin']} />}>
        <Route path="/a" element={<Navigate to="/a/classes" replace />} />
        <Route path="/a/classes" element={<AdminClassesPage />} />
        <Route path="/a/classes/:classId" element={<AdminClassDetailPage />} />
        <Route path="/a/students" element={<AdminStudentsPage />} />
        <Route path="/a/exams/:examId/edit" element={<AdminExamEditorPage />} />
      </Route>

      {/* Protected Student Routes */}
      <Route element={<RequireAuth allowedRoles={['student']} />}>
        <Route path="/s" element={<Navigate to="/s/exams" replace />} />
        <Route path="/s/exams" element={<StudentExamsPage />} />
      </Route>

      {/* Catch-all fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <ToastProvider>
            <ServerWakeBanner />
            <StorageWarningBanner />
            <BrowserRouter>
              <Suspense
                fallback={
                  <div className="min-h-screen flex items-center justify-center bg-canvas text-text-primary">
                    <span className="font-mono text-xs text-text-muted">Đang tải Mathrix UI...</span>
                  </div>
                }
              >
                <AppRoutes />
              </Suspense>
            </BrowserRouter>
          </ToastProvider>
        </AuthProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export default App;
