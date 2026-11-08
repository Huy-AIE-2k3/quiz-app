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
};
