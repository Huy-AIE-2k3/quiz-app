/**
 * Global Error Boundary & Dynamic Chunk Update Handler.
 *
 * Implements:
 * - Application-level crash recovery UI with retry/reload action.
 * - Vite preload error handler (vite:preloadError) when newly deployed chunks conflict with cached HTML.
 * - Guarantees localStorage exam drafts and outbox remain preserved.
 */

import { Component, ErrorInfo, type ReactNode } from 'react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { VI } from '../../lib/i18n/vi';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  hasPreloadError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    hasPreloadError: false,
  };

  private preloadCleanup?: () => void;

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, hasPreloadError: false };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // In production, send to telemetry/logging service
    console.error('Uncaught error in UI component:', error, errorInfo);
  }

  public componentDidMount(): void {
    const handlePreloadError = () => {
      this.setState({ hasPreloadError: true });
    };

    if (typeof window !== 'undefined') {
      window.addEventListener('vite:preloadError', handlePreloadError);
      this.preloadCleanup = () => {
        window.removeEventListener('vite:preloadError', handlePreloadError);
      };
    }
  }

  public componentWillUnmount(): void {
    if (this.preloadCleanup) {
      this.preloadCleanup();
    }
  }

  private handleReload = () => {
    if (typeof window !== 'undefined') {
      window.location.reload();
    }
  };

  private handleReset = () => {
    this.setState({ hasError: false, error: null, hasPreloadError: false });
  };

  public render(): ReactNode {
    // 1. Vite chunk version update dialog
    if (this.state.hasPreloadError) {
      return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-canvas/80 backdrop-blur-sm">
          <Card className="max-w-md w-full p-6 space-y-4 border-brand/30 shadow-lg">
            <h2 className="text-lg font-bold font-display text-text-primary">
              {VI.server.updateTitle}
            </h2>
            <p className="text-sm text-text-secondary">{VI.server.updateMessage}</p>
            <div className="flex justify-end pt-2">
              <Button onClick={this.handleReload} variant="primary">
                {VI.common.reload}
              </Button>
            </div>
          </Card>
        </div>
      );
    }

    // 2. Fatal rendering error fallback
    if (this.state.hasError) {
      return (
        <main className="min-h-screen bg-canvas flex items-center justify-center p-4 text-text-primary">
          <Card className="max-w-lg w-full p-6 space-y-4 border-red-500/30">
            <div className="flex items-center space-x-3">
              <span className="w-3 h-3 rounded-full bg-red-500" />
              <h1 className="text-lg font-bold font-display">{VI.common.error}</h1>
            </div>

            <p className="text-sm text-text-secondary">
              Đã xảy ra sự cố ngoài dự kiến trong giao diện người dùng. Dữ liệu làm bài thi của bạn
              vẫn được bảo vệ an toàn trên thiết bị.
            </p>

            {this.state.error?.message && (
              <pre className="p-3 bg-canvas-dark rounded text-xs font-mono text-red-400 overflow-x-auto max-h-32">
                {this.state.error.message}
              </pre>
            )}

            <div className="flex items-center justify-end space-x-3 pt-3 border-t border-line-subtle">
              <Button variant="ghost" onClick={this.handleReset}>
                {VI.common.retry}
              </Button>
              <Button variant="primary" onClick={this.handleReload}>
                {VI.common.reload}
              </Button>
            </div>
          </Card>
        </main>
      );
    }

    return this.props.children;
  }
}
