/**
 * Full Exam Editor Page (Step 4.4 & SC-12).
 *
 * Implements:
 * - 3-column split workspace: Question list (@dnd-kit) | Form editor | Live preview
 * - Autosave debounce 1.5s with Vietnamese IME composition pause (TC-4.4-03, TC-4.4-06)
 * - Real-time student-faithful live preview (TC-4.4-02)
 * - LaTeX formula error detection with inline banner and error counter (TC-4.4-08)
 * - Clipboard image paste (Ctrl+V) with client compression & upload progress (TC-4.4-04)
 * - Drag-and-drop sortable questions (TC-4.4-05)
 * - Version conflict 409 modal with clipboard backup (TC-4.4-07)
 * - Read-only mode for locked exams with duplicate action (TC-4.4-09)
 * - Live test box for Short Number evaluation (TC-4.4-10)
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Eye,
  Check,
  AlertTriangle,
  Lock,
  Copy,
  Image as ImageIcon,
  Loader2,
} from 'lucide-react';

import {
  adminApi,
  AdminQuestionItem,
  ExamDetailItem,
  QuestionType,
} from '../../lib/adminApi';
import { SaveIndicator, SaveStatus } from '../../components/exam/SaveIndicator';
import { useToast } from '../../components/ui/useToast';
import { LatexToolbar } from '../../components/exam-editor/LatexToolbar';
import { QuestionListSidebar } from '../../components/exam-editor/QuestionListSidebar';
import { LivePreviewPanel } from '../../components/exam-editor/LivePreviewPanel';
import { VersionConflictModal } from '../../components/exam-editor/VersionConflictModal';
import { McqEditor } from '../../components/exam-editor/types/McqEditor';
import { TfEditor } from '../../components/exam-editor/types/TfEditor';
import { ShortTextEditor } from '../../components/exam-editor/types/ShortTextEditor';
import { ShortNumberEditor } from '../../components/exam-editor/types/ShortNumberEditor';
import { FileUploadEditor } from '../../components/exam-editor/types/FileUploadEditor';
import { compressImageForUpload } from '../../lib/imageCompression';

export const AdminExamEditorPage: React.FC = () => {
  const { examId } = useParams<{ examId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const toastRef = useRef(toast);
  toastRef.current = toast;

  const [loading, setLoading] = useState(true);
  const [exam, setExam] = useState<ExamDetailItem | null>(null);
  const [questions, setQuestions] = useState<AdminQuestionItem[]>([]);
  const [activeQuestionId, setActiveQuestionId] = useState<string | null>(null);

  // Autosave and network states
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('saved');
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const isComposingRef = useRef(false); // Vietnamese IME Telex flag (TC-4.4-03)
  const saveTimerRef = useRef<NodeJS.Timeout | null>(null);
  const pendingSavePayloadRef = useRef<{ id: string; payload: any } | null>(null);

  // Asset upload states (TC-4.4-04)
  const [isUploadingImage, setIsUploadingImage] = useState(false);
  const [uploadProgressText, setUploadProgressText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Version conflict modal (TC-4.4-07)
  const [conflictModalOpen, setConflictModalOpen] = useState(false);

  // LaTeX formula error count (TC-4.4-08)
  const [formulaErrorCount, setFormulaErrorCount] = useState(0);

  // Active question derived object
  const activeQuestion = questions.find((q) => q.id === activeQuestionId) || null;
  const isLocked = Boolean(exam?.locked_at);

  // Load exam and question details
  const fetchExamData = useCallback(async () => {
    if (!examId) return;
    try {
      setLoading(true);
      const [examData, questionsData] = await Promise.all([
        adminApi.getExam(examId),
        adminApi.listExamQuestions(examId),
      ]);
      setExam(examData);
      setQuestions(questionsData);
      setActiveQuestionId((prev) => prev || (questionsData.length > 0 ? questionsData[0].id : null));
    } catch (err: any) {
      toastRef.current.error(err?.message || 'Không thể tải thông tin đề thi.', 'Lỗi tải đề thi');
    } finally {
      setLoading(false);
    }
  }, [examId]);

  useEffect(() => {
    fetchExamData();
  }, [fetchExamData]);

  // Execute actual question update API call
  const performSave = useCallback(
    async (questionId: string, payload: Partial<AdminQuestionItem>) => {
      if (!examId || isLocked) return;

      // TC-4.4-06: Guard against offline state
      if (typeof window !== 'undefined' && !window.navigator.onLine) {
        setSaveStatus('offline');
        pendingSavePayloadRef.current = { id: questionId, payload };
        return;
      }

      setSaveStatus('saving');
      try {
        const updated = await adminApi.updateQuestion(questionId, payload);
        setQuestions((prev) =>
          prev.map((q) => (q.id === questionId ? { ...q, ...updated } : q))
        );
        setSaveStatus('saved');
        setHasUnsavedChanges(false);
        pendingSavePayloadRef.current = null;
      } catch (err: any) {
        if (err?.code === 'version_conflict' || err?.status === 409) {
          // TC-4.4-07: Show conflict resolution modal
          setConflictModalOpen(true);
          setSaveStatus('error');
        } else {
          setSaveStatus('error');
          toastRef.current.error(err?.message || 'Không thể lưu thay đổi câu hỏi.', 'Lỗi tự động lưu');
        }
      }
    },
    [examId, isLocked]
  );

  // Debounced autosave scheduler with IME composition safety (TC-4.4-03)
  const scheduleAutosave = useCallback(
    (questionId: string, payload: Partial<AdminQuestionItem>) => {
      setHasUnsavedChanges(true);
      pendingSavePayloadRef.current = { id: questionId, payload };

      if (saveTimerRef.current) {
        clearTimeout(saveTimerRef.current);
      }

      saveTimerRef.current = setTimeout(() => {
        // If user is actively typing Vietnamese accented characters, postpone timer
        if (isComposingRef.current) {
          scheduleAutosave(questionId, payload);
          return;
        }
        performSave(questionId, payload);
      }, 1500); // 1.5s debounce
    },
    [performSave]
  );

  // Auto-flush pending saves when network comes back online (TC-4.4-06)
  useEffect(() => {
    const handleOnline = () => {
      if (pendingSavePayloadRef.current) {
        const { id, payload } = pendingSavePayloadRef.current;
        performSave(id, payload);
      }
    };
    const handleOffline = () => {
      if (hasUnsavedChanges) {
        setSaveStatus('offline');
      }
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [hasUnsavedChanges, performSave]);

  // Warn user before leaving if unsaved changes exist
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = 'Bạn có thay đổi chưa được lưu. Bạn có chắc muốn rời đi?';
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasUnsavedChanges]);

  // Update question locally and trigger autosave
  const updateActiveQuestion = (field: keyof AdminQuestionItem, value: any) => {
    if (!activeQuestion || isLocked) return;

    const updated = { ...activeQuestion, [field]: value };
    setQuestions((prev) => prev.map((q) => (q.id === activeQuestion.id ? updated : q)));

    scheduleAutosave(activeQuestion.id, {
      [field]: value,
      version: activeQuestion.version,
    });
  };

  // Drag and drop question reorder (TC-4.4-05)
  const handleReorderQuestions = async (newOrderedIds: string[]) => {
    if (!examId || isLocked) return;
    const previousOrder = questions;

    // Optimistically update order locally
    const reordered = newOrderedIds
      .map((id, idx) => {
        const q = questions.find((item) => item.id === id);
        return q ? { ...q, position: idx + 1 } : null;
      })
      .filter(Boolean) as AdminQuestionItem[];

    setQuestions(reordered);

    try {
      await adminApi.reorderQuestions(examId, newOrderedIds);
      toast.success('Thứ tự các câu hỏi đã được lưu.', 'Đã cập nhật thứ tự');
    } catch (err: any) {
      // Revert on failure
      setQuestions(previousOrder);
      toast.error(err?.message || 'Không thể lưu thứ tự mới. Đã hoàn tác.', 'Lỗi sắp xếp câu hỏi');
    }
  };

  // Add a new question
  const handleAddQuestion = async (type: QuestionType) => {
    if (!examId || isLocked) return;

    try {
      const position = questions.length + 1;
      const initialConfig: Record<string, any> =
        type === 'mcq'
          ? {
              options: [
                { id: 'o1', content_md: '' },
                { id: 'o2', content_md: '' },
                { id: 'o3', content_md: '' },
                { id: 'o4', content_md: '' },
              ],
            }
          : type === 'tf'
            ? {
                statements: [
                  { id: 's1', statement: '' },
                  { id: 's2', statement: '' },
                  { id: 's3', statement: '' },
                  { id: 's4', statement: '' },
                ],
                scoring: 'thpt',
              }
            : type === 'short_text'
              ? { grading: 'auto', case_sensitive: false, ignore_accents: false, review_wrong: false }
              : type === 'short_number'
                ? { tolerance: 0.01, tolerance_type: 'abs' }
                : { max_files: 1, max_mb: 5, allowed_ext: ['pdf', 'png', 'jpg'] };

      const initialAnswerKey: Record<string, any> =
        type === 'mcq'
          ? { correct: 'o1' }
          : type === 'tf'
            ? { s1: true, s2: false, s3: true, s4: false }
            : type === 'short_text'
              ? { accepted: [] }
              : type === 'short_number'
                ? { values: [] }
                : {};

      const created = await adminApi.createQuestion(examId, {
        type,
        position,
        points: 1.0,
        content_md: '',
        explanation_md: '',
        config: initialConfig,
        answer_key: initialAnswerKey,
      });

      setQuestions((prev) => [...prev, created]);
      setActiveQuestionId(created.id);
      toast.success(`Đã thêm câu hỏi số ${position} (${type}).`, 'Đã tạo câu hỏi');
    } catch (err: any) {
      toast.error(err?.message || 'Không thể tạo câu hỏi mới.', 'Lỗi thêm câu hỏi');
    }
  };

  // Delete question
  const handleDeleteQuestion = async (questionId: string) => {
    if (isLocked) return;
    try {
      await adminApi.deleteQuestion(questionId);
      const remaining = questions.filter((q) => q.id !== questionId);
      setQuestions(remaining);
      if (activeQuestionId === questionId) {
        setActiveQuestionId(remaining[0]?.id || null);
      }
      toast.success('Câu hỏi đã được xóa khỏi đề thi.', 'Đã xóa câu hỏi');
    } catch (err: any) {
      toast.error(err?.message || 'Không thể xóa câu hỏi.', 'Lỗi xóa câu hỏi');
    }
  };

  // Duplicate question
  const handleDuplicateQuestion = async (questionId: string) => {
    if (!examId || isLocked) return;
    const target = questions.find((q) => q.id === questionId);
    if (!target) return;

    try {
      const position = questions.length + 1;
      const created = await adminApi.createQuestion(examId, {
        type: target.type,
        position,
        points: target.points,
        content_md: target.content_md,
        explanation_md: target.explanation_md,
        config: target.config,
        answer_key: target.answer_key,
      });

      setQuestions((prev) => [...prev, created]);
      setActiveQuestionId(created.id);
      toast.success(`Đã tạo bản sao câu hỏi tại vị trí ${position}.`, 'Đã nhân bản câu hỏi');
    } catch (err: any) {
      toast.error(err?.message || 'Không thể sao chép câu hỏi.', 'Lỗi nhân bản');
    }
  };

  // Duplicate exam (TC-4.4-09: for locked exams)
  const handleDuplicateExam = async () => {
    if (!examId) return;
    try {
      const duplicated = await adminApi.duplicateExam(examId);
      toast.success('Đã tạo bản sao mới ở trạng thái bản nháp.', 'Đã nhân bản đề thi');
      navigate(`/a/exams/${duplicated.id}/edit`);
    } catch (err: any) {
      toast.error(err?.message || 'Không thể tạo bản sao đề thi.', 'Lỗi nhân bản đề thi');
    }
  };

  // Image upload and paste handler (TC-4.4-04)
  const processImageUpload = async (imageFile: File) => {
    if (!examId || isLocked) return;

    try {
      setIsUploadingImage(true);
      setUploadProgressText('Đang nén ảnh...');

      // 1. Client-side compression
      const compressed = await compressImageForUpload(imageFile);

      // 2. Upload to server
      setUploadProgressText('Đang tải lên hệ thống...');
      const assetResp = await adminApi.uploadAsset(examId, compressed);

      // 3. Insert markdown tag into content_md at cursor
      const textarea = textareaRef.current;
      const insertMarkdown = assetResp.markdown || `![](asset:${assetResp.file_id})`;

      if (textarea && activeQuestion) {
        const start = textarea.selectionStart ?? textarea.value.length;
        const end = textarea.selectionEnd ?? textarea.value.length;
        const original = activeQuestion.content_md;
        const updated = original.substring(0, start) + `\n${insertMarkdown}\n` + original.substring(end);
        updateActiveQuestion('content_md', updated);
      } else if (activeQuestion) {
        updateActiveQuestion('content_md', `${activeQuestion.content_md}\n${insertMarkdown}\n`);
      }

      toast.success('Ảnh đã được chèn vào nội dung câu hỏi.', 'Đã tải ảnh thành công');
    } catch (err: any) {
      toast.error(err?.message || 'Không thể tải ảnh lên.', 'Lỗi tải ảnh');
    } finally {
      setIsUploadingImage(false);
      setUploadProgressText('');
    }
  };

  // Clipboard paste handler on textarea (TC-4.4-04)
  const handleTextareaPaste = (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    if (isLocked) return;
    const items = e.clipboardData?.items;
    if (!items) return;

    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item.type.indexOf('image') !== -1) {
        const file = item.getAsFile();
        if (file) {
          e.preventDefault();
          processImageUpload(file);
          return;
        }
      }
    }
  };

  // Exam header update (Title, duration)
  const handleUpdateExamTitle = async (title: string) => {
    if (!examId || !exam) return;
    setExam((prev) => (prev ? { ...prev, title } : null));
    try {
      await adminApi.updateExam(examId, { title, version: exam.version });
    } catch {
      // Ignore background title update errors
    }
  };

  const handleUpdateDuration = async (minutes: number) => {
    if (!examId || !exam || isLocked) return;
    const validMinutes = Math.min(300, Math.max(1, minutes));
    setExam((prev) => (prev ? { ...prev, duration_minutes: validMinutes } : null));
    try {
      await adminApi.updateExam(examId, { duration_minutes: validMinutes, version: exam.version });
    } catch {
      // Ignore background duration update errors
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-canvas flex items-center justify-center text-text-muted font-mono text-xs">
        <Loader2 className="w-5 h-5 animate-spin mr-2 text-brand" />
        <span>Đang tải thông tin đề thi và câu hỏi...</span>
      </div>
    );
  }

  if (!exam) {
    return (
      <div className="min-h-screen bg-canvas flex flex-col items-center justify-center text-text-primary text-xs font-mono gap-3">
        <span>Không tìm thấy đề thi hoặc đề thi đã bị xóa.</span>
        <button
          onClick={() => navigate('/a/exams')}
          className="px-3 py-1.5 rounded bg-brand text-canvas font-bold"
        >
          Quay lại danh sách đề
        </button>
      </div>
    );
  }

  return (
    <div className="bg-canvas text-text-primary font-sans h-screen flex flex-col antialiased overflow-hidden">
      {/* ================= TOP CONFIGURATION BAR ================= */}
      <header className="shrink-0 bg-surface border-b border-border-subtle px-6 py-2.5 flex flex-wrap items-center justify-between gap-4 z-30 select-none">
        {/* Brand + Breadcrumb + Title Input */}
        <div className="flex items-center gap-3 flex-1 min-w-[280px]">
          <Link
            to="/a/exams"
            className="flex items-center gap-1.5 text-xs text-text-secondary hover:text-text-primary transition-colors shrink-0"
            title="Quay lại danh sách đề thi"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="font-mono">Đề thi</span>
          </Link>
          <span className="text-text-muted font-mono">/</span>
          <input
            type="text"
            value={exam.title}
            disabled={isLocked}
            onChange={(e) => handleUpdateExamTitle(e.target.value)}
            placeholder="Nhập tên đề thi..."
            className="w-full max-w-md h-8 px-3 bg-canvas rounded-md border border-border-subtle text-xs font-semibold text-text-primary focus:border-brand focus:outline-none disabled:opacity-75"
          />
        </div>

        {/* Configuration Items: Duration, Save Indicator, KaTeX Error Counter, Actions */}
        <div className="flex items-center gap-3 flex-wrap">
          {/* Duration in Minutes */}
          <div className="flex items-center gap-1.5 bg-canvas px-3 py-1 rounded-md border border-border-subtle text-xs font-mono">
            <span className="text-text-muted">Thời lượng:</span>
            <input
              type="number"
              min="1"
              max="300"
              disabled={isLocked}
              value={exam.duration_minutes}
              onChange={(e) => handleUpdateDuration(parseInt(e.target.value) || 45)}
              className="w-12 bg-transparent text-xs font-semibold text-brand text-right focus:outline-none"
            />
            <span className="text-text-muted">phút</span>
          </div>

          {/* Save Status Indicator */}
          <div className="px-2">
            <SaveIndicator status={saveStatus} onRetry={() => performSave(activeQuestion?.id || '', {})} />
          </div>

          {/* Formula Error Counter Badge (TC-4.4-08) */}
          {formulaErrorCount > 0 && (
            <div className="flex items-center gap-1 px-2.5 py-1 rounded bg-status-wrong/10 border border-status-wrong/30 text-status-wrong text-xs font-mono font-semibold">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>{formulaErrorCount} lỗi công thức</span>
            </div>
          )}

          {/* Preview Button */}
          <Link
            to={`/a/exams/${exam.id}/preview`}
            className="h-8 px-3 rounded-md border border-border-subtle bg-elevated hover:bg-border-subtle text-text-secondary hover:text-text-primary text-xs font-medium flex items-center gap-1.5 transition-colors"
          >
            <Eye className="w-3.5 h-3.5" />
            <span>Xem trước đề</span>
          </Link>

          {/* Publish / Status Badge */}
          {isLocked ? (
            <div className="h-8 px-3 rounded-md bg-status-flagged/10 border border-status-flagged/30 text-status-flagged text-xs font-mono font-semibold flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5" />
              <span>Đang khóa (Có thí sinh)</span>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => navigate(`/a/exams/${exam.id}/preview`)}
              className="h-8 px-4 rounded-md bg-brand hover:bg-brand-hover text-canvas font-semibold text-xs flex items-center gap-1.5 transition-colors shadow-sm"
            >
              <Check className="w-3.5 h-3.5" />
              <span>Xuất bản</span>
            </button>
          )}
        </div>
      </header>

      {/* Locked Exam Alert Banner (TC-4.4-09) */}
      {isLocked && (
        <div className="bg-status-flagged/10 border-b border-status-flagged/30 px-6 py-2 flex items-center justify-between text-xs text-status-flagged">
          <div className="flex items-center gap-2 font-mono">
            <Lock className="w-4 h-4 shrink-0" />
            <span>
              Đề thi đã có học sinh làm bài và đang bị khóa nội dung. Không thể sửa điểm hoặc câu hỏi.
            </span>
          </div>
          <button
            type="button"
            onClick={handleDuplicateExam}
            className="px-3 py-1 rounded bg-status-flagged text-canvas font-bold text-xs flex items-center gap-1 hover:opacity-90 transition-opacity"
          >
            <Copy className="w-3.5 h-3.5" />
            <span>Nhân bản để chỉnh sửa</span>
          </button>
        </div>
      )}

      {/* ================= MAIN 3-COLUMN SPLIT WORKSPACE ================= */}
      <main className="flex-1 flex overflow-hidden">
        {/* CỘT TRÁI: DANH SÁCH CÂU HỎI (Kéo thả @dnd-kit) */}
        <QuestionListSidebar
          questions={questions}
          activeQuestionId={activeQuestionId}
          onSelectQuestion={setActiveQuestionId}
          onAddQuestion={handleAddQuestion}
          onDeleteQuestion={handleDeleteQuestion}
          onDuplicateQuestion={handleDuplicateQuestion}
          onReorder={handleReorderQuestions}
          disabled={isLocked}
        />

        {/* CỘT GIỮA: FORM SOẠN THẢO CÂU HỎI */}
        <section className="flex-1 overflow-y-auto p-6 space-y-6">
          {activeQuestion ? (
            <>
              {/* Question Configuration Header: Type & Points */}
              <div className="p-4 rounded-xl bg-surface border border-border-subtle flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <span className="font-display font-bold text-base text-text-primary">
                    Câu {String(activeQuestion.position).padStart(2, '0')}
                  </span>
                  <select
                    disabled={isLocked}
                    value={activeQuestion.type}
                    onChange={(e) => updateActiveQuestion('type', e.target.value as QuestionType)}
                    className="h-8 px-2.5 bg-canvas border border-border-subtle rounded-md text-xs font-mono text-text-primary focus:border-brand focus:outline-none"
                  >
                    <option value="mcq">Trắc nghiệm nhiều lựa chọn</option>
                    <option value="tf">Đúng / Sai theo mệnh đề</option>
                    <option value="short_number">Điền số (Trả lời ngắn số)</option>
                    <option value="short_text">Trả lời ngắn (Văn bản)</option>
                    <option value="file_upload">Nộp bài dạng tệp tin</option>
                  </select>
                </div>

                <div className="flex items-center gap-2 text-xs font-mono">
                  <span className="text-text-secondary">Điểm số:</span>
                  <input
                    type="number"
                    step="0.1"
                    min="0.1"
                    max="100"
                    disabled={isLocked}
                    value={activeQuestion.points}
                    onChange={(e) => updateActiveQuestion('points', parseFloat(e.target.value) || 1.0)}
                    className="w-16 h-8 px-2 bg-canvas border border-border-subtle rounded-md text-xs font-semibold text-brand text-right focus:border-brand focus:outline-none"
                  />
                  <span className="text-text-muted">điểm</span>
                </div>
              </div>

              {/* Question Content Input & Image Upload */}
              <div className="p-5 rounded-xl bg-surface border border-border-subtle space-y-3">
                <div className="flex items-center justify-between">
                  <label className="block text-xs font-bold text-text-secondary uppercase tracking-wider font-mono">
                    Nội dung câu hỏi (Markdown &amp; LaTeX):
                  </label>
                  <div className="flex items-center gap-2">
                    {/* Image Paste / Upload helper */}
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/png,image/jpeg,image/webp"
                      className="hidden"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) processImageUpload(file);
                      }}
                    />
                    {!isLocked && (
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isUploadingImage}
                        className="px-2.5 py-1 rounded bg-elevated hover:bg-border-subtle border border-border-subtle text-xs font-mono text-text-secondary hover:text-text-primary flex items-center gap-1.5 transition-colors"
                      >
                        {isUploadingImage ? (
                          <>
                            <Loader2 className="w-3.5 h-3.5 animate-spin text-brand" />
                            <span>{uploadProgressText}</span>
                          </>
                        ) : (
                          <>
                            <ImageIcon className="w-3.5 h-3.5 text-brand" />
                            <span>Chèn ảnh (Ctrl+V)</span>
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>

                {/* LaTeX Toolbar */}
                <LatexToolbar
                  textareaRef={textareaRef}
                  value={activeQuestion.content_md}
                  onChange={(val) => updateActiveQuestion('content_md', val)}
                  disabled={isLocked}
                />

                {/* Question Textarea with Vietnamese IME & Paste listeners (TC-4.4-03, TC-4.4-04) */}
                <textarea
                  ref={textareaRef}
                  rows={6}
                  disabled={isLocked}
                  value={activeQuestion.content_md}
                  onPaste={handleTextareaPaste}
                  onCompositionStart={() => {
                    isComposingRef.current = true;
                  }}
                  onCompositionEnd={() => {
                    isComposingRef.current = false;
                    // Trigger autosave after composition completes
                    scheduleAutosave(activeQuestion.id, {
                      content_md: activeQuestion.content_md,
                      version: activeQuestion.version,
                    });
                  }}
                  onChange={(e) => updateActiveQuestion('content_md', e.target.value)}
                  placeholder="Nhập đề bài ở đây... Ví dụ: Cho hàm số $f(x) = \int_0^x \sqrt{t^2+1}dt$. Tính giá trị của $f'(1)$..."
                  className="w-full p-3.5 bg-canvas border border-border-subtle rounded-b-lg text-xs font-sans text-text-primary placeholder:text-text-muted focus:border-brand focus:outline-none leading-relaxed font-mono"
                />
              </div>

              {/* Type-Specific Editor */}
              <div className="p-5 rounded-xl bg-surface border border-border-subtle space-y-4">
                {activeQuestion.type === 'mcq' && (
                  <McqEditor
                    options={activeQuestion.config?.options || []}
                    correctOptionId={activeQuestion.answer_key?.correct || 'o1'}
                    onChangeOptions={(opts) =>
                      updateActiveQuestion('config', { ...activeQuestion.config, options: opts })
                    }
                    onChangeCorrect={(correctId) =>
                      updateActiveQuestion('answer_key', { correct: correctId })
                    }
                    disabled={isLocked}
                  />
                )}

                {activeQuestion.type === 'tf' && (
                  <TfEditor
                    statements={activeQuestion.config?.statements || []}
                    answerKey={activeQuestion.answer_key || {}}
                    scoringMode={activeQuestion.config?.scoring || 'thpt'}
                    onChangeStatements={(stmts) =>
                      updateActiveQuestion('config', { ...activeQuestion.config, statements: stmts })
                    }
                    onChangeAnswerKey={(key) => updateActiveQuestion('answer_key', key)}
                    onChangeScoringMode={(mode) =>
                      updateActiveQuestion('config', { ...activeQuestion.config, scoring: mode })
                    }
                    disabled={isLocked}
                  />
                )}

                {activeQuestion.type === 'short_text' && (
                  <ShortTextEditor
                    accepted={activeQuestion.answer_key?.accepted || []}
                    grading={activeQuestion.config?.grading || 'auto'}
                    caseSensitive={activeQuestion.config?.case_sensitive || false}
                    ignoreAccents={activeQuestion.config?.ignore_accents || false}
                    reviewWrong={activeQuestion.config?.review_wrong || false}
                    onChangeAccepted={(acc) =>
                      updateActiveQuestion('answer_key', { accepted: acc })
                    }
                    onChangeGrading={(g) =>
                      updateActiveQuestion('config', { ...activeQuestion.config, grading: g })
                    }
                    onChangeCaseSensitive={(cs) =>
                      updateActiveQuestion('config', { ...activeQuestion.config, case_sensitive: cs })
                    }
                    onChangeIgnoreAccents={(ia) =>
                      updateActiveQuestion('config', { ...activeQuestion.config, ignore_accents: ia })
                    }
                    onChangeReviewWrong={(rw) =>
                      updateActiveQuestion('config', { ...activeQuestion.config, review_wrong: rw })
                    }
                    disabled={isLocked}
                  />
                )}

                {activeQuestion.type === 'short_number' && (
                  <ShortNumberEditor
                    values={activeQuestion.answer_key?.values || []}
                    tolerance={activeQuestion.config?.tolerance ?? 0.01}
                    toleranceType={activeQuestion.config?.tolerance_type || 'abs'}
                    onChangeValues={(vals) =>
                      updateActiveQuestion('answer_key', { values: vals })
                    }
                    onChangeTolerance={(tol) =>
                      updateActiveQuestion('config', { ...activeQuestion.config, tolerance: tol })
                    }
                    onChangeToleranceType={(tt) =>
                      updateActiveQuestion('config', { ...activeQuestion.config, tolerance_type: tt })
                    }
                    disabled={isLocked}
                  />
                )}

                {activeQuestion.type === 'file_upload' && (
                  <FileUploadEditor
                    maxFiles={activeQuestion.config?.max_files || 1}
                    maxMb={activeQuestion.config?.max_mb || 5}
                    allowedExt={activeQuestion.config?.allowed_ext || ['pdf', 'png', 'jpg']}
                    onChangeMaxFiles={(mf) =>
                      updateActiveQuestion('config', { ...activeQuestion.config, max_files: mf })
                    }
                    onChangeMaxMb={(mb) =>
                      updateActiveQuestion('config', { ...activeQuestion.config, max_mb: mb })
                    }
                    onChangeAllowedExt={(ext) =>
                      updateActiveQuestion('config', { ...activeQuestion.config, allowed_ext: ext })
                    }
                    disabled={isLocked}
                  />
                )}
              </div>

              {/* Explanation Markdown (Lời giải chi tiết) */}
              <div className="p-5 rounded-xl bg-surface border border-border-subtle space-y-3">
                <label className="block text-xs font-bold text-text-secondary uppercase tracking-wider font-mono">
                  Lời giải chi tiết / Hướng dẫn giải (Hiển thị sau khi công bố kết quả):
                </label>
                <textarea
                  rows={4}
                  disabled={isLocked}
                  value={activeQuestion.explanation_md || ''}
                  onChange={(e) => updateActiveQuestion('explanation_md', e.target.value)}
                  placeholder="Nhập lời giải hoặc barem chấm điểm tại đây (hỗ trợ công thức LaTeX)..."
                  className="w-full p-3.5 bg-canvas border border-border-subtle rounded-lg text-xs font-sans text-text-primary placeholder:text-text-muted focus:border-brand focus:outline-none leading-relaxed font-mono"
                />
              </div>
            </>
          ) : (
            <div className="h-full flex items-center justify-center text-text-muted font-mono text-xs">
              Chọn hoặc tạo câu hỏi để bắt đầu soạn thảo.
            </div>
          )}
        </section>

        {/* CỘT PHẢI: XEM TRƯỚC TRỰC TIẾP (Live Preview - Giao diện học sinh) */}
        <LivePreviewPanel
          question={activeQuestion}
          positionNumber={activeQuestion?.position || 1}
          onFormulaErrorsChange={setFormulaErrorCount}
        />
      </main>

      {/* Version Conflict Modal (TC-4.4-07) */}
      <VersionConflictModal
        isOpen={conflictModalOpen}
        localContent={activeQuestion?.content_md || ''}
        onClose={() => setConflictModalOpen(false)}
        onReload={() => {
          setConflictModalOpen(false);
          fetchExamData();
        }}
        onOverwrite={() => {
          setConflictModalOpen(false);
          // Refetch to get latest version number then save
          adminApi.getExam(examId!).then(() => {
            if (activeQuestion) {
              performSave(activeQuestion.id, {
                content_md: activeQuestion.content_md,
                config: activeQuestion.config,
                answer_key: activeQuestion.answer_key,
              });
            }
          });
        }}
      />
    </div>
  );
};
