/**
 * Question List Sidebar with Drag-and-Drop Reordering (@dnd-kit).
 *
 * Implements Step 4.4:
 * - Drag-and-drop sortable list of questions
 * - Keyboard accessible reordering
 * - Status checkmarks (✓ complete, ! incomplete)
 * - Quick add question by type
 */

import React, { useState } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Plus, GripVertical, Trash2, Copy } from 'lucide-react';
import { AdminQuestionItem, QuestionType } from '../../lib/adminApi';

const TYPE_NAMES: Record<QuestionType, string> = {
  mcq: 'Trắc nghiệm',
  tf: 'Đúng / Sai',
  short_text: 'Trả lời ngắn',
  short_number: 'Điền số',
  file_upload: 'Nộp tệp tin',
};

interface SortableQuestionCardProps {
  question: AdminQuestionItem;
  index: number;
  isActive: boolean;
  onSelect: () => void;
  onDelete: () => void;
  onDuplicate: () => void;
  disabled?: boolean;
}

const SortableQuestionCard: React.FC<SortableQuestionCardProps> = ({
  question,
  index,
  isActive,
  onSelect,
  onDelete,
  onDuplicate,
  disabled = false,
}) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: question.id,
    disabled,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    zIndex: isDragging ? 50 : 'auto',
  };

  // Determine if question has complete configuration
  const isComplete = Boolean(
    question.content_md.trim() &&
      (question.type === 'mcq'
        ? question.answer_key?.correct
        : question.type === 'tf'
          ? Object.keys(question.answer_key || {}).length > 0
          : question.type === 'short_text'
            ? question.config?.grading === 'manual' || (question.answer_key?.accepted?.length ?? 0) > 0
            : question.type === 'short_number'
              ? (question.answer_key?.values?.length ?? 0) > 0
              : true)
  );

  return (
    <div
      ref={setNodeRef}
      style={style}
      onClick={onSelect}
      className={`group p-2.5 rounded-lg border transition-all cursor-pointer select-none flex items-center justify-between gap-2 ${
        isDragging
          ? 'opacity-60 bg-elevated border-brand shadow-lg'
          : isActive
            ? 'border-brand bg-brand/10 shadow-sm'
            : 'border-border-subtle bg-surface hover:border-border-strong hover:bg-elevated'
      }`}
    >
      <div className="flex items-center gap-2 min-w-0">
        {/* Drag handle */}
        {!disabled && (
          <button
            type="button"
            {...attributes}
            {...listeners}
            className="p-0.5 text-text-muted hover:text-text-primary cursor-grab active:cursor-grabbing shrink-0"
            title="Kéo thả để đổi thứ tự câu hỏi"
            onClick={(e) => e.stopPropagation()}
          >
            <GripVertical className="w-3.5 h-3.5" />
          </button>
        )}

        {/* Position number */}
        <span
          className={`font-mono font-bold text-xs shrink-0 ${
            isActive ? 'text-brand' : 'text-text-secondary'
          }`}
        >
          {String(index + 1).padStart(2, '0')}.
        </span>

        {/* Question Type & Truncated snippet */}
        <div className="min-w-0 flex flex-col">
          <span className="text-xs font-medium text-text-primary truncate">
            {TYPE_NAMES[question.type] || question.type}
          </span>
          <span className="text-[10px] text-text-muted font-mono truncate">
            {question.content_md
              ? question.content_md.replace(/[\$#\*`]/g, '').trim().substring(0, 20) || 'Chưa có nội dung'
              : 'Chưa có nội dung'}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-1.5 shrink-0">
        {/* Points badge */}
        <span className="text-[11px] font-mono text-text-muted">
          {typeof question.points === 'number' ? question.points.toFixed(1) : question.points}đ
        </span>

        {/* Completeness indicator */}
        {isComplete ? (
          <span className="w-5 h-5 rounded-full bg-brand/20 text-brand flex items-center justify-center font-bold text-[10px]" title="Đã đủ đáp án">
            ✓
          </span>
        ) : (
          <span className="w-5 h-5 rounded-full bg-status-flagged/20 text-status-flagged flex items-center justify-center font-bold text-[10px]" title="Chưa nhập đủ đáp án hoặc đề bài">
            !
          </span>
        )}

        {/* Action icons on hover */}
        {!disabled && (
          <div className="hidden group-hover:flex items-center gap-1 ml-1">
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onDuplicate();
              }}
              title="Nhân bản câu hỏi này"
              className="p-1 text-text-muted hover:text-text-primary transition-colors"
            >
              <Copy className="w-3 h-3" />
            </button>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
              title="Xóa câu hỏi này"
              className="p-1 text-text-muted hover:text-status-wrong transition-colors"
            >
              <Trash2 className="w-3 h-3" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

interface QuestionListSidebarProps {
  questions: AdminQuestionItem[];
  activeQuestionId: string | null;
  onSelectQuestion: (id: string) => void;
  onAddQuestion: (type: QuestionType) => void;
  onDeleteQuestion: (id: string) => void;
  onDuplicateQuestion: (id: string) => void;
  onReorder: (newOrderedIds: string[]) => void;
  disabled?: boolean;
}

export const QuestionListSidebar: React.FC<QuestionListSidebarProps> = ({
  questions,
  activeQuestionId,
  onSelectQuestion,
  onAddQuestion,
  onDeleteQuestion,
  onDuplicateQuestion,
  onReorder,
  disabled = false,
}) => {
  const [showAddMenu, setShowAddMenu] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 5 },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id || disabled) return;

    const oldIndex = questions.findIndex((q) => q.id === active.id);
    const newIndex = questions.findIndex((q) => q.id === over.id);

    if (oldIndex !== -1 && newIndex !== -1) {
      const reordered = arrayMove(questions, oldIndex, newIndex);
      onReorder(reordered.map((q) => q.id));
    }
  };

  return (
    <aside className="w-72 lg:w-80 border-r border-border-subtle bg-surface/40 flex flex-col shrink-0 h-full overflow-hidden select-none">
      {/* Header with Title and Add Button */}
      <div className="p-3 border-b border-border-subtle flex items-center justify-between bg-surface relative">
        <div className="flex items-center gap-2">
          <span className="font-display text-xs font-bold text-text-primary uppercase tracking-wider">
            Câu hỏi ({questions.length})
          </span>
        </div>

        {!disabled && (
          <div className="relative">
            <button
              type="button"
              onClick={() => setShowAddMenu(!showAddMenu)}
              className="px-2.5 py-1 rounded-md bg-brand/10 border border-brand/40 text-brand hover:bg-brand/20 text-xs font-medium flex items-center gap-1 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Thêm câu</span>
            </button>

            {/* Dropdown Menu for Question Types */}
            {showAddMenu && (
              <>
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setShowAddMenu(false)}
                />
                <div className="absolute right-0 mt-1 w-48 rounded-lg bg-elevated border border-border-strong shadow-xl py-1 z-50 text-xs font-mono">
                  {(['mcq', 'tf', 'short_number', 'short_text', 'file_upload'] as QuestionType[]).map(
                    (type) => (
                      <button
                        key={type}
                        type="button"
                        onClick={() => {
                          onAddQuestion(type);
                          setShowAddMenu(false);
                        }}
                        className="w-full text-left px-3 py-1.5 text-text-primary hover:bg-brand/10 hover:text-brand transition-colors flex items-center justify-between"
                      >
                        <span>{TYPE_NAMES[type]}</span>
                        <span className="text-[10px] text-text-muted uppercase">{type}</span>
                      </button>
                    )
                  )}
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* Sortable Question List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
        {questions.length === 0 ? (
          <div className="text-center py-8 px-4 text-text-muted text-xs font-mono">
            Chưa có câu hỏi nào. Nhấn "+ Thêm câu" ở trên để bắt đầu soạn đề.
          </div>
        ) : (
          <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
            <SortableContext items={questions.map((q) => q.id)} strategy={verticalListSortingStrategy}>
              {questions.map((q, idx) => (
                <SortableQuestionCard
                  key={q.id}
                  question={q}
                  index={idx}
                  isActive={activeQuestionId === q.id}
                  onSelect={() => onSelectQuestion(q.id)}
                  onDelete={() => onDeleteQuestion(q.id)}
                  onDuplicate={() => onDuplicateQuestion(q.id)}
                  disabled={disabled}
                />
              ))}
            </SortableContext>
          </DndContext>
        )}
      </div>
    </aside>
  );
};
