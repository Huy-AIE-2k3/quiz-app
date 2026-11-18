/**
 * Student API Client (Step 5.1).
 *
 * Provides methods for student exam listing and exam introduction view.
 * Guarantees zero leakage of answers, internal keys, or score configs.
 */

import { request } from './api';

export type StudentExamState =
  | 'upcoming'
  | 'open'
  | 'closed'
  | 'in_progress'
  | 'submitted'
  | 'result_available';

export interface StudentExamListItem {
  id: string;
  title: string;
  subject: string;
  duration_minutes: number;
  question_count: number;
  open_at: string | null;
  close_at: string | null;
  state: StudentExamState;
  attempt_id: string | null;
}

export interface StudentExamDetail {
  id: string;
  title: string;
  subject: string;
  description_md: string;
  duration_minutes: number;
  question_count: number;
  total_points: number | string;
  open_at: string | null;
  close_at: string | null;
  state: StudentExamState;
  attempt_id: string | null;
  can_start: boolean;
}

export const studentApi = {
  listExams: async (): Promise<StudentExamListItem[]> => {
    return request<StudentExamListItem[]>('/api/v1/student/exams');
  },

  getExam: async (examId: string): Promise<StudentExamDetail> => {
    return request<StudentExamDetail>(`/api/v1/student/exams/${examId}`);
  },
};
