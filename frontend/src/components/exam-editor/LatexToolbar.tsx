/**
 * LaTeX Toolbar component for quick insertion of mathematical formulas and symbols.
 */

import React, { useState } from 'react';
import { LATEX_TEMPLATES, LATEX_SYMBOLS, insertLatexAtCursor } from './latexUtils';

interface LatexToolbarProps {
  textareaRef: React.RefObject<HTMLTextAreaElement>;
  value: string;
  onChange: (val: string) => void;
  disabled?: boolean;
}

export const LatexToolbar: React.FC<LatexToolbarProps> = ({
  textareaRef,
  value: _value,
  onChange,
  disabled = false,
}) => {
  const [showSymbols, setShowSymbols] = useState(false);

  const handleInsert = (snippet: string) => {
    if (disabled || !textareaRef.current) return;
    insertLatexAtCursor(textareaRef.current, snippet, onChange);
  };

  return (
    <div className="flex flex-wrap items-center gap-1.5 p-2 bg-elevated/80 border-b border-border-subtle rounded-t-lg select-none">
      <span className="text-[11px] font-mono text-text-muted mr-1 font-semibold">LaTeX:</span>

      {/* Main Formula Templates */}
      <div className="flex flex-wrap items-center gap-1">
        {LATEX_TEMPLATES.map((item) => (
          <button
            key={item.label}
            type="button"
            disabled={disabled}
            onClick={() => handleInsert(item.template)}
            title={item.description}
            className="px-2 py-0.5 rounded text-xs font-mono bg-canvas hover:bg-surface border border-border-subtle text-text-primary hover:text-brand transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {item.label}
          </button>
        ))}
      </div>

      <div className="h-4 w-px bg-border-strong mx-1" />

      {/* Symbol toggle */}
      <button
        type="button"
        disabled={disabled}
        onClick={() => setShowSymbols(!showSymbols)}
        className={`px-2 py-0.5 rounded text-xs font-mono border transition-colors ${
          showSymbols
            ? 'bg-brand/10 border-brand text-brand'
            : 'bg-canvas hover:bg-surface border-border-subtle text-text-secondary'
        } disabled:opacity-50 disabled:cursor-not-allowed`}
      >
        {showSymbols ? 'Ẩn ký hiệu ▲' : 'Ký hiệu ▼'}
      </button>

      {/* Expanded Symbols Panel */}
      {showSymbols && (
        <div className="w-full mt-1.5 pt-1.5 border-t border-border-subtle flex flex-wrap gap-1">
          {LATEX_SYMBOLS.map((sym) => (
            <button
              key={sym.label}
              type="button"
              disabled={disabled}
              onClick={() => handleInsert(sym.symbol)}
              title={sym.symbol}
              className="w-7 h-6 flex items-center justify-center rounded text-xs font-serif bg-canvas hover:bg-surface border border-border-subtle text-text-primary hover:text-brand transition-colors disabled:opacity-50"
            >
              {sym.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

