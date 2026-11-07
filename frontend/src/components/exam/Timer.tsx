import React, { useState, useEffect, useRef } from 'react';
import { Clock, AlertTriangle, AlertCircle } from 'lucide-react';

export type TimerState = 'normal' | 'warning' | 'critical' | 'expired';

export interface TimerProps {
  readonly initialSeconds?: number;
  readonly remainingSeconds?: number;
  readonly onTimeUp?: () => void;
  readonly isRunning?: boolean;
  readonly className?: string;
}

export const Timer: React.FC<TimerProps> = ({
  initialSeconds = 3600,
  remainingSeconds: externalSeconds,
  onTimeUp,
  isRunning = true,
  className = '',
}) => {
  const [secondsLeft, setSecondsLeft] = useState<number>(
    externalSeconds !== undefined ? externalSeconds : initialSeconds
  );
  const [announcement, setAnnouncement] = useState<string>('');
  const prevStateRef = useRef<TimerState>('normal');

  // Synchronize external remainingSeconds if provided
  useEffect(() => {
    if (externalSeconds !== undefined) {
      setSecondsLeft(externalSeconds);
    }
  }, [externalSeconds]);

  // Monotonic interval countdown when standalone
  useEffect(() => {
    if (externalSeconds !== undefined || !isRunning) return;

    const interval = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          onTimeUp?.();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [externalSeconds, isRunning, onTimeUp]);

  // Calculate current state
  let state: TimerState = 'normal';
  let label = 'Bình thường';
  let Icon = Clock;
  let colorClass = 'text-timer-normal-text border-timer-normal-border bg-timer-normal-bg';

  if (secondsLeft <= 0) {
    state = 'expired';
    label = 'Hết giờ';
    Icon = AlertCircle;
    colorClass = 'text-timer-critical-text border-timer-critical-border bg-timer-critical-bg';
  } else if (secondsLeft < 60) {
    state = 'critical';
    label = 'Khẩn cấp';
    Icon = AlertCircle;
    colorClass = 'text-timer-critical-text border-timer-critical-border bg-timer-critical-bg';
  } else if (secondsLeft < 300) {
    state = 'warning';
    label = 'Sắp hết giờ';
    Icon = AlertTriangle;
    colorClass = 'text-timer-warning-text border-timer-warning-border bg-timer-warning-bg';
  }

  // Accessibility: Only emit aria-live announcements when transitioning milestone states
  useEffect(() => {
    if (state !== prevStateRef.current) {
      if (state === 'warning') {
        setAnnouncement('Cảnh báo: Thời gian làm bài còn dưới 5 phút');
      } else if (state === 'critical') {
        setAnnouncement('Khẩn cấp: Thời gian làm bài còn dưới 1 phút');
      } else if (state === 'expired') {
        setAnnouncement('Đã hết thời gian làm bài. Hệ thống đang tiến hành nộp bài');
      }
      prevStateRef.current = state;
    }
  }, [state]);

  const hours = Math.floor(secondsLeft / 3600);
  const minutes = Math.floor((secondsLeft % 3600) / 60);
  const seconds = secondsLeft % 60;
  const timeStr = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

  return (
    <div className="inline-flex flex-col items-center">
      <div
        data-testid="timer-pill"
        data-timer-state={state}
        className={`flex items-center gap-2 px-3 py-1.5 rounded-md border font-mono tabular-nums text-sm font-semibold select-none transition-colors ${colorClass} ${className}`}
      >
        <Icon data-testid={`timer-icon-${state}`} className={`w-4 h-4 shrink-0 ${state === 'critical' ? 'animate-pulse' : ''}`} aria-hidden="true" />
        <span>{timeStr}</span>
        <span className="text-[11px] font-sans font-semibold uppercase px-1.5 py-0.5 rounded bg-canvas/30">
          {label}
        </span>
      </div>

      {/* Screen reader milestone announcement only */}
      <div aria-live="polite" aria-atomic="true" className="sr-only">
        {announcement}
      </div>
    </div>
  );
};

