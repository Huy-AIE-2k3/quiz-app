/**
 * Public Landing Page (Guest accessible).
 * Faithfully implements the Google Stitch SC-00 Landing Design:
 * - Default Dark Theme with dotted matrix canvas and cursor flashlight spotlight.
 * - Interactive 3D Rubik's cube cluster with parallax mouse-tracking tilt.
 * - Single authenticated call-to-action to /login.
 * - Strict guest privacy: zero internal data or system metrics exposed.
 */

import React, { useEffect, useRef } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { KeyRound, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './LandingPage.css';

export const LandingPage: React.FC = () => {
  const { isAuthenticated, role } = useAuth();
  const containerRef = useRef<HTMLDivElement>(null);
  const rubikCubeRef = useRef<HTMLDivElement>(null);
  const rubikContainerRef = useRef<HTMLDivElement>(null);

  // Requirement 3: Enforce default dark theme for landing page
  useEffect(() => {
    document.documentElement.classList.add('dark');
  }, []);

  // Stitch mouse tracking: Flashlight spotlight + 3D Rubik Parallax Tilt
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const container = containerRef.current;
      if (!container) return;

      container.style.setProperty('--mouse-x', `${e.clientX}px`);
      container.style.setProperty('--mouse-y', `${e.clientY}px`);

      if (rubikCubeRef.current && rubikContainerRef.current) {
        const rect = rubikContainerRef.current.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;

        const deltaX = (e.clientX - centerX) / (window.innerWidth / 2);
        const deltaY = (e.clientY - centerY) / (window.innerHeight / 2);

        const tiltX = -22 - deltaY * 22;
        const tiltY = 34 + deltaX * 30;

        rubikCubeRef.current.style.transform = `rotateX(${tiltX}deg) rotateY(${tiltY}deg)`;
      }
    };

    const handleMouseLeave = () => {
      const container = containerRef.current;
      if (container) {
        container.style.setProperty('--mouse-x', '-500px');
        container.style.setProperty('--mouse-y', '-500px');
      }
      if (rubikCubeRef.current) {
        rubikCubeRef.current.style.transform = 'rotateX(-22deg) rotateY(34deg)';
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseleave', handleMouseLeave);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, []);

  // If already authenticated, redirect to user's home
  if (isAuthenticated) {
    return <Navigate to={role === 'admin' ? '/a/classes' : '/s/exams'} replace />;
  }

  return (
    <div
      ref={containerRef}
      className="dark bg-canvas text-text-primary font-sans min-h-screen flex flex-col justify-between relative overflow-x-hidden selection:bg-brand selection:text-canvas"
    >
      {/* Background Layer 1: Dot Matrix Canvas */}
      <div className="fixed inset-0 landing-dot-matrix pointer-events-none z-0" />

      {/* Background Layer 2: Interactive Dot Glow around Cursor */}
      <div className="fixed inset-0 landing-dot-glow pointer-events-none z-0" />

      {/* Background Layer 3: Interactive Cursor Flashlight Spotlight */}
      <div className="fixed inset-0 landing-cursor-spotlight pointer-events-none z-0" />

      {/* Ambient Glow Orbs */}
      <div className="fixed top-1/3 -left-36 w-96 h-96 bg-brand/10 rounded-full blur-[140px] pointer-events-none z-0" />
      <div className="fixed top-1/4 -right-36 w-96 h-96 bg-status-wrong-border/10 rounded-full blur-[140px] pointer-events-none z-0" />

      {/* Main Hero Stage */}
      <main className="relative z-10 flex-1 flex items-center justify-center max-w-7xl mx-auto px-6 py-12 lg:py-20 w-full">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center w-full">
          {/* Hero Left: Badge, Headline, Subtext, Single Call to Action */}
          <div className="lg:col-span-7 flex flex-col items-start gap-6 text-left">
            {/* Category Badge */}
            <div className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full bg-surface border border-line-subtle text-xs font-mono font-medium shadow-sm">
              <span className="w-2 h-2 rounded-full bg-brand animate-pulse" />
              <span className="font-display font-bold text-text-primary tracking-wider text-sm">MATHRIX</span>
              <span className="text-line-strong">/</span>
              <span className="text-brand tracking-wide">NỀN TẢNG KHẢO THÍ TOÁN &amp; TIN HỌC CHUYÊN SÂU</span>
            </div>

            {/* Headline */}
            <h1 className="font-display font-bold text-4xl sm:text-5xl lg:text-6xl text-text-primary tracking-tight leading-[1.12]">
              Test đến đâu,
              <br />
              <span className="text-brand">hiểu mình đến đó</span>
            </h1>

            {/* Subtext */}
            <p className="font-sans text-base sm:text-lg text-text-secondary max-w-xl leading-relaxed">
              Đo lường năng lực chuẩn xác với hệ thống 4 dạng thức thi mới, phân tích phổ điểm thời gian thực và sandbox
              chấm mã nguồn tự động.
            </p>

            {/* Single Sign-in Button */}
            <div className="pt-2">
              <Link
                to="/login"
                className="h-13 px-8 py-3.5 rounded-xl bg-brand hover:bg-brand-hover text-canvas font-display font-bold text-base tracking-wide inline-flex items-center justify-center gap-3 transition-all shadow-xl shadow-brand/25 active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-brand group"
                aria-label="Đăng nhập hệ thống Mathrix"
              >
                <KeyRound className="w-5 h-5 group-hover:rotate-12 transition-transform" />
                <span>Đăng nhập hệ thống</span>
                <ArrowRight className="w-5 h-5 font-bold group-hover:translate-x-1 transition-transform" />
              </Link>
            </div>
          </div>

          {/* Hero Right: 3D Interactive Rubik Cube with Floating Satellite Cubes */}
          <div className="lg:col-span-5 flex items-center justify-center relative min-h-[420px] sm:min-h-[480px]">
            {/* Center Cube Glow */}
            <div className="absolute w-72 h-72 rounded-full bg-brand/20 blur-[100px] pointer-events-none" />
            <div className="absolute w-56 h-56 rounded-full bg-status-wrong-border/15 blur-[90px] pointer-events-none" />

            {/* 3D Scene Container */}
            <div
              ref={rubikContainerRef}
              className="scene-3d w-[320px] h-[320px] sm:w-[380px] sm:h-[380px] flex items-center justify-center cursor-grab active:cursor-grabbing select-none"
              aria-label="Mô hình 3D Khối Rubik tương tác Mathrix"
            >
              <div ref={rubikCubeRef} className="rubik-cube-cluster relative w-[230px] h-[230px]">
                {/* TOP LAYER (Y: -80px) */}
                <div className="mini-cube" style={{ transform: 'translate3d(-80px, -80px, 0px)' }}>
                  <div className="cube-face face-front c-emerald" />
                  <div className="cube-face face-back c-black" />
                  <div className="cube-face face-left c-red" />
                  <div className="cube-face face-right c-black" />
                  <div className="cube-face face-top c-red" />
                  <div className="cube-face face-bottom c-black" />
                </div>

                <div className="mini-cube" style={{ transform: 'translate3d(0px, -80px, 0px)' }}>
                  <div className="cube-face face-front c-black" />
                  <div className="cube-face face-back c-red" />
                  <div className="cube-face face-left c-black" />
                  <div className="cube-face face-right c-black" />
                  <div className="cube-face face-top c-emerald" />
                  <div className="cube-face face-bottom c-black" />
                </div>

                <div className="mini-cube" style={{ transform: 'translate3d(80px, -80px, 0px)' }}>
                  <div className="cube-face face-front c-red" />
                  <div className="cube-face face-back c-black" />
                  <div className="cube-face face-left c-black" />
                  <div className="cube-face face-right c-emerald" />
                  <div className="cube-face face-top c-black" />
                  <div className="cube-face face-bottom c-black" />
                </div>

                {/* MIDDLE LAYER (Y: 0px) */}
                <div className="mini-cube" style={{ transform: 'translate3d(-80px, 0px, 0px)' }}>
                  <div className="cube-face face-front c-black" />
                  <div className="cube-face face-back c-emerald" />
                  <div className="cube-face face-left c-emerald" />
                  <div className="cube-face face-right c-black" />
                  <div className="cube-face face-top c-black" />
                  <div className="cube-face face-bottom c-black" />
                </div>

                {/* Center Core Cube with 'M' logo on front */}
                <div className="mini-cube" style={{ transform: 'translate3d(0px, 0px, 0px)' }}>
                  <div className="cube-face face-front c-emerald flex items-center justify-center font-display font-bold text-canvas text-xl">
                    M
                  </div>
                  <div className="cube-face face-back c-black" />
                  <div className="cube-face face-left c-black" />
                  <div className="cube-face face-right c-black" />
                  <div className="cube-face face-top c-black" />
                  <div className="cube-face face-bottom c-black" />
                </div>

                <div className="mini-cube" style={{ transform: 'translate3d(80px, 0px, 0px)' }}>
                  <div className="cube-face face-front c-red" />
                  <div className="cube-face face-back c-black" />
                  <div className="cube-face face-left c-black" />
                  <div className="cube-face face-right c-red" />
                  <div className="cube-face face-top c-black" />
                  <div className="cube-face face-bottom c-black" />
                </div>

                {/* BOTTOM LAYER (Y: 80px) */}
                <div className="mini-cube" style={{ transform: 'translate3d(-80px, 80px, 0px)' }}>
                  <div className="cube-face face-front c-red" />
                  <div className="cube-face face-back c-black" />
                  <div className="cube-face face-left c-black" />
                  <div className="cube-face face-right c-black" />
                  <div className="cube-face face-top c-black" />
                  <div className="cube-face face-bottom c-emerald" />
                </div>

                <div className="mini-cube" style={{ transform: 'translate3d(0px, 80px, 0px)' }}>
                  <div className="cube-face face-front c-black" />
                  <div className="cube-face face-back c-black" />
                  <div className="cube-face face-left c-black" />
                  <div className="cube-face face-right c-black" />
                  <div className="cube-face face-top c-black" />
                  <div className="cube-face face-bottom c-red" />
                </div>

                <div className="mini-cube" style={{ transform: 'translate3d(80px, 80px, 0px)' }}>
                  <div className="cube-face face-front c-emerald" />
                  <div className="cube-face face-back c-red" />
                  <div className="cube-face face-left c-black" />
                  <div className="cube-face face-right c-black" />
                  <div className="cube-face face-top c-black" />
                  <div className="cube-face face-bottom c-black" />
                </div>

                {/* FRONT FLOATING LAYER (Z: 80px) */}
                <div className="mini-cube" style={{ transform: 'translate3d(0px, 0px, 80px)' }}>
                  <div className="cube-face face-front c-red" />
                  <div className="cube-face face-back c-black" />
                  <div className="cube-face face-left c-emerald" />
                  <div className="cube-face face-right c-black" />
                  <div className="cube-face face-top c-black" />
                  <div className="cube-face face-bottom c-black" />
                </div>

                <div className="mini-cube" style={{ transform: 'translate3d(-80px, -80px, 80px)' }}>
                  <div className="cube-face face-front c-black" />
                  <div className="cube-face face-back c-black" />
                  <div className="cube-face face-left c-red" />
                  <div className="cube-face face-right c-black" />
                  <div className="cube-face face-top c-emerald" />
                  <div className="cube-face face-bottom c-black" />
                </div>

                <div className="mini-cube" style={{ transform: 'translate3d(80px, 80px, 80px)' }}>
                  <div className="cube-face face-front c-emerald" />
                  <div className="cube-face face-back c-black" />
                  <div className="cube-face face-left c-black" />
                  <div className="cube-face face-right c-red" />
                  <div className="cube-face face-top c-black" />
                  <div className="cube-face face-bottom c-black" />
                </div>

                {/* FLOATING SATELLITE MINI CUBES */}
                {/* Satellite 1: Red */}
                <div className="mini-cube satellite-1" style={{ width: '44px', height: '44px' }}>
                  <div className="cube-face c-red" style={{ width: '44px', height: '44px', transform: 'translateZ(22px)' }} />
                  <div className="cube-face c-black" style={{ width: '44px', height: '44px', transform: 'rotateY(180deg) translateZ(22px)' }} />
                  <div className="cube-face c-red" style={{ width: '44px', height: '44px', transform: 'rotateY(-90deg) translateZ(22px)' }} />
                  <div className="cube-face c-black" style={{ width: '44px', height: '44px', transform: 'rotateY(90deg) translateZ(22px)' }} />
                  <div className="cube-face c-red" style={{ width: '44px', height: '44px', transform: 'rotateX(90deg) translateZ(22px)' }} />
                  <div className="cube-face c-black" style={{ width: '44px', height: '44px', transform: 'rotateX(-90deg) translateZ(22px)' }} />
                </div>

                {/* Satellite 2: Emerald */}
                <div className="mini-cube satellite-2" style={{ width: '48px', height: '48px' }}>
                  <div className="cube-face c-emerald" style={{ width: '48px', height: '48px', transform: 'translateZ(24px)' }} />
                  <div className="cube-face c-black" style={{ width: '48px', height: '48px', transform: 'rotateY(180deg) translateZ(24px)' }} />
                  <div className="cube-face c-emerald" style={{ width: '48px', height: '48px', transform: 'rotateY(-90deg) translateZ(24px)' }} />
                  <div className="cube-face c-black" style={{ width: '48px', height: '48px', transform: 'rotateY(90deg) translateZ(24px)' }} />
                  <div className="cube-face c-emerald" style={{ width: '48px', height: '48px', transform: 'rotateX(90deg) translateZ(24px)' }} />
                  <div className="cube-face c-black" style={{ width: '48px', height: '48px', transform: 'rotateX(-90deg) translateZ(24px)' }} />
                </div>

                {/* Satellite 3: Black */}
                <div className="mini-cube satellite-3" style={{ width: '40px', height: '40px' }}>
                  <div className="cube-face c-black" style={{ width: '40px', height: '40px', transform: 'translateZ(20px)' }} />
                  <div className="cube-face c-black" style={{ width: '40px', height: '40px', transform: 'rotateY(180deg) translateZ(20px)' }} />
                  <div className="cube-face c-black" style={{ width: '40px', height: '40px', transform: 'rotateY(-90deg) translateZ(20px)' }} />
                  <div className="cube-face c-black" style={{ width: '40px', height: '40px', transform: 'rotateY(90deg) translateZ(20px)' }} />
                  <div className="cube-face c-black" style={{ width: '40px', height: '40px', transform: 'rotateX(90deg) translateZ(20px)' }} />
                  <div className="cube-face c-black" style={{ width: '40px', height: '40px', transform: 'rotateX(-90deg) translateZ(20px)' }} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Centered Footer */}
      <footer className="relative z-10 w-full border-t border-line-subtle/80 py-5 px-6 text-center text-xs font-mono text-text-muted">
        <p>Hệ thống nội bộ, vui lòng không chia sẻ ra bên ngoài</p>
      </footer>
    </div>
  );
};
