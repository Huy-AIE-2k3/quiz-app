import React from 'react';

export const App: React.FC = () => {
  return (
    <main className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-surface border border-border rounded-md p-6 shadow-sm">
        <div className="flex items-center space-x-3 mb-4">
          <div className="w-3 h-3 rounded-full bg-success"></div>
          <h1 className="text-xl font-bold text-ink">Quiz Toán - Tin</h1>
        </div>
        <p className="text-ink-muted text-sm mb-6">
          Hệ thống kiểm tra trực tuyến nội bộ dành cho học sinh Toán & Tin học.
        </p>
        <div className="p-3 bg-bg rounded-sm border border-border text-xs text-ink-muted">
          Khung ứng dụng monorepo đã sẵn sàng (Giai đoạn 0.1).
        </div>
      </div>
    </main>
  );
};

export default App;

