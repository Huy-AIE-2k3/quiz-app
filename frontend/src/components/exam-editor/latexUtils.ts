/**
 * LaTeX Toolbar Templates and Validation Utilities.
 */

import katex from 'katex';

export interface LatexTemplate {
  label: string;
  template: string;
  cursorOffset?: number; // Cursor offset from end of inserted text
  description?: string;
}

export const LATEX_TEMPLATES: LatexTemplate[] = [
  { label: 'a/b', template: '\\frac{a}{b}', description: 'Phân số' },
  { label: '√x', template: '\\sqrt{x}', description: 'Căn bậc 2' },
  { label: 'ⁿ√x', template: '\\sqrt[n]{x}', description: 'Căn bậc n' },
  { label: 'xⁿ', template: 'x^{n}', description: 'Lũy thừa' },
  { label: 'xᵢ', template: 'x_{i}', description: 'Chỉ số dưới' },
  { label: '∫', template: '\\int_{a}^{b} f(x) dx', description: 'Tích phân' },
  { label: '∑', template: '\\sum_{i=1}^{n} a_i', description: 'Tổng xích-ma' },
  { label: 'lim', template: '\\lim_{x \\to x_0} f(x)', description: 'Giới hạn' },
  {
    label: '[matrix]',
    template: '\\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix}',
    description: 'Ma trận',
  },
  {
    label: '{cases}',
    template: '\\begin{cases} x + y = 1 \\\\ x - y = 0 \\end{cases}',
    description: 'Hệ phương trình',
  },
  { label: 'v⃗', template: '\\vec{v}', description: 'Vectơ' },
];

export const LATEX_SYMBOLS = [
  { label: 'α', symbol: '\\alpha' },
  { label: 'β', symbol: '\\beta' },
  { label: 'π', symbol: '\\pi' },
  { label: 'θ', symbol: '\\theta' },
  { label: 'Δ', symbol: '\\Delta' },
  { label: '≤', symbol: '\\le' },
  { label: '≥', symbol: '\\ge' },
  { label: '≠', symbol: '\\neq' },
  { label: '±', symbol: '\\pm' },
  { label: '∈', symbol: '\\in' },
  { label: '∉', symbol: '\\notin' },
  { label: '⊂', symbol: '\\subset' },
  { label: '∪', symbol: '\\cup' },
  { label: '∩', symbol: '\\cap' },
  { label: '∀', symbol: '\\forall' },
  { label: '∃', symbol: '\\exists' },
  { label: '∞', symbol: '\\infty' },
  { label: '→', symbol: '\\rightarrow' },
  { label: '⇔', symbol: '\\Leftrightarrow' },
];

/**
 * Inserts LaTeX snippet at textarea cursor position.
 * If already enclosed in math delimiters ($...$), inserts raw template;
 * otherwise automatically wraps in $...$.
 */
export function insertLatexAtCursor(
  textarea: HTMLTextAreaElement,
  snippet: string,
  onUpdate: (newValue: string) => void
): void {
  const start = textarea.selectionStart ?? textarea.value.length;
  const end = textarea.selectionEnd ?? textarea.value.length;
  const original = textarea.value;

  // Determine if cursor is currently within $...$
  const textBefore = original.substring(0, start);
  const dollarCountBefore = (textBefore.match(/(?<!\\)\$/g) || []).length;
  const isInsideMath = dollarCountBefore % 2 === 1;

  const toInsert = isInsideMath ? snippet : `$${snippet}$`;

  const updatedValue = original.substring(0, start) + toInsert + original.substring(end);
  onUpdate(updatedValue);

  // Restore cursor position inside the snippet
  const newCursorPos = start + toInsert.length;
  requestAnimationFrame(() => {
    textarea.focus();
    textarea.setSelectionRange(newCursorPos, newCursorPos);
  });
}

/**
 * Validates LaTeX expressions inside Markdown text using KaTeX throwOnError.
 * Returns the count and list of syntax errors.
 */
export function validateLatexFormulas(text: string): {
  count: number;
  errors: Array<{ formula: string; message: string }>;
} {
  if (!text) return { count: 0, errors: [] };

  const errors: Array<{ formula: string; message: string }> = [];
  // Match $$...$$ (block math) and $...$ (inline math)
  const mathRegex = /\$\$([\s\S]*?)\$\$|(?<!\\)\$([^\$\n]+?)(?<!\\)\$/g;
  let match;

  while ((match = mathRegex.exec(text)) !== null) {
    const formula = match[1] !== undefined ? match[1] : match[2];
    if (formula && formula.trim()) {
      try {
        katex.renderToString(formula, { throwOnError: true });
      } catch (err: any) {
        errors.push({
          formula,
          message: err?.message || 'Lỗi cú pháp KaTeX',
        });
      }
    }
  }

  return { count: errors.length, errors };
}

/**
 * Evaluates numeric student input for Short Number questions (Step 4.4 quick test box).
 */
export function evaluateShortNumberTest(
  input: string,
  targetValues: string[],
  tolerance: number,
  toleranceType: 'abs' | 'rel' = 'abs'
): {
  isValidNumber: boolean;
  parsedNumber: number | null;
  isCorrect: boolean;
  matchedTarget?: string;
  diff?: number;
} {
  if (!input || !input.trim()) {
    return { isValidNumber: false, parsedNumber: null, isCorrect: false };
  }

  const clean = input.trim().replace(',', '.');
  let parsed: number | null = null;

  // Fraction handling (e.g. 3/2)
  if (clean.includes('/')) {
    const parts = clean.split('/');
    if (parts.length === 2) {
      const num = parseFloat(parts[0]);
      const den = parseFloat(parts[1]);
      if (!isNaN(num) && !isNaN(den) && den !== 0) {
        parsed = num / den;
      }
    }
  } else {
    const num = parseFloat(clean);
    if (!isNaN(num) && isFinite(num)) {
      parsed = num;
    }
  }

  if (parsed === null) {
    return { isValidNumber: false, parsedNumber: null, isCorrect: false };
  }

  // Compare against accepted target values
  for (const targetStr of targetValues) {
    const targetClean = targetStr.trim().replace(',', '.');
    let targetNum: number | null = null;
    if (targetClean.includes('/')) {
      const parts = targetClean.split('/');
      if (parts.length === 2) {
        targetNum = parseFloat(parts[0]) / parseFloat(parts[1]);
      }
    } else {
      targetNum = parseFloat(targetClean);
    }

    if (targetNum !== null && !isNaN(targetNum)) {
      const diff = Math.abs(parsed - targetNum);
      const allowedTolerance =
        toleranceType === 'rel' ? Math.abs(targetNum) * (tolerance / 100) : tolerance;

      if (diff <= allowedTolerance + 1e-9) {
        return {
          isValidNumber: true,
          parsedNumber: parsed,
          isCorrect: true,
          matchedTarget: targetStr,
          diff,
        };
      }
    }
  }

  return { isValidNumber: true, parsedNumber: parsed, isCorrect: false };
}
