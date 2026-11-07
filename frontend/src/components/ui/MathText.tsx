import React, { Component, ErrorInfo, ReactNode, memo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import rehypeSanitize from 'rehype-sanitize';
import { AlertTriangle, AlertCircle } from 'lucide-react';
import { isAllowedImageSource, normalizeBlockMath } from './mathUtils';
import 'katex/dist/katex.min.css';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  errorMessage?: string;
}

class MathTextErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, errorMessage: error.message };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('MathText rendering error:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <span
          role="alert"
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-status-wrong-bg text-status-wrong-text border border-status-wrong-border font-mono text-xs select-none"
        >
          <AlertCircle className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
          <span>[Lỗi hiển thị công thức/nội dung]</span>
        </span>
      );
    }
    return this.props.children;
  }
}

export interface MathTextProps {
  readonly content: string;
  readonly className?: string;
  readonly allowBlobUrl?: boolean;
  readonly allowedR2Domains?: readonly string[];
}

const katexOptions = {
  throwOnError: false,
  strict: 'ignore',
  trust: false,
  errorColor: 'var(--status-wrong-text)',
  maxExpand: 1000,
  maxSize: 20,
};

const MathTextRenderer: React.FC<MathTextProps> = ({
  content,
  className = '',
  allowBlobUrl = false,
  allowedR2Domains = [],
}) => {
  const normalizedContent = normalizeBlockMath(content);

  return (
    <MathTextErrorBoundary>
      <div className={`prose-math text-text-primary text-sm leading-relaxed ${className}`}>
        <ReactMarkdown
          remarkPlugins={[remarkMath]}
          rehypePlugins={[
            rehypeSanitize,
            [rehypeKatex, katexOptions],
          ]}
          components={{
            img: ({ src, alt }) => {
              const isValid = isAllowedImageSource(src, allowBlobUrl, allowedR2Domains);
              if (!isValid) {
                return (
                  <span
                    role="img"
                    aria-label={alt || 'Ảnh ngoài nguồn cho phép'}
                    className="my-2 inline-flex items-center gap-2 px-3 py-2 rounded-md border border-status-wrong-border bg-status-wrong-bg/15 text-status-wrong-text text-xs font-mono select-none"
                  >
                    <AlertTriangle className="w-4 h-4 shrink-0" aria-hidden="true" />
                    <span>[Ảnh không hợp lệ hoặc từ nguồn không được phép]</span>
                  </span>
                );
              }

              return (
                <img
                  src={src}
                  alt={alt || ''}
                  loading="lazy"
                  className="max-w-full h-auto rounded-md border border-line-subtle my-2"
                />
              );
            },
            a: ({ href, children, ...props }) => {
              const isUnsafe =
                !href ||
                href.toLowerCase().startsWith('javascript:') ||
                href.toLowerCase().startsWith('data:');

              if (isUnsafe) {
                return <span className="text-text-muted cursor-not-allowed">{children}</span>;
              }

              return (
                <a
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-brand hover:underline font-medium"
                  {...props}
                >
                  {children}
                </a>
              );
            },
            pre: ({ children, ...props }) => (
              <pre
                className="my-3 p-3.5 rounded-lg bg-surface border border-line-subtle font-mono text-xs overflow-x-auto text-text-primary leading-relaxed"
                {...props}
              >
                {children}
              </pre>
            ),
            code: ({ className: codeClassName, children, ...props }) => {
              const isBlock = codeClassName?.includes('language-');
              if (!isBlock) {
                return (
                  <code
                    className="px-1.5 py-0.5 rounded bg-elevated border border-line-subtle font-mono text-xs text-brand font-medium"
                    {...props}
                  >
                    {children}
                  </code>
                );
              }
              return (
                <code className="font-mono text-xs leading-relaxed block" {...props}>
                  {children}
                </code>
              );
            },
            table: ({ children, ...props }) => (
              <div className="my-3 overflow-x-auto rounded border border-line-subtle">
                <table className="w-full text-left text-xs font-sans" {...props}>
                  {children}
                </table>
              </div>
            ),
            th: ({ children, ...props }) => (
              <th className="p-2.5 bg-elevated font-mono font-semibold border-b border-line-subtle" {...props}>
                {children}
              </th>
            ),
            td: ({ children, ...props }) => (
              <td className="p-2.5 border-b border-line-subtle/50" {...props}>
                {children}
              </td>
            ),
          }}
        >
          {normalizedContent}
        </ReactMarkdown>
      </div>
    </MathTextErrorBoundary>
  );
};

export const MathText = memo(MathTextRenderer);
MathText.displayName = 'MathText';
