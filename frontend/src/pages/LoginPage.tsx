/**
 * Login Page.
 *
 * Implements:
 * - Credential authentication via POST /api/v1/auth/login.
 * - Return-to redirect preservation (returnTo URL param).
 * - Rate limiting (429) & invalid credential feedback in clear Vietnamese.
 * - Anti-double-click form submit protection.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { AlertCircle } from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { useAuth, AuthUser } from '../context/AuthContext';
import { request, ApiError, NetworkError } from '../lib/api';
import { VI } from '../lib/i18n/vi';
import './LandingPage.css';

interface BackendLoginResponse {
  access_token?: string;
  token?: string;
  token_type?: string;
  role?: 'admin' | 'student';
  user_id?: string;
  username?: string;
  full_name?: string;
  expires_at?: string;
  user?: AuthUser;
}

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated, role } = useAuth();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Extract returnTo query parameter safely
  const searchParams = new URLSearchParams(location.search);
  const rawReturnTo = searchParams.get('returnTo');
  const returnTo = rawReturnTo && rawReturnTo.startsWith('/') ? rawReturnTo : null;

  // Enforce default dark theme for login page
  useEffect(() => {
    document.documentElement.classList.add('dark');
  }, []);

  // If already authenticated, redirect immediately
  useEffect(() => {
    if (isAuthenticated) {
      if (returnTo) {
        navigate(returnTo, { replace: true });
      } else {
        navigate(role === 'admin' ? '/a/classes' : '/s/exams', { replace: true });
      }
    }
  }, [isAuthenticated, role, returnTo, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isLoading) return;

    const trimmedUser = username.trim().toLowerCase();
    if (!trimmedUser || !password) {
      setErrorMessage('Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const data = await request<BackendLoginResponse>('/api/v1/auth/login', {
        method: 'POST',
        body: { username: trimmedUser, password },
        skipAuth: true,
      });

      const token = data.access_token || data.token;
      if (!token) {
        throw new Error('Máy chủ không trả về token xác thực hợp lệ.');
      }

      const role = data.role || data.user?.role || 'student';
      const authUser: AuthUser = data.user || {
        id: data.user_id || '',
        username: data.username || trimmedUser,
        full_name: data.full_name || trimmedUser,
        role: role,
        is_active: true,
      };

      login(token, authUser);

      // Navigate to destination
      if (returnTo) {
        navigate(returnTo, { replace: true });
      } else if (role === 'admin') {
        navigate('/a/classes', { replace: true });
      } else {
        navigate('/s/exams', { replace: true });
      }
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        if (err.status === 401 || err.code === 'invalid_credentials') {
          setErrorMessage('Tên đăng nhập hoặc mật khẩu không chính xác.');
        } else if (err.status === 403 || err.code === 'account_disabled') {
          setErrorMessage(err.message || 'Tài khoản đã bị tạm khóa. Vui lòng liên hệ giáo viên quản trị.');
        } else if (err.status === 429 || err.code === 'rate_limited') {
          setErrorMessage(err.message || VI.network.tooManyRequests);
        } else if (err.status === 502 || err.status === 503 || err.status === 504) {
          setErrorMessage('Máy chủ đang khởi động hoặc chưa sẵn sàng. Vui lòng thử lại sau vài giây.');
        } else {
          setErrorMessage(err.message || 'Đã có lỗi xảy ra trong quá trình đăng nhập. Vui lòng thử lại.');
        }
      } else if (err instanceof NetworkError) {
        setErrorMessage(
          err.message || 'Không thể kết nối đến máy chủ. Vui lòng kiểm tra lại mạng hoặc đảm bảo backend đang chạy.'
        );
      } else if (err instanceof Error) {
        setErrorMessage(err.message || VI.common.error);
      } else {
        setErrorMessage(VI.common.error);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="dark min-h-screen bg-canvas text-text-primary flex flex-col justify-center items-center p-4 relative overflow-hidden selection:bg-brand selection:text-canvas">
      {/* Background Dot Matrix Canvas & Ambient Glow */}
      <div className="fixed inset-0 landing-dot-matrix pointer-events-none z-0" />
      <div className="fixed top-1/4 -left-36 w-80 h-80 bg-brand/10 rounded-full blur-[120px] pointer-events-none z-0" />
      <div className="fixed bottom-1/4 -right-36 w-80 h-80 bg-status-wrong-border/10 rounded-full blur-[120px] pointer-events-none z-0" />

      <div className="w-full max-w-md space-y-6 relative z-10">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <Link to="/" className="inline-flex items-center space-x-2">
            <span className="w-3.5 h-3.5 rounded-full bg-brand inline-block shadow-sm shadow-brand/40" />
            <span className="text-2xl font-bold font-display tracking-tight">MATHRIX</span>
            <Badge variant="brand" size="sm">
              TOÁN - TIN
            </Badge>
          </Link>
          <p className="text-xs text-text-muted font-sans">{VI.auth.loginSubtitle}</p>
        </div>

        {/* Login Card */}
        <Card className="p-6 sm:p-8 space-y-6 border-line-subtle shadow-2xl bg-surface relative z-10">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1">
              <label htmlFor="username" className="block text-xs font-semibold text-text-secondary">
                {VI.auth.username}
              </label>
              <Input
                id="username"
                name="username"
                type="text"
                autoComplete="username"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="vd: hocsinh01 hoặc teacher"
                disabled={isLoading}
                className="w-full"
              />
            </div>

            <div className="space-y-1">
              <label htmlFor="password" className="block text-xs font-semibold text-text-secondary">
                {VI.auth.password}
              </label>
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                isPasswordToggle
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                disabled={isLoading}
                className="w-full"
              />
            </div>

            {errorMessage && (
              <div
                role="alert"
                className="p-3 rounded-md bg-status-wrong-bg border border-status-wrong-border text-xs text-status-wrong-text font-sans flex items-start gap-2.5 animate-in fade-in"
              >
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span className="leading-relaxed">{errorMessage}</span>
              </div>
            )}

            <Button
              type="submit"
              variant="primary"
              size="md"
              disabled={isLoading}
              className="w-full justify-center mt-2 shadow-lg shadow-brand/20"
            >
              {isLoading ? VI.auth.signingIn : VI.auth.signIn}
            </Button>
          </form>
        </Card>

        {/* Guest Return Link */}
        <div className="text-center">
          <Link
            to="/"
            className="text-xs text-text-muted hover:text-brand transition-colors font-mono"
          >
            &larr; Về trang chủ công khai
          </Link>
        </div>
      </div>
    </div>
  );
};
