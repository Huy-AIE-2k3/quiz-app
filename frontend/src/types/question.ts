/**
 * Domain types for Questions and Answers matching Backend Database ERD.
 */

// 1. Dạng câu hỏi
export type QuestionType = 'mcq' | 'true_false' | 'short_answer' | 'file_upload';

// 2. Dạng 1: Trắc nghiệm 4 lựa chọn A, B, C, D
export interface MCQOption {
  readonly id: string; // e.g. "o1", "o2", "o3", "o4"
  readonly label: 'A' | 'B' | 'C' | 'D';
  readonly content_md: string;
}

export interface MCQConfig {
  readonly options: readonly MCQOption[];
  readonly shuffle_options?: boolean;
}

export interface MCQAnswerValue {
  readonly selected: string; // option id (e.g. "o1")
}

// 3. Dạng 2: Đúng / Sai
export interface TrueFalseItem {
  readonly id: 'a' | 'b' | 'c' | 'd';
  readonly content_md: string;
}

export interface TrueFalseGroupConfig {
  readonly format: 'group_4';
  readonly items: readonly TrueFalseItem[];
  readonly scoring_mode: 'per_item' | 'step_threshold';
  // Kiểu 1: Điểm riêng cho từng ý a, b, c, d
  readonly item_points?: Record<'a' | 'b' | 'c' | 'd', number>;
  // Kiểu 2: Thang điểm TNTHPT theo số lượng ý đúng
  readonly step_scores?: Record<'1' | '2' | '3' | '4', number>;
}

export interface TrueFalseSingleConfig {
  readonly format: 'single';
  readonly options: readonly [
    { readonly id: 'true'; readonly label: 'Đúng' },
    { readonly id: 'false'; readonly label: 'Sai' }
  ];
}

export type TrueFalseConfig = TrueFalseGroupConfig | TrueFalseSingleConfig;

export interface TrueFalseGroupAnswerValue {
  readonly answers: Partial<Record<'a' | 'b' | 'c' | 'd', boolean>>;
}

export interface TrueFalseSingleAnswerValue {
  readonly selected: boolean;
}

export type TrueFalseAnswerValue = TrueFalseGroupAnswerValue | TrueFalseSingleAnswerValue;

// 4. Dạng 3: Điền số (Trả lời ngắn dạng số thập phân)
export interface ShortAnswerConfig {
  readonly input_type: 'decimal';
  readonly tolerance?: number;
  readonly tolerance_type?: 'abs' | 'rel';
  readonly unit?: string; // e.g. "cm", "m/s"
}

export interface ShortAnswerValue {
  readonly value: number | string; // Số thập phân (e.g. 3.14 hoặc "3.14")
}

// 5. Dạng 4: Tự luận nộp tệp bài làm
export interface FileUploadConfig {
  readonly allowed_extensions: readonly string[]; // e.g. ["docx", "pdf", "cpp", "py", "zip"]
  readonly max_file_size_mb: number; // e.g. 10
  readonly max_files: number; // e.g. 1
  readonly rubric_md?: string;
}

export interface FileUploadAnswerValue {
  readonly file_id: string; // UUID in FILES table
  readonly file_name: string;
  readonly s3_key?: string;
  readonly file_size?: number;
}

// 6. Tổng hợp Cấu hình và Giá trị câu trả lời
export type QuestionConfig = MCQConfig | TrueFalseConfig | ShortAnswerConfig | FileUploadConfig;

export type AnswerValue =
  | MCQAnswerValue
  | TrueFalseAnswerValue
  | ShortAnswerValue
  | FileUploadAnswerValue;

// 7. Schema câu hỏi phía học sinh (Student View - Không lộ answer_key)
export interface StudentQuestion {
  readonly id: string;
  readonly position: number;
  readonly question_type: QuestionType;
  readonly content_md: string;
  readonly points: number;
  readonly config: QuestionConfig;
}
