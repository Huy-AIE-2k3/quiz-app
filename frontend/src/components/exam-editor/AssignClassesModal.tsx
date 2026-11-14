/**
 * Assign Classes Modal Component (Step 4.5 & TC-4.5-04).
 *
 * Implements:
 * - Class assignment by set (PUT /api/v1/admin/exams/:id/classes)
 * - Search and multi-select classes
 * - Content lock guard: Warning and prevention when removing classes with student attempts
 * - Clear Vietnamese error notification on 409 cannot_remove_class
 */

import React, { useState, useEffect } from 'react';
import {
  X,
  Layers,
  Search,
  Check,
  AlertCircle,
  Lock,
  Loader2,
} from 'lucide-react';
import {
  adminApi,
  ExamDetailItem,
} from '../../lib/adminApi';

export interface AssignClassesModalProps {
  readonly isOpen: boolean;
  readonly exam: ExamDetailItem;
  readonly onClose: () => void;
  readonly onUpdated: (updatedExam: ExamDetailItem) => void;
}

interface ClassItem {
  id: string;
  name: string;
  code: string;
  is_archived: boolean;
  member_count?: number;
}

export const AssignClassesModal: React.FC<AssignClassesModalProps> = ({
  isOpen,
  exam,
  onClose,
  onUpdated,
}) => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [classes, setClasses] = useState<ClassItem[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const isLocked = Boolean(exam.locked_at);
  const originalAssignedIds = new Set(exam.assigned_classes?.map((c) => c.id) || []);

  useEffect(() => {
    if (!isOpen) return;

    let isMounted = true;
    setLoading(true);
    setErrorMessage(null);
    setSearch('');
    setSelectedIds(new Set(exam.assigned_classes?.map((c) => c.id) || []));

    adminApi
      .listClasses({ limit: 100 })
      .then((data) => {
        if (!isMounted) return;
        setClasses(data.items || []);
      })
      .catch((err) => {
        if (!isMounted) return;
        setErrorMessage(err?.message || 'Không thể tải danh sách lớp học.');
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [isOpen, exam]);

  if (!isOpen) return null;

  const filteredClasses = classes.filter(
    (c) =>
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.code.toLowerCase().includes(search.toLowerCase())
  );

  const toggleClass = (classId: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(classId)) {
        next.delete(classId);
      } else {
        next.add(classId);
      }
      return next;
    });
  };

  const handleSave = async () => {
    setSaving(true);
    setErrorMessage(null);

    try {
      const updated = await adminApi.assignExamClasses(exam.id, Array.from(selectedIds));
      onUpdated(updated);
      onClose();
    } catch (err: any) {
      if (err?.code === 'cannot_remove_class' || err?.status === 409) {
        setErrorMessage(
          err.message ||
            'Không thể rút lớp khỏi đề thi vì đã có học sinh thuộc lớp này bắt đầu làm bài.'
        );
      } else {
        setErrorMessage(err?.message || 'Có lỗi xảy ra khi cập nhật phân công lớp.');
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="assign-classes-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-overlay-scrim backdrop-blur-xs animate-in fade-in duration-200"
    >
      <div className="bg-surface rounded-xl border border-border-subtle shadow-xl w-full max-w-lg max-h-[85vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="p-4 border-b border-border-subtle flex items-center justify-between bg-surface-elevated/40">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-brand" />
            <h2 id="assign-classes-title" className="font-display font-bold text-sm text-text-primary">
              Phân công Lớp học cho Đề thi
            </h2>
          </div>
          <button
            onClick={onClose}
            disabled={saving}
            className="p-1 rounded-md text-text-muted hover:text-text-primary hover:bg-surface-elevated transition-colors"
            title="Đóng"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-3 flex-1 overflow-y-auto">
          {/* Lock notice if locked */}
          {isLocked && (
            <div className="p-3 rounded-lg border border-status-review-border bg-status-review-bg text-status-review-text text-xs flex items-start gap-2">
              <Lock className="w-4 h-4 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">Đề thi đã bị khóa nội dung: </span>
                <span>
                  Bạn chỉ có thể thêm lớp mới. Không được phép rút các lớp đã có học sinh làm bài thi.
                </span>
              </div>
            </div>
          )}

          {/* Search bar */}
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-text-muted" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Tìm lớp theo tên hoặc mã lớp..."
              className="w-full h-9 pl-9 pr-3 rounded-md border border-border-subtle bg-canvas text-xs font-mono text-text-primary placeholder:text-text-muted focus:border-brand focus:outline-none"
            />
          </div>

          {/* Error Banner */}
          {errorMessage && (
            <div
              role="alert"
              className="p-3 rounded-lg border border-status-wrong-border bg-status-wrong-bg text-status-wrong-text text-xs font-mono flex items-start gap-2"
            >
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Classes Checklist */}
          {loading ? (
            <div className="py-12 flex items-center justify-center text-xs font-mono text-text-muted">
              <Loader2 className="w-4 h-4 animate-spin mr-2 text-brand" />
              <span>Đang tải danh sách lớp học...</span>
            </div>
          ) : filteredClasses.length === 0 ? (
            <div className="py-8 text-center text-xs font-mono text-text-muted">
              Không tìm thấy lớp học nào phù hợp.
            </div>
          ) : (
            <div className="divide-y divide-border-subtle border border-border-subtle rounded-lg max-h-64 overflow-y-auto bg-canvas">
              {filteredClasses.map((cls) => {
                const isSelected = selectedIds.has(cls.id);
                const wasOriginallyAssigned = originalAssignedIds.has(cls.id);
                const isRemovingLocked = isLocked && wasOriginallyAssigned && !isSelected;

                return (
                  <div
                    key={cls.id}
                    onClick={() => toggleClass(cls.id)}
                    className={`p-3 flex items-center justify-between cursor-pointer select-none transition-colors ${
                      isSelected ? 'bg-brand/5' : 'hover:bg-surface-elevated/40'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-4 h-4 rounded border flex items-center justify-center transition-colors ${
                          isSelected
                            ? 'bg-brand border-brand text-text-on-brand'
                            : 'border-border-subtle bg-surface'
                        }`}
                      >
                        {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                      </div>
                      <div>
                        <div className="flex items-center gap-1.5">
                          <span className="text-xs font-semibold text-text-primary">{cls.name}</span>
                          <span className="text-[11px] font-mono text-text-muted">({cls.code})</span>
                        </div>
                        {cls.is_archived && (
                          <span className="text-[10px] font-mono text-status-wrong-text">Đã lưu trữ</span>
                        )}
                      </div>
                    </div>

                    {isRemovingLocked && (
                      <span className="text-[10px] font-mono text-status-review-text flex items-center gap-1">
                        <Lock className="w-3 h-3" />
                        Đang bỏ chọn
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-border-subtle bg-surface-elevated/40 flex items-center justify-between">
          <span className="text-xs font-mono text-text-muted">
            Đã chọn {selectedIds.size} lớp
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={saving}
              className="px-3 py-1.5 rounded-md border border-border-subtle text-xs font-semibold text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors"
            >
              Hủy
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={saving || loading}
              className="px-4 py-1.5 rounded-md bg-brand text-xs font-semibold text-text-on-brand hover:brightness-110 active:brightness-95 transition-all flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
            >
              {saving ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Đang lưu...</span>
                </>
              ) : (
                <span>Lưu thay đổi</span>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
