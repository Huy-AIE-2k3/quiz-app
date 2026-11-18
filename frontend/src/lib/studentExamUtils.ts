/**
 * Student Examination Utility Functions (Step 5.1).
 *
 * Provides shared helpers for badge styling, subject labels, and date formatting.
 */

import { StudentExamState } from './studentApi';
import { BadgeProps } from '../components/ui/Badge';

export const getStateBadgeConfig = (
  state: StudentExamState
): { label: string; variant: BadgeProps['variant']; dot: boolean } => {
  switch (state) {
    case 'open':
      return { label: 'Đang mở', variant: 'brand', dot: true };
    case 'in_progress':
      return { label: 'Đang làm dở', variant: 'warning', dot: true };
    case 'upcoming':
      return { label: 'Sắp diễn ra', variant: 'info', dot: true };
    case 'submitted':
      return { label: 'Đã nộp bài', variant: 'neutral', dot: false };
    case 'result_available':
      return { label: 'Đã có điểm', variant: 'brand', dot: false };
    case 'closed':
    default:
      return { label: 'Đã kết thúc', variant: 'neutral', dot: false };
  }
};

export const getSubjectLabel = (subject: string): string => {
  switch (subject.toLowerCase()) {
    case 'toan':
    case 'math':
      return 'Toán học';
    case 'tin':
    case 'computer_science':
      return 'Tin học';
    case 'both':
      return 'Toán & Tin';
    default:
      return subject;
  }
};

export const formatDateTime = (isoString: string | null): string => {
  if (!isoString) return 'Không giới hạn';
  try {
    const d = new Date(isoString);
    return new Intl.DateTimeFormat('vi-VN', {
      hour: '2-digit',
      minute: '2-digit',
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    }).format(d);
  } catch {
    return isoString;
  }
};
