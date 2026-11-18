/**
 * ReAuthModal - In-place re-authentication modal for exam sessions (TC-5.6-04).
 *
 * Prevents page redirection when 401 Unauthorized occurs during exam taking,
 * allowing students to re-login in place and resume offline outbox syncing seamlessly.
 */

import React, { useState } from 'react';
import { Lock, AlertCircle, Loader2 } from 'lucide-react';
import { Button } from '../ui/Button';
import { safeStorage } from '../../lib/storage';
import { request, ApiError } from '../../lib/api';
import { useAuth } from '../../context/AuthContext';

interface ReAuthModalProps {
  isOpen: boolean;
  username?: string;
  onSuccess: () => void;
}

interface LoginApiResponse {
  access_token: string;
  token_type?: string;
  role?: 'admin' | 'student';
  user_id?: string;
  username?: string;
  full_name?: string;
  is_active?: boolean;
}

export const ReAuthModal: React.FC<ReAuthModalProps> = ({ isOpen, username = '', onSuccess }) => {
  const { login, user } = useAuth();
  const effectiveUsername = username || user?.username || '';

  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password.trim()) {
      setError('Vui lòng nhập mật khẩu.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await request<LoginApiResponse>('/api/v1/auth/login', {
        method: 'POST',
        body: {
          username: effectiveUsername,
          password,
        },
        skipAuth: true,
      });

      if (data.access_token) {
        safeStorage.setToken(data.access_token);
        login(data.access_token, {
          id: data.user_id || user?.id || '',
          username: data.username || effectiveUsername,
          full_name: data.full_name || user?.full_name || '',
          role: data.role || 'student',
          is_active: data.is_active ?? true,
        });

        setPassword('');
        setError(null);
        onSuccess();
      } else {
        setError('Đăng nhập không thành công, vui lòng thử lại.');
      }
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        if (err.status === 401 || err.code === 'invalid_credentials') {
          setError('Mật khẩu không chính xác.');
        } else {
          setError(err.message || 'Đăng nhập thất bại.');
        }
      } else {
        setError('Lỗi kết nối khi xác thực lại.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="reauth-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-canvas/80 backdrop-blur-xs"
    >
      <div className="w-full max-w-md bg-surface border border-line-subtle rounded-xl shadow-2xl p-6 sm:p-8 space-y-6">
        {/* Header with lock icon */}
        <div className="flex items-center space-x-3 text-status-flag-text">
          <div className="w-10 h-10 rounded-full bg-status-flag-bg border border-status-flag-border flex items-center justify-center shrink-0">
            <Lock className="w-5 h-5 text-status-flag-border" />
          </div>
          <div>
            <h2 id="reauth-modal-title" className="text-base sm:text-lg font-display font-bold text-text-primary">
              Phiên đăng nhập đã hết hạn
            </h2>
            <p className="text-xs text-text-muted">Bài thi của bạn vẫn được lưu an toàn.</p>
          </div>
        </div>

        <p className="text-xs sm:text-sm text-text-secondary leading-relaxed">
          Vui lòng nhập mật khẩu tài khoản <strong>{effectiveUsername}</strong> để tiếp tục gửi các câu trả lời
          đang chờ và không làm gián đoạn bài làm.
        </p>

        {error && (
          <div className="p-3 rounded-lg bg-status-wrong-bg border border-status-wrong-border text-status-wrong-text text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="block text-xs font-mono font-medium text-text-secondary">
              Mật khẩu:
            </label>
            <input
              type="password"
              data-testid="reauth-password-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Nhập mật khẩu để tiếp tục..."
              autoFocus
              disabled={loading}
              className="w-full px-3 py-2 rounded-lg bg-canvas border border-line-subtle text-text-primary text-sm focus:outline-hidden focus:border-brand font-sans"
            />
          </div>

          <div className="pt-2">
            <Button
              type="submit"
              variant="primary"
              disabled={loading}
              className="w-full"
              iconLeft={loading ? <Loader2 className="w-4 h-4 animate-spin" /> : undefined}
            >
              {loading ? 'Đang xác thực...' : 'Xác nhận và tiếp tục làm bài'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
