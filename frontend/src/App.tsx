import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { ToastProvider, Button, Badge } from './components';

// Code-splitting for dev showroom to keep initial bundle size minimal (TC-1.5-05)
const DevComponentsPage = lazy(() =>
  import('./pages/DevComponentsPage').then((m) => ({ default: m.DevComponentsPage }))
);

const HomePlaceholder: React.FC = () => {
  return (
    <main className="min-h-screen flex items-center justify-center p-4 bg-canvas text-text-primary">
      <div className="max-w-md w-full bg-surface border border-line-subtle rounded-lg p-6 shadow-sm text-left">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 rounded-full bg-brand animate-pulse"></div>
            <h1 className="text-xl font-bold font-display text-text-primary">Quiz Toán - Tin</h1>
          </div>
          <Badge variant="brand" size="sm">
            MATHRIX
          </Badge>
        </div>

        <p className="text-text-muted text-sm mb-6 font-sans">
          Hệ thống kiểm tra trực tuyến nội bộ dành cho học sinh Toán &amp; Tin học.
        </p>

        <div className="p-3 bg-elevated rounded-md border border-line-subtle text-xs text-text-secondary mb-6">
          Thư viện React Components chuẩn hóa Design System Emerald Precision đã sẵn sàng (Giai đoạn 1.5).
        </div>

        <div className="flex items-center justify-between pt-2 border-t border-line-subtle">
          <Link to="/dev/components">
            <Button size="sm" variant="outline">
              Mở /dev/components
            </Button>
          </Link>
          <span className="text-[11px] font-mono text-text-muted">Mathrix UI v0.1</span>
        </div>
      </div>
    </main>
  );
};

export const App: React.FC = () => {
  return (
    <ToastProvider>
      <BrowserRouter>
        <Suspense
          fallback={
            <div className="min-h-screen flex items-center justify-center bg-canvas text-text-primary">
              <span className="font-mono text-xs text-text-muted">Đang tải Mathrix UI...</span>
            </div>
          }
        >
          <Routes>
            <Route path="/" element={<HomePlaceholder />} />
            <Route path="/dev/components" element={<DevComponentsPage />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </ToastProvider>
  );
};

export default App;
