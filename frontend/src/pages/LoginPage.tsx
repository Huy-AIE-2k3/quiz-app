/**
 * Login Page.
 *
 * Implements:
 * - Credential authentication via POST /api/v1/auth/login.
 * - Return-to redirect preservation (returnTo URL param).
 * - Rate limiting (429) & invalid credential feedback in clear Vietnamese.
 * - Anti-double-click form submit protection.
 */

import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { Card } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { useAuth, AuthUser } from '../context/AuthContext';
import { request, ApiError, NetworkError } from '../lib/api';
import { VI } from '../lib/i18n/vi';

interface LoginResponse {
  token: string;
  user: AuthUser;
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

  // If already authenticated, redirect immediately
  React.useEffect(() => {
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
      const data = await request<LoginResponse>('/api/v1/auth/login', {
        method: 'POST',
        body: { username: trimmedUser, password },
        skipAuth: true,
      });

      login(data.token, data.user);

      // Navigate to destination
      if (returnTo) {
        navigate(returnTo, { replace: true });
      } else if (data.user.role === 'admin') {
        navigate('/a/classes', { replace: true });
      } else {
        navigate('/s/exams', { replace: true });
      }
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        if (err.status === 401) {
          setErrorMessage('Tên đăng nhập hoặc mật khẩu không chính xác.');
        } else if (err.status === 429) {
          setErrorMessage(err.message || VI.network.tooManyRequests);
        } else {
          setErrorMessage(err.message || VI.common.error);
        }
      } else if (err instanceof NetworkError) {
        setErrorMessage(VI.network.offline);
      } else {
        setErrorMessage(VI.common.error);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-canvas text-text-primary flex flex-col justify-center items-center p-4">
      <div className="w-full max-w-md space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <Link to="/" className="inline-flex items-center space-x-2">
            <span className="w-3.5 h-3.5 rounded-full bg-brand inline-block shadow-sm" />
            <span className="text-2xl font-bold font-display tracking-tight">MATHRIX</span>
            <Badge variant="brand" size="sm">
              TOÁN - TIN
            </Badge>
          </Link>
          <p className="text-xs text-text-muted">{VI.auth.loginSubtitle}</p>
        </div>

        {/* Login Card */}
        <Card className="p-6 sm:p-8 space-y-6 border-line-subtle shadow-md">
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
                className="p-3 rounded bg-red-500/10 border border-red-500/20 text-xs text-red-400 font-sans"
              >
                {errorMessage}
              </div>
            )}

            <Button
              type="submit"
              variant="primary"
              size="md"
              disabled={isLoading}
              className="w-full justify-center mt-2"
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
