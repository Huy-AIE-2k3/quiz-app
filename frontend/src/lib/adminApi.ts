/**
 * Admin API Client services for Classes, Students, and CSV Import.
 */

import { request } from './api';

export interface ClassItem {
  id: string;
  code: string;
  name: string;
  subject: 'toan' | 'tin' | 'both';
  academic_year: number;
  is_archived: boolean;
  version: number;
  student_count: number;
  exam_count: number;
  created_at: string;
}

export interface ClassListResponse {
  items: ClassItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface StudentClassSimple {
  id: string;
  code: string;
  name: string;
}

export interface StudentItem {
  id: string;
  username: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  classes: StudentClassSimple[];
}

export interface StudentListResponse {
  items: StudentItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface CreateClassPayload {
  code: string;
  name: string;
  subject: 'toan' | 'tin' | 'both';
  academic_year: number;
}

export interface UpdateClassPayload {
  name?: string;
  subject?: 'toan' | 'tin' | 'both';
  academic_year?: number;
  is_archived?: boolean;
  version: number;
}

export interface CreateStudentPayload {
  username: string;
  full_name: string;
  password?: string;
  class_ids?: string[];
}

export interface UpdateStudentPayload {
  full_name?: string;
  is_active?: boolean;
}

export interface CsvRowDetail {
  row_number: number;
  full_name: string;
  username: string;
  class_code: string | null;
  status: 'valid' | 'error';
  errors: string[];
}

export interface StudentImportedItem {
  id: string;
  username: string;
  full_name: string;
  class_code?: string | null;
  password_plain: string;
}

export interface CsvImportResult {
  total_rows: number;
  valid_rows: number;
  error_rows: number;
  estimated_hash_seconds: number;
  can_commit: boolean;
  rows: CsvRowDetail[];
  created_count: number;
  students: StudentImportedItem[];
  csv_export_content?: string | null;
}

// Exam & Question Types for Step 4.4
export type QuestionType = 'mcq' | 'tf' | 'short_text' | 'short_number' | 'file_upload';

export interface McqOption {
  id: string;
  content_md: string;
}

export interface TfStatement {
  id: string;
  statement: string;
}

export interface AdminQuestionItem {
  id: string;
  exam_id: string;
  position: number;
  type: QuestionType;
  points: string | number;
  content_md: string;
  explanation_md?: string | null;
  config: Record<string, any>;
  answer_key: Record<string, any>;
  version: number;
  created_at: string;
}

export interface ExamDetailItem {
  id: string;
  title: string;
  description_md?: string | null;
  subject: 'math' | 'computer_science';
  duration_minutes: number;
  status: 'draft' | 'published' | 'closed' | 'archived';
  open_at?: string | null;
  close_at?: string | null;
  locked_at?: string | null;
  shuffle_questions: boolean;
  shuffle_options: boolean;
  result_visibility: 'immediate' | 'after_close' | 'manual';
  version: number;
  created_by: string;
  created_at: string;
  assigned_classes?: { id: string; name: string; code: string; is_archived: boolean }[];
  question_count?: number;
  total_points?: string | number;
  attempt_count?: number;
  questions?: AdminQuestionItem[];
}

export interface ExamValidationSummary {
  question_count: number;
  total_points: string | number;
  duration_minutes: number;
  class_count: number;
  student_count: number;
}

export interface ExamValidationResult {
  valid: boolean;
  errors: string[];
  warnings?: string[];
  summary?: ExamValidationSummary;
  // Compatibility helpers
  issues?: { code: string; message: string }[];
  question_count?: number;
  total_points?: string;
  class_count?: number;
}

export interface ExamPreviewQuestion {
  id: string;
  type: QuestionType;
  content_md: string;
  points: string;
  config: Record<string, any>;
  unavailable?: boolean;
}

export interface ExamPreviewResponse {
  id: string;
  title: string;
  description_md: string;
  subject: string;
  duration_minutes: number;
  status: 'draft' | 'published' | 'closed' | 'archived';
  shuffle_questions: boolean;
  shuffle_options: boolean;
  questions: ExamPreviewQuestion[];
}

export interface UploadAssetResponse {
  asset: string;
  markdown: string;
  file_id: string;
  size_bytes: number;
  mime_type: string;
  width?: number;
  height?: number;
}

export const adminApi = {
  // Classes
  listClasses: (params: { search?: string; limit?: number; offset?: number; is_archived?: boolean } = {}) => {
    const query = new URLSearchParams();
    if (params.search) query.set('search', params.search);
    if (params.limit !== undefined) query.set('limit', String(params.limit));
    if (params.offset !== undefined) query.set('offset', String(params.offset));
    if (params.is_archived !== undefined) query.set('is_archived', String(params.is_archived));
    const qs = query.toString();
    return request<ClassListResponse>(`/api/v1/admin/classes${qs ? `?${qs}` : ''}`);
  },

  getClass: (id: string) => {
    return request<ClassItem>(`/api/v1/admin/classes/${id}`);
  },

  createClass: (payload: CreateClassPayload) => {
    return request<ClassItem>('/api/v1/admin/classes', {
      method: 'POST',
      body: payload,
    });
  },

  updateClass: (id: string, payload: UpdateClassPayload) => {
    return request<ClassItem>(`/api/v1/admin/classes/${id}`, {
      method: 'PATCH',
      body: payload,
    });
  },

  deleteClass: (id: string) => {
    return request<{ status: string; message: string }>(`/api/v1/admin/classes/${id}`, {
      method: 'DELETE',
    });
  },

  updateClassMembers: (classId: string, userIds: string[]) => {
    return request<{ class_id: string; added: number; removed: number; total: number }>(
      `/api/v1/admin/classes/${classId}/members`,
      {
        method: 'PUT',
        body: { user_ids: userIds },
      }
    );
  },

  // Students
  listStudents: (
    params: { search?: string; class_id?: string; is_active?: boolean; limit?: number; offset?: number } = {},
    signal?: AbortSignal
  ) => {
    const query = new URLSearchParams();
    if (params.search) query.set('search', params.search);
    if (params.class_id) query.set('class_id', params.class_id);
    if (params.is_active !== undefined) query.set('is_active', String(params.is_active));
    if (params.limit !== undefined) query.set('limit', String(params.limit));
    if (params.offset !== undefined) query.set('offset', String(params.offset));
    const qs = query.toString();
    return request<StudentListResponse>(`/api/v1/admin/students${qs ? `?${qs}` : ''}`, {
      signal,
    });
  },

  createStudent: (payload: CreateStudentPayload) => {
    return request<StudentItem & { generated_password?: string }>('/api/v1/admin/students', {
      method: 'POST',
      body: payload,
    });
  },

  updateStudent: (id: string, payload: UpdateStudentPayload) => {
    return request<StudentItem>(`/api/v1/admin/students/${id}`, {
      method: 'PATCH',
      body: payload,
    });
  },

  resetStudentPassword: (id: string, password?: string) => {
    return request<{ status: string; student_id: string; generated_password?: string }>(
      `/api/v1/admin/students/${id}/reset-password`,
      {
        method: 'POST',
        body: { password },
      }
    );
  },

  // CSV Import
  importStudentsCsv: (
    file: File,
    options: { dry_run?: boolean; auto_generate_passwords?: boolean; default_class_id?: string } = {}
  ) => {
    const query = new URLSearchParams();
    query.set('dry_run', String(options.dry_run ?? true));
    query.set('auto_generate_passwords', String(options.auto_generate_passwords ?? false));
    if (options.default_class_id) {
      query.set('default_class_id', options.default_class_id);
    }

    const formData = new FormData();
    formData.append('file', file);

    return request<CsvImportResult>(`/api/v1/admin/students/import?${query.toString()}`, {
      method: 'POST',
      body: formData,
    });
  },

  // Exams (Step 4.2 & 4.4)
  getExam: (examId: string) => {
    return request<ExamDetailItem>(`/api/v1/admin/exams/${examId}`);
  },

  updateExam: (examId: string, payload: Partial<ExamDetailItem> & { version: number }) => {
    return request<ExamDetailItem>(`/api/v1/admin/exams/${examId}`, {
      method: 'PATCH',
      body: payload,
    });
  },

  validateExam: (examId: string) => {
    return request<ExamValidationResult>(`/api/v1/admin/exams/${examId}/validate`);
  },

  transitionExamStatus: (examId: string, targetStatus: string, version: number = 1) => {
    return request<ExamDetailItem>(
      `/api/v1/admin/exams/${examId}/status`,
      {
        method: 'POST',
        body: { status: targetStatus, version },
      }
    );
  },

  assignExamClasses: (examId: string, classIds: string[]) => {
    return request<ExamDetailItem>(`/api/v1/admin/exams/${examId}/classes`, {
      method: 'PUT',
      body: { class_ids: classIds },
    });
  },

  getExamPreview: (examId: string, seed?: number) => {
    const qs = seed !== undefined ? `?seed=${seed}` : '';
    return request<ExamPreviewResponse>(`/api/v1/admin/exams/${examId}/preview${qs}`);
  },

  reorderQuestions: (examId: string, orderedIds: string[]) => {
    return request<{ status: string; count: number }>(
      `/api/v1/admin/exams/${examId}/questions/reorder`,
      {
        method: 'POST',
        body: { ordered_ids: orderedIds },
      }
    );
  },

  duplicateExam: (examId: string) => {
    return request<ExamDetailItem>(`/api/v1/admin/exams/${examId}/duplicate`, {
      method: 'POST',
    });
  },

  // Questions (Step 4.1 & 4.4)
  listExamQuestions: (examId: string) => {
    return request<AdminQuestionItem[]>(`/api/v1/admin/exams/${examId}/questions`);
  },

  createQuestion: (examId: string, payload: Partial<AdminQuestionItem>) => {
    return request<AdminQuestionItem>(`/api/v1/admin/exams/${examId}/questions`, {
      method: 'POST',
      body: payload,
    });
  },

  updateQuestion: (
    questionId: string,
    payload: Partial<AdminQuestionItem> & { version?: number }
  ) => {
    return request<AdminQuestionItem>(`/api/v1/admin/questions/${questionId}`, {
      method: 'PATCH',
      body: payload,
    });
  },

  deleteQuestion: (questionId: string) => {
    return request<{ status: string; question_id: string }>(
      `/api/v1/admin/questions/${questionId}`,
      {
        method: 'DELETE',
      }
    );
  },

  // Assets (Step 4.3 & 4.4)
  uploadAsset: (examId: string, file: File) => {
    const formData = new FormData();
    formData.append('exam_id', examId);
    formData.append('file', file);
    return request<UploadAssetResponse>('/api/v1/admin/assets', {
      method: 'POST',
      body: formData,
    });
  },
};

