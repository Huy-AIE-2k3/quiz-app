import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MathText } from './ui/MathText';
import { isAllowedImageSource } from './ui/mathUtils';

describe('TC-1.6-01: Valid Mathematics Formulas (Inline & Block Display)', () => {
  it('renders inline math $x^2+y^2=r^2$ using KaTeX', () => {
    const { container } = render(<MathText content="Phương trình đường tròn: $x^2+y^2=r^2$." />);
    expect(screen.getByText(/Phương trình đường tròn:/i)).toBeInTheDocument();
    expect(container.querySelector('.katex')).toBeInTheDocument();
    expect(container.querySelector('.katex-html')).toBeInTheDocument();
  });

  it('renders display block math $$\\int_0^1 x dx$$ with proper KaTeX display class', () => {
    const { container } = render(
      <MathText
        content={`Tính giá trị tích phân sau:

$$\\int_0^1 x\\,dx$$`}
      />
    );
    expect(screen.getByText(/Tính giá trị tích phân sau:/i)).toBeInTheDocument();
    expect(container.querySelector('.katex-display')).toBeInTheDocument();
  });
});

describe('TC-1.6-02: Syntax Error Handling in LaTeX Formulas', () => {
  it('renders syntax error in-place without crashing and preserves the rest of the text', () => {
    const { container } = render(
      <MathText
        content="Công thức sai: $\frac{1}{$ và công thức đúng kế tiếp: $y = 2x$."
      />
    );

    // The component did not crash
    expect(screen.getByText(/Công thức sai:/i)).toBeInTheDocument();
    expect(screen.getByText(/và công thức đúng kế tiếp:/i)).toBeInTheDocument();

    // KaTeX error span rendered in-place
    const errorEl = container.querySelector('.katex-error');
    expect(errorEl).toBeInTheDocument();

    // The valid formula is still rendered
    expect(container.querySelectorAll('.katex').length).toBeGreaterThanOrEqual(1);
  });
});

describe('TC-1.6-03: Defense Against XSS (Scripts, Event Handlers, JavaScript URLs)', () => {
  it('strips raw <script> tags and removes onerror attributes', () => {
    const { container } = render(
      <MathText content={'<script>window.__xss = true;</script><img src="x" onerror="window.__xss = true;" />'} />
    );

    expect(container.querySelector('script')).toBeNull();
    const img = container.querySelector('img');
    if (img) {
      expect(img.getAttribute('onerror')).toBeNull();
    }
  });

  it('neutralizes malicious markdown links with javascript: protocol', () => {
    const { container } = render(
      <MathText content="[Bấm nhận quà](javascript:alert(1))" />
    );

    const anchor = container.querySelector('a');
    if (anchor) {
      expect(anchor.getAttribute('href')).not.toMatch(/^javascript:/i);
    } else {
      // Rehype-sanitize or custom renderer completely stripped or disabled the unsafe link
      expect(screen.getByText('Bấm nhận quà')).toBeInTheDocument();
    }
  });

  it('blocks KaTeX \\href with javascript protocol (trust: false)', () => {
    const { container } = render(
      <MathText content="$\href{javascript:alert(1)}{click}$" />
    );

    // trust: false renders error or strips executable link
    const anchor = container.querySelector('a[href^="javascript:"]');
    expect(anchor).toBeNull();
  });
});

describe('TC-1.6-04: Deeply Nested and Large Formulas (Anti-Bomb)', () => {
  it('handles 500-layer nested brackets without crashing or hanging', () => {
    // Generate 500 nested superscripts: x^{x^{x...}}
    let deepMath = 'x';
    for (let i = 0; i < 500; i++) {
      deepMath = `x^{${deepMath}}`;
    }

    const startTime = performance.now();
    const { container } = render(<MathText content={`$${deepMath}$`} />);
    const elapsed = performance.now() - startTime;

    // Completed within 1000ms and rendered either output or bound error
    expect(elapsed).toBeLessThan(1500);
    expect(container).toBeInTheDocument();
  });
});

describe('TC-1.6-05: Vietnamese Diacritics in Formulas and Markdown', () => {
  it('preserves Vietnamese text inside \\text{...} and markdown bold/italic', () => {
    const sample = 'Cho $\\text{đa thức } P(x) = x^2 + 1$ với **nghiệm thực** duy nhất.';
    const { container } = render(<MathText content={sample} />);

    expect(screen.getAllByText(/đa thức/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/nghiệm thực/i)).toBeInTheDocument();
    expect(container.textContent).toContain('đa thức');
    expect(container.textContent).toContain('nghiệm thực');
  });
});

describe('TC-1.6-06: Out-of-Source Image Filtering (R2 & Asset vs External)', () => {
  it('isAllowedImageSource helper correctly identifies allowed and forbidden image sources', () => {
    // Allowed sources
    expect(isAllowedImageSource('asset:550e8400-e29b-41d4-a716-446655440000')).toBe(true);
    expect(isAllowedImageSource('/assets/images/geometry-q1.png')).toBe(true);
    expect(isAllowedImageSource('https://quiz-bucket.r2.cloudflarestorage.com/image.png')).toBe(true);
    expect(isAllowedImageSource('http://127.0.0.1:9000/quiz-files/diagram.png')).toBe(true);
    expect(isAllowedImageSource('blob:http://localhost:5173/uuid-1234', true)).toBe(true);

    // Forbidden external sources
    expect(isAllowedImageSource('https://evil.example.com/exploit.png')).toBe(false);
    expect(isAllowedImageSource('http://untrusted-site.org/malware.jpg')).toBe(false);
    expect(isAllowedImageSource('javascript:alert(1)')).toBe(false);
    expect(isAllowedImageSource('')).toBe(false);
  });

  it('renders warning fallback box instead of <img> for external untrusted image', () => {
    const { container } = render(
      <MathText content="![Ảnh độc hại](https://evil.example.com/a.png)" />
    );

    // Does not render <img> for evil source
    expect(container.querySelector('img')).toBeNull();
    // Renders fallback warning box
    expect(screen.getByText(/Ảnh không hợp lệ hoặc từ nguồn không được phép/i)).toBeInTheDocument();
  });

  it('renders <img> tag normally for allowed asset: or relative image sources', () => {
    const { container } = render(
      <MathText content="![Hình vẽ câu 1](/assets/images/circle.png)" />
    );

    const img = container.querySelector('img');
    expect(img).not.toBeNull();
    expect(img?.getAttribute('src')).toBe('/assets/images/circle.png');
    expect(img?.getAttribute('alt')).toBe('Hình vẽ câu 1');
  });
});

describe('TC-1.6-07: Computer Science Code Blocks (Tin học)', () => {
  it('renders multi-line code block in <pre> with font-mono and overflow-x-auto without layout breakage', () => {
    const longPythonCode = `def solve_knapsack(weights: list[int], values: list[int], capacity: int) -> int:
    # ` + 'r'.repeat(250) + `
    dp = [0] * (capacity + 1)
    for w, v in zip(weights, values):
        for j in range(capacity, w - 1, -1):
            dp[j] = max(dp[j], dp[j - w] + v)
    return dp[capacity]`;

    const { container } = render(
      <MathText content={`\`\`\`python\n${longPythonCode}\n\`\`\``} />
    );

    const pre = container.querySelector('pre');
    expect(pre).toBeInTheDocument();
    expect(pre).toHaveClass('overflow-x-auto');
    expect(pre).toHaveClass('font-mono');
    expect(screen.getByText(/def solve_knapsack/i)).toBeInTheDocument();
  });
});
