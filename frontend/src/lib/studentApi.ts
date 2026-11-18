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

export interface StudentStartAttemptResponse {
  id: string;
  exam_id: string;
  status: 'in_progress' | 'submitted';
  started_at: string;
  deadline_at: string;
  submitted_at?: string | null;
  remaining_seconds: number;
  server_now: string;
}

export interface StudentAnswerItem {
  question_id: string;
  value: Record<string, unknown>;
  client_seq: number;
}

export interface StudentQuestionItem {
  id: string;
  type: 'mcq' | 'tf' | 'short_text' | 'short_number' | 'file_upload';
  content_md: string;
  points: string | number;
  config: Record<string, unknown>;
  unavailable?: boolean;
}

export interface StudentAttemptDetail {
  id: string;
  exam_id: string;
  exam_title: string;
  status: 'in_progress' | 'submitted';
  started_at: string;
  deadline_at: string;
  submitted_at?: string | null;
  remaining_seconds: number;
  server_now: string;
  questions: StudentQuestionItem[];
  answers: Record<string, StudentAnswerItem>;
}

export interface StudentSaveAnswerResponse {
  question_id: string;
  client_seq: number;
  status: 'saved' | 'ignored';
  updated_at: string;
  value: Record<string, unknown>;
}

export const studentApi = {
  listExams: async (): Promise<StudentExamListItem[]> => {
    return request<StudentExamListItem[]>('/api/v1/student/exams');
  },

  getExam: async (examId: string): Promise<StudentExamDetail> => {
    return request<StudentExamDetail>(`/api/v1/student/exams/${examId}`);
  },

  startExam: async (examId: string): Promise<StudentStartAttemptResponse> => {
    return request<StudentStartAttemptResponse>(`/api/v1/student/exams/${examId}/start`, {
      method: 'POST',
    });
  },

  getAttempt: async (attemptId: string): Promise<StudentAttemptDetail> => {
    return request<StudentAttemptDetail>(`/api/v1/student/attempts/${attemptId}`);
  },

  saveAnswer: async (
    attemptId: string,
    questionId: string,
    value: Record<string, unknown>,
    clientSeq: number
  ): Promise<StudentSaveAnswerResponse> => {
    return request<StudentSaveAnswerResponse>(
      `/api/v1/student/attempts/${attemptId}/answers/${questionId}`,
      {
        method: 'PUT',
        body: JSON.stringify({ value, client_seq: clientSeq }),
      }
    );
  },
};
