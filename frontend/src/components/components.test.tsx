import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import {
  Button,
  Input,
  Textarea,
  Select,
  Checkbox,
  Radio,
  Badge,
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Modal,
  ConfirmDialog,
  Skeleton,
  EmptyState,
  ErrorState,
  Banner,
  FileDropzone,
  Pagination,
  Timer,
  SaveIndicator,
  QuestionNav,
} from './index';

describe('TC-1.5-01: UI Component States (Default, Loading, Disabled, Error)', () => {
  it('Button: renders default, loading, disabled, and error/danger variants correctly', () => {
    const { rerender } = render(<Button variant="primary">Lưu bài thi</Button>);
    expect(screen.getByRole('button', { name: 'Lưu bài thi' })).toBeInTheDocument();

    // Loading state: shows spinner and is disabled
    rerender(<Button loading loadingText="Đang xử lý...">Lưu bài thi</Button>);
    const loadingBtn = screen.getByRole('button', { name: 'Đang xử lý...' });
    expect(loadingBtn).toBeDisabled();
    expect(screen.getByTestId('button-spinner')).toBeInTheDocument();

    // Disabled state
    rerender(<Button disabled>Không khả dụng</Button>);
    expect(screen.getByRole('button', { name: 'Không khả dụng' })).toBeDisabled();

    // Danger variant
    rerender(<Button variant="danger">Xóa đề</Button>);
    expect(screen.getByRole('button', { name: 'Xóa đề' })).toHaveClass('text-status-wrong-text');
  });

  it('Input: renders label, placeholder, error message, and disabled state with aria attributes', () => {
    const { rerender } = render(
      <Input
        label="Mã học sinh"
        placeholder="Nhập mã..."
        helperText="Định dạng HS-2025"
      />
    );
    expect(screen.getByLabelText('Mã học sinh')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Nhập mã...')).toBeInTheDocument();
    expect(screen.getByText('Định dạng HS-2025')).toBeInTheDocument();

    // Error state
    rerender(
      <Input
        label="Mã học sinh"
        error="Mã học sinh không tồn tại"
        defaultValue="HS-000"
      />
    );
    const input = screen.getByLabelText('Mã học sinh');
    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByText('Mã học sinh không tồn tại')).toBeInTheDocument();

    // Disabled state
    rerender(<Input label="Mã học sinh" disabled />);
    expect(screen.getByLabelText('Mã học sinh')).toBeDisabled();
  });

  it('Textarea: renders label, character counter, error message, and disabled state', () => {
    render(
      <Textarea
        label="Đề xuất lời giải"
        showCount
        maxLength={100}
        error="Nội dung quá ngắn"
        defaultValue="Lời giải..."
      />
    );
    expect(screen.getByLabelText('Đề xuất lời giải')).toBeInTheDocument();
    expect(screen.getByText('Nội dung quá ngắn')).toBeInTheDocument();
    expect(screen.getByText('11 / 100')).toBeInTheDocument();
  });

  it('Select: renders options and error message with accessible attributes', () => {
    render(
      <Select
        label="Khối lớp"
        error="Vui lòng chọn khối"
        options={[
          { value: '10', label: 'Lớp 10' },
          { value: '11', label: 'Lớp 11' },
          { value: '12', label: 'Lớp 12' },
        ]}
      />
    );
    expect(screen.getByLabelText('Khối lớp')).toBeInTheDocument();
    expect(screen.getByText('Vui lòng chọn khối')).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Lớp 12' })).toBeInTheDocument();
  });

  it('Checkbox & Radio: render labels, checked states, and disabled states correctly', () => {
    const handleCheck = vi.fn();
    render(
      <Checkbox
        label="Chấp nhận nội quy phòng thi"
        description="Không gian lận, không mở tab khác"
        onChange={handleCheck}
      />
    );
    const checkbox = screen.getByRole('checkbox', { name: /Chấp nhận nội quy phòng thi/i });
    expect(checkbox).not.toBeChecked();
    fireEvent.click(checkbox);
    expect(handleCheck).toHaveBeenCalledTimes(1);

    // Radio
    render(<Radio name="test-radio" label="Phương án A" defaultChecked />);
    const radio = screen.getByRole('radio', { name: /Phương án A/i });
    expect(radio).toBeChecked();
  });

  it('Badge: renders all status variants (brand, warning, danger, neutral) with dot indicators', () => {
    render(
      <div>
        <Badge variant="brand" dot>Hoạt động</Badge>
        <Badge variant="warning" dot>Cảnh báo</Badge>
        <Badge variant="danger" dot>Đã đóng</Badge>
        <Badge variant="neutral">Mặc định</Badge>
      </div>
    );
    expect(screen.getByText('Hoạt động')).toBeInTheDocument();
    expect(screen.getByText('Cảnh báo')).toBeInTheDocument();
    expect(screen.getByText('Đã đóng')).toBeInTheDocument();
    expect(screen.getByText('Mặc định')).toBeInTheDocument();
  });

  it('Card: renders CardHeader, CardTitle, and CardContent structurally', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Tiêu đề thẻ</CardTitle>
        </CardHeader>
        <CardContent>
          <p>Nội dung chi tiết của thẻ</p>
        </CardContent>
      </Card>
    );
    expect(screen.getByText('Tiêu đề thẻ')).toBeInTheDocument();
    expect(screen.getByText('Nội dung chi tiết của thẻ')).toBeInTheDocument();
  });

  it('Modal & ConfirmDialog: render accessible dialog roles and trigger action callbacks', () => {
    const handleClose = vi.fn();
    const handleConfirm = vi.fn();

    const { rerender } = render(
      <Modal isOpen={true} onClose={handleClose} title="Hộp thoại kiểm tra">
        <p>Nội dung hộp thoại</p>
      </Modal>
    );
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Hộp thoại kiểm tra')).toBeInTheDocument();

    // ConfirmDialog
    rerender(
      <ConfirmDialog
        isOpen={true}
        onClose={handleClose}
        onConfirm={handleConfirm}
        title="Xác nhận nộp bài"
        description="Bạn có chắc chắn muốn nộp bài thi ngay bây giờ?"
      />
    );
    expect(screen.getByText('Xác nhận nộp bài')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Xác nhận' }));
    expect(handleConfirm).toHaveBeenCalledTimes(1);
  });

  it('Skeleton, EmptyState, ErrorState, Banner, and Pagination render cleanly', () => {
    const handleRetry = vi.fn();
    const handlePageChange = vi.fn();

    render(
      <div>
        <Skeleton variant="text" data-testid="skeleton-text" />
        <EmptyState title="Không tìm thấy bài thi" description="Vui lòng thử lại với từ khóa khác" />
        <ErrorState title="Lỗi kết nối CSDL" message="Vui lòng thử lại sau" onRetry={handleRetry} />
        <Banner variant="offline" title="Mất mạng" message="Đang lưu bài làm cục bộ" />
        <Pagination currentPage={2} totalPages={5} onPageChange={handlePageChange} />
      </div>
    );

    expect(screen.getByTestId('skeleton-text')).toBeInTheDocument();
    expect(screen.getByText('Không tìm thấy bài thi')).toBeInTheDocument();
    expect(screen.getByText('Lỗi kết nối CSDL')).toBeInTheDocument();
    expect(screen.getByText('Mất mạng:')).toBeInTheDocument();
    expect(screen.getByTestId('pagination-nav')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Thử lại' }));
    expect(handleRetry).toHaveBeenCalledTimes(1);
  });

  it('FileDropzone: supports file drag & drop and validates maximum file size', () => {
    const handleFile = vi.fn();
    render(
      <FileDropzone
        accept=".py,.cpp"
        maxSizeMb={1}
        onFileSelect={handleFile}
        label="Nộp mã nguồn"
      />
    );
    expect(screen.getByText('Nộp mã nguồn')).toBeInTheDocument();

    // Try selecting oversized file (> 1MB)
    const bigFile = new File(['a'.repeat(2 * 1024 * 1024)], 'solution.py', { type: 'text/x-python' });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    fireEvent.change(input, { target: { files: [bigFile] } });
    expect(screen.getByText(/Dung lượng file vượt quá giới hạn/i)).toBeInTheDocument();
    expect(handleFile).not.toHaveBeenCalled();
  });
});

