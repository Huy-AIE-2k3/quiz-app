import React from 'react';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';

export interface PaginationProps {
  readonly currentPage: number;
  readonly totalPages: number;
  readonly onPageChange: (page: number) => void;
  readonly totalItems?: number;
  readonly pageSize?: number;
  readonly className?: string;
}

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  onPageChange,
  totalItems,
  pageSize,
  className = '',
}) => {
  if (totalPages <= 1 && totalItems === undefined) return null;

  // Generate page numbers with ellipsis
  const getPageNumbers = () => {
    const pages: (number | string)[] = [];
    const delta = 1;

    for (let i = 1; i <= totalPages; i++) {
      if (
        i === 1 ||
        i === totalPages ||
        (i >= currentPage - delta && i <= currentPage + delta)
      ) {
        pages.push(i);
      } else if (pages[pages.length - 1] !== '...') {
        pages.push('...');
      }
    }
    return pages;
  };

  const pages = getPageNumbers();

  return (
    <div
      data-testid="pagination-nav"
      className={`flex items-center justify-between flex-wrap gap-4 py-3 text-xs font-mono select-none ${className}`}
    >
      {totalItems !== undefined && pageSize !== undefined && (
        <span className="text-text-muted">
          Hiển thị {(currentPage - 1) * pageSize + 1} -{' '}
          {Math.min(currentPage * pageSize, totalItems)} trong tổng số {totalItems}
        </span>
      )}

      <div className="flex items-center gap-1 ml-auto">
        <button
          type="button"
          onClick={() => onPageChange(1)}
          disabled={currentPage === 1}
          aria-label="Trang đầu"
          className="h-8 w-8 flex items-center justify-center rounded border border-line-subtle bg-surface text-text-secondary hover:text-text-primary hover:border-line-strong disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          <ChevronsLeft className="w-3.5 h-3.5" />
        </button>

        <button
          type="button"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          aria-label="Trang trước"
          className="h-8 w-8 flex items-center justify-center rounded border border-line-subtle bg-surface text-text-secondary hover:text-text-primary hover:border-line-strong disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          <ChevronLeft className="w-3.5 h-3.5" />
        </button>

        {pages.map((p, idx) =>
          typeof p === 'number' ? (
            <button
              key={`page-${p}`}
              type="button"
              onClick={() => onPageChange(p)}
              aria-current={p === currentPage ? 'page' : undefined}
              className={`h-8 min-w-[32px] px-2 flex items-center justify-center rounded font-semibold transition-colors ${
                p === currentPage
                  ? 'bg-brand text-canvas font-bold'
                  : 'border border-line-subtle bg-surface text-text-secondary hover:text-text-primary hover:border-line-strong'
              }`}
            >
              {p}
            </button>
          ) : (
            <span key={`dots-${idx}`} className="px-2 text-text-muted">
              ...
            </span>
          )
        )}

        <button
          type="button"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          aria-label="Trang sau"
          className="h-8 w-8 flex items-center justify-center rounded border border-line-subtle bg-surface text-text-secondary hover:text-text-primary hover:border-line-strong disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          <ChevronRight className="w-3.5 h-3.5" />
        </button>

        <button
          type="button"
          onClick={() => onPageChange(totalPages)}
          disabled={currentPage === totalPages}
          aria-label="Trang cuối"
          className="h-8 w-8 flex items-center justify-center rounded border border-line-subtle bg-surface text-text-secondary hover:text-text-primary hover:border-line-strong disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          <ChevronsRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};

