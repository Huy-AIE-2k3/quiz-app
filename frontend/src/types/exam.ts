/**
 * Domain types for Exams, Attempts, and Sessions matching Backend Database ERD.
 */

import { AnswerValue, QuestionType } from './question';

export type SubjectType = 'math' | 'computer_science';
export type ExamStatus = 'draft' | 'published' | 'locked' | 'archived';
export type AttemptStatus = 'in_progress' | 'submitted';

export interface Exam {
  readonly id: string;
  readonly title: string;
  readonly description_md?: string | null;
  readonly subject: SubjectType;
  readonly duration_minutes: number;
  readonly status: ExamStatus;
  readonly open_at?: string | null;
  readonly close_at?: string | null;
  readonly locked_at?: string | null;
  readonly version: number;
  readonly created_by: string;
  readonly created_at: string;
}

export interface Attempt {
  readonly id: string;
  readonly exam_id: string;
  readonly student_id: string;
  readonly status: AttemptStatus;
  readonly started_at: string;
  readonly deadline_at: string;
  readonly shuffle_seed: number;
  readonly score_total?: number | null;
  readonly submitted_at?: string | null;
  readonly created_at: string;
}

export interface AnswerRecord {
  readonly id: string;
  readonly attempt_id: string;
  readonly question_id: string;
  readonly file_id?: string | null;
  readonly value: AnswerValue;
  readonly sub_scores?: Record<string, unknown> | null;
  readonly client_seq: number;
  readonly score?: number | null;
  readonly is_correct?: boolean | null;
  readonly feedback_md?: string | null;
  readonly graded_by?: string | null;
  readonly graded_at?: string | null;
  readonly version: number;
  readonly updated_at: string;
}

export interface QuestionStatusItem {
  readonly id: string;
  readonly number: number;
  readonly status: 'unanswered' | 'answered' | 'flagged';
  readonly point: number;
  readonly question_type?: QuestionType;
}