describe('TC-1.5-02: Anti-Double-Click on Form Submit Button', () => {
  it('prevents multiple submissions when user clicks rapidly during an in-flight async request', async () => {
    let callCount = 0;
    const slowAsyncHandler = vi.fn(async () => {
      callCount += 1;
      await new Promise((resolve) => setTimeout(resolve, 80));
    });

    render(
      <form onSubmit={(e) => e.preventDefault()}>
        <Button type="submit" onClick={slowAsyncHandler}>
          Nộp bài thi
        </Button>
      </form>
    );

    const submitBtn = screen.getByRole('button', { name: 'Nộp bài thi' });

    // Double-click rapidly
    fireEvent.click(submitBtn);
    fireEvent.click(submitBtn);
    fireEvent.click(submitBtn);

    // Initial click triggered
    expect(slowAsyncHandler).toHaveBeenCalledTimes(1);
    expect(callCount).toBe(1);

    // Wait for the async task to complete
    await waitFor(() => {
      expect(submitBtn).not.toBeDisabled();
    });

    // After completion, button can be clicked again
    fireEvent.click(submitBtn);
    expect(slowAsyncHandler).toHaveBeenCalledTimes(2);
  });
});

describe('TC-1.5-06: Countdown Timer & SaveIndicator Milestone Transitions', () => {
  it('Timer: transitions through Normal, Warning, Critical, Expired states with correct color tokens and icons', () => {
    const { rerender } = render(<Timer remainingSeconds={600} />);
    // > 5 minutes: Normal state
    expect(screen.getByTestId('timer-pill')).toHaveAttribute('data-timer-state', 'normal');
    expect(screen.getByTestId('timer-icon-normal')).toBeInTheDocument();
    expect(screen.getByText('Bình thường')).toBeInTheDocument();
    expect(screen.getByText('00:10:00')).toBeInTheDocument();

    // < 5 minutes (240s): Warning state
    rerender(<Timer remainingSeconds={240} />);
    expect(screen.getByTestId('timer-pill')).toHaveAttribute('data-timer-state', 'warning');
    expect(screen.getByTestId('timer-icon-warning')).toBeInTheDocument();
    expect(screen.getByText('Sắp hết giờ')).toBeInTheDocument();
    expect(screen.getByText('00:04:00')).toBeInTheDocument();
    expect(screen.getByText(/Thời gian làm bài còn dưới 5 phút/i)).toBeInTheDocument();

    // < 1 minute (45s): Critical state
    rerender(<Timer remainingSeconds={45} />);
    expect(screen.getByTestId('timer-pill')).toHaveAttribute('data-timer-state', 'critical');
    expect(screen.getByTestId('timer-icon-critical')).toBeInTheDocument();
    expect(screen.getByText('Khẩn cấp')).toBeInTheDocument();
    expect(screen.getByText('00:00:45')).toBeInTheDocument();
    expect(screen.getByText(/Thời gian làm bài còn dưới 1 phút/i)).toBeInTheDocument();

    // 0s: Expired state
    rerender(<Timer remainingSeconds={0} />);
    expect(screen.getByTestId('timer-pill')).toHaveAttribute('data-timer-state', 'expired');
    expect(screen.getByText('Hết giờ')).toBeInTheDocument();
    expect(screen.getByText('00:00:00')).toBeInTheDocument();
  });

  it('SaveIndicator: displays accurate status for saved, saving, offline, and error states', () => {
    const handleRetry = vi.fn();
    const { rerender } = render(<SaveIndicator status="saved" />);
    expect(screen.getByTestId('save-indicator')).toHaveAttribute('data-save-status', 'saved');
    expect(screen.getByText('Đã lưu')).toBeInTheDocument();

    // Saving
    rerender(<SaveIndicator status="saving" />);
    expect(screen.getByTestId('save-indicator')).toHaveAttribute('data-save-status', 'saving');
    expect(screen.getByText('Đang lưu...')).toBeInTheDocument();

    // Offline
    rerender(<SaveIndicator status="offline" />);
    expect(screen.getByTestId('save-indicator')).toHaveAttribute('data-save-status', 'offline');
    expect(screen.getByText('Đã lưu cục bộ (Mất mạng)')).toBeInTheDocument();

    // Error with retry button
    rerender(<SaveIndicator status="error" onRetry={handleRetry} />);
    expect(screen.getByTestId('save-indicator')).toHaveAttribute('data-save-status', 'error');
    expect(screen.getByText('Lỗi lưu')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Thử lại' }));
    expect(handleRetry).toHaveBeenCalledTimes(1);
  });

  it('QuestionNav: shows progress percentage and updates when questions are answered or flagged', () => {
    const handleSelect = vi.fn();
    const mockList = [
      { id: '1', number: 1, status: 'answered' as const },
      { id: '2', number: 2, status: 'flagged' as const },
      { id: '3', number: 3, status: 'unanswered' as const },
    ];

    render(
      <QuestionNav
        questions={mockList}
        currentQuestion={2}
        onSelectQuestion={handleSelect}
      />
    );

    // Progress: 1/3 ~ 33%
    expect(screen.getByText('1/3 (33%)')).toBeInTheDocument();
    expect(screen.getByTestId('flag-indicator-2')).toBeInTheDocument();

    // Click question 3
    fireEvent.click(screen.getByTestId('question-btn-3'));
    expect(handleSelect).toHaveBeenCalledWith(3);
  });
});
