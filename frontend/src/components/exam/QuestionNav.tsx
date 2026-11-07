import React from 'react';

export type QuestionCellStatus = 'unanswered' | 'answered' | 'flagged';

export interface QuestionNavItem {
  readonly id: string;
  readonly number: number;
  readonly status: QuestionCellStatus;
}

export interface QuestionNavProps {
  readonly questions: readonly QuestionNavItem[];
  readonly currentQuestion: number;
  readonly onSelectQuestion: (questionNumber: number) => void;
  readonly className?: string;
}

export const QuestionNav: React.FC<QuestionNavProps> = ({
  questions,
  currentQuestion,
  onSelectQuestion,
  className = '',
}) => {
  const answeredCount = questions.filter((q) => q.status === 'answered').length;
  const flaggedCount = questions.filter((q) => q.status === 'flagged').length;
  const totalCount = questions.length;
  const percentage = totalCount > 0 ? Math.round((answeredCount / totalCount) * 100) : 0;

  return (
    <div
      data-testid="question-nav"
      className={`flex flex-col gap-4 p-4 rounded-lg bg-surface border border-line-subtle text-left ${className}`}
    >
      <div className="flex flex-col gap-1.5 border-b border-line-subtle pb-3">
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-text-secondary">Tiến độ làm bài</span>
          <span className="font-semibold text-brand">
            {answeredCount}/{totalCount} ({percentage}%)
          </span>
        </div>
        <div className="w-full h-1.5 rounded-full bg-elevated overflow-hidden">
          <div
            className="h-full bg-brand transition-all duration-300 rounded-full"
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>

      {/* Grid Palette */}
      <div className="grid grid-cols-5 sm:grid-cols-5 gap-2 max-h-72 overflow-y-auto pr-1">
        {questions.map((q) => {
          const isActive = q.number === currentQuestion;
          const isAnswered = q.status === 'answered';
          const isFlagged = q.status === 'flagged';

          return (
            <button
              key={q.id}
              type="button"
              data-testid={`question-btn-${q.number}`}
              data-status={q.status}
              data-active={isActive ? 'true' : 'false'}
              onClick={() => onSelectQuestion(q.number)}
              aria-label={`Câu ${q.number}: ${
                isAnswered ? 'Đã trả lời' : isFlagged ? 'Đã đánh dấu' : 'Chưa trả lời'
              }${isActive ? ', Đang chọn' : ''}`}
              className={`relative h-10 rounded-md font-mono text-xs font-semibold flex items-center justify-center transition-all select-none focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-1 focus:ring-offset-surface ${
                isAnswered
                  ? 'bg-brand text-canvas font-bold hover:bg-brand-hover shadow-xs'
                  : 'bg-elevated text-text-primary border border-line-subtle hover:border-line-strong'
              } ${isActive ? 'ring-2 ring-brand border-brand' : ''}`}
            >
              <span>{q.number}</span>

              {isFlagged && (
                <span
                  data-testid={`flag-indicator-${q.number}`}
                  aria-hidden="true"
                  className="absolute top-1 right-1 w-2 h-2 rounded-full bg-status-flag-text ring-1 ring-canvas"
                />
              )}
            </button>
          );
        })}
      </div>

      {/* Legend */}
      <div className="grid grid-cols-2 gap-2 pt-2 border-t border-line-subtle text-[11px] font-mono text-text-muted">
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded bg-brand" />
          <span>Đã làm ({answeredCount})</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded bg-elevated border border-line-subtle" />
          <span>Chưa làm</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-status-flag-text" />
          <span>Đánh dấu ({flaggedCount})</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded ring-2 ring-brand" />
          <span>Đang xem</span>
        </div>
      </div>
    </div>
  );
};

