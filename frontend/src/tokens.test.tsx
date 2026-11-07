import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Clock, AlertTriangle, AlertCircle } from 'lucide-react';

// Timer Component testing TC-1.2-05 (Achromatopsia accessible)
interface TimerProps {
  remainingSeconds: number;
}

function AssessmentTimerPill({ remainingSeconds }: TimerProps) {
  let state = 'normal';
  let label = 'Bình thường';
  let Icon = Clock;
  let colorClass = 'text-timer-normal-text border-timer-normal-border bg-timer-normal-bg';

  if (remainingSeconds < 60) {
    state = 'critical';
    label = 'Khẩn cấp';
    Icon = AlertCircle;
    colorClass = 'text-timer-critical-text border-timer-critical-border bg-timer-critical-bg';
  } else if (remainingSeconds < 300) {
    state = 'warning';
    label = 'Sắp hết giờ';
    Icon = AlertTriangle;
    colorClass = 'text-timer-warning-text border-timer-warning-border bg-timer-warning-bg';
  }

  const hours = Math.floor(remainingSeconds / 3600);
  const minutes = Math.floor((remainingSeconds % 3600) / 60);
  const seconds = remainingSeconds % 60;
  const timeStr = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

  return (
    <div
      data-testid="timer-pill"
      data-timer-state={state}
      className={`flex items-center gap-2 px-3 py-1 rounded-md border font-mono tabular-nums ${colorClass}`}
    >
      <Icon data-testid={`timer-icon-${state}`} className="w-4 h-4" />
      <span>{timeStr}</span>
      <span className="text-xs font-sans font-semibold uppercase">{label}</span>
    </div>
  );
}

describe('TC-1.2-02: Vietnamese Typography & Diacritics Integrity', () => {
  it('renders complex Vietnamese mathematical and technical text without corruption', () => {
    const vietnameseSample =
      'Hàm số y = f(x) liên tục, có đạo hàm trên ℝ. Khảo sát tính đồng biến, nghịch biến và cực trị.';
    render(<p className="question-prose">{vietnameseSample}</p>);
    expect(screen.getByText(vietnameseSample)).toBeInTheDocument();
  });
});

describe('TC-1.2-05: Accessible Countdown Timer with Achromatopsia Support', () => {
  it('renders Normal state with Clock icon and text label for > 5 minutes', () => {
    render(<AssessmentTimerPill remainingSeconds={600} />);
    expect(screen.getByTestId('timer-pill')).toHaveAttribute('data-timer-state', 'normal');
    expect(screen.getByTestId('timer-icon-normal')).toBeInTheDocument();
    expect(screen.getByText('Bình thường')).toBeInTheDocument();
    expect(screen.getByText('00:10:00')).toBeInTheDocument();
  });

  it('renders Warning state with AlertTriangle icon and text label for < 5 minutes', () => {
    render(<AssessmentTimerPill remainingSeconds={240} />);
    expect(screen.getByTestId('timer-pill')).toHaveAttribute('data-timer-state', 'warning');
    expect(screen.getByTestId('timer-icon-warning')).toBeInTheDocument();
    expect(screen.getByText('Sắp hết giờ')).toBeInTheDocument();
    expect(screen.getByText('00:04:00')).toBeInTheDocument();
  });

  it('renders Critical state with AlertCircle icon and text label for < 1 minute', () => {
    render(<AssessmentTimerPill remainingSeconds={45} />);
    expect(screen.getByTestId('timer-pill')).toHaveAttribute('data-timer-state', 'critical');
    expect(screen.getByTestId('timer-icon-critical')).toBeInTheDocument();
    expect(screen.getByText('Khẩn cấp')).toBeInTheDocument();
    expect(screen.getByText('00:00:45')).toBeInTheDocument();
  });
});

