import React, { useState } from 'react';
import { adminApi, CsvImportResult } from '../../lib/adminApi';
import { NetworkError } from '../../lib/api';
import { Button } from '../ui/Button';
import { FileDropzone } from '../ui/FileDropzone';
import { Checkbox } from '../ui/Checkbox';
import { Badge } from '../ui/Badge';
import { Table } from '../ui/Table';
import {
  CheckCircle2,
  AlertCircle,
  Download,
  ArrowLeft,
  ArrowRight,
  ShieldAlert,
  WifiOff,
} from 'lucide-react';

interface CsvImportWizardProps {
  defaultClassId?: string;
  onSuccess?: () => void;
  onCancel?: () => void;
}

const ERROR_LABELS: Record<string, string> = {
  name_empty: 'Họ và tên để trống',
  username_invalid: 'Tên đăng nhập không hợp lệ (cần 3-32 ký tự a-z, 0-9, ._-)',
  username_duplicate_in_file: 'Tên đăng nhập bị trùng lặp trong tệp',
  username_taken: 'Tên đăng nhập đã tồn tại trên hệ thống',
  class_not_found: 'Mã lớp không tồn tại',
  password_invalid: 'Mật khẩu phải từ 6 đến 128 ký tự',
  password_required: 'Chưa có mật khẩu (hãy bật tự sinh mật khẩu)',
};

export const CsvImportWizard: React.FC<CsvImportWizardProps> = ({
  defaultClassId,
  onSuccess,
  onCancel,
}) => {
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [file, setFile] = useState<File | null>(null);
  const [autoGenPasswords, setAutoGenPasswords] = useState(true);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [networkErrorAlert, setNetworkErrorAlert] = useState<string | null>(null);
  const [dryRunResult, setDryRunResult] = useState<CsvImportResult | null>(null);
  const [commitResult, setCommitResult] = useState<CsvImportResult | null>(null);

  // Step 1: Run Dry-run check
  const handleDryRun = async () => {
    if (!file) return;
    setLoading(true);
    setErrorMsg(null);
    setNetworkErrorAlert(null);

    try {
      const res = await adminApi.importStudentsCsv(file, {
        dry_run: true,
        auto_generate_passwords: autoGenPasswords,
        default_class_id: defaultClassId,
      });
      setDryRunResult(res);
      setStep(2);
    } catch (err: unknown) {
      if (err instanceof NetworkError) {
        setErrorMsg('Không thể kết nối đến máy chủ. Vui lòng kiểm tra đường truyền mạng.');
      } else if (typeof err === 'object' && err !== null && 'message' in err) {
        setErrorMsg((err as { message: string }).message);
      } else {
        setErrorMsg('Lỗi không xác định khi kiểm tra tệp CSV.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Confirm and Commit Atomic Import
  const handleConfirmCommit = async () => {
    if (!file) return;
    setLoading(true);
    setErrorMsg(null);
    setNetworkErrorAlert(null);

    try {
      const res = await adminApi.importStudentsCsv(file, {
        dry_run: false,
        auto_generate_passwords: autoGenPasswords,
        default_class_id: defaultClassId,
      });
      setCommitResult(res);
      setStep(3);
    } catch (err: unknown) {
      if (err instanceof NetworkError) {
        // TC-3.4-07: Display clear network failure warning, NEVER retry automatically
        setNetworkErrorAlert(
          'Đã xảy ra lỗi gián đoạn kết nối mạng trong quá trình xác nhận nhập. ' +
            'Hệ thống KHÔNG tự ý gửi lại yêu cầu để tránh nhân đôi dữ liệu. ' +
            'Vui lòng kiểm tra lại danh sách học sinh trên hệ thống trước khi thử lại.'
        );
      } else if (typeof err === 'object' && err !== null && 'message' in err) {
        setErrorMsg((err as { message: string }).message);
      } else {
        setErrorMsg('Lỗi không xác định khi lưu học sinh vào hệ thống.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Download Passwords CSV
  const handleDownloadCsv = () => {
    if (!commitResult?.csv_export_content) return;
    // Ensure UTF-8 BOM encoding for native Excel compatibility
    const blob = new Blob([commitResult.csv_export_content], {
      type: 'text/csv;charset=utf-8;',
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute(
      'download',
      `mat_khau_hoc_sinh_${new Date().toISOString().slice(0, 10)}.csv`
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col gap-6 text-text-primary">
      {/* Step Indicators */}
      <div className="flex items-center justify-between border-b border-line-subtle pb-4">
        <div className="flex items-center gap-2">
          <span
            className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
              step >= 1 ? 'bg-brand text-text-inverse' : 'bg-surface-raised text-text-muted'
            }`}
          >
            1
          </span>
          <span className={`text-xs font-medium ${step === 1 ? 'text-brand' : 'text-text-secondary'}`}>
            Chọn tệp &amp; Cấu hình
          </span>
        </div>

        <div className="w-8 h-px bg-line-subtle" />

        <div className="flex items-center gap-2">
          <span
            className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
              step >= 2 ? 'bg-brand text-text-inverse' : 'bg-surface-raised text-text-muted'
            }`}
          >
            2
          </span>
          <span className={`text-xs font-medium ${step === 2 ? 'text-brand' : 'text-text-secondary'}`}>
            Xem trước &amp; Kiểm tra lỗi
          </span>
        </div>

        <div className="w-8 h-px bg-line-subtle" />

        <div className="flex items-center gap-2">
          <span
            className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
              step === 3 ? 'bg-brand text-text-inverse' : 'bg-surface-raised text-text-muted'
            }`}
          >
            3
          </span>
          <span className={`text-xs font-medium ${step === 3 ? 'text-brand' : 'text-text-secondary'}`}>
            Tải bảng mật khẩu
          </span>
        </div>
      </div>

      {/* Network Error Alert (TC-3.4-07) */}
      {networkErrorAlert && (
        <div className="p-4 rounded-lg bg-status-wrong-bg border border-status-wrong-border text-status-wrong-text flex items-start gap-3">
          <WifiOff className="w-5 h-5 shrink-0 mt-0.5" />
          <div className="flex flex-col gap-1 text-xs">
            <span className="font-semibold text-sm">Mất kết nối mạng!</span>
            <span>{networkErrorAlert}</span>
          </div>
        </div>
      )}

      {/* General Error Message */}
      {errorMsg && (
        <div className="p-3 rounded-md bg-status-wrong-bg border border-status-wrong-border text-status-wrong-text text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* ================= STEP 1: Upload File ================= */}
      {step === 1 && (
        <div className="flex flex-col gap-5">
          <FileDropzone
            accept=".csv,text/csv"
            maxSizeMb={1}
            onFileSelect={(f) => setFile(f)}
            currentFile={file}
            label="Chọn hoặc kéo thả tệp CSV danh sách học sinh"
            helperText="Định dạng CSV UTF-8 hoặc Windows-1258. Dung lượng tối đa 1 MB, tối đa 500 dòng."
          />

          <div className="p-3.5 rounded-lg bg-surface border border-line-subtle flex flex-col gap-1.5">
            <Checkbox
              id="auto-gen-passwords"
              checked={autoGenPasswords}
              onChange={(e) => setAutoGenPasswords(e.target.checked)}
              label="Tự động tạo mật khẩu ngẫu nhiên an toàn cho các ô trống"
            />
            <span className="text-xs text-text-muted pl-6">
              Mật khẩu dài 8 ký tự, bao gồm cả chữ và số, loại bỏ các ký tự dễ nhầm (0, O, I, l, 1).
            </span>
          </div>

          <div className="flex items-center justify-between pt-2">
            {onCancel && (
              <Button variant="ghost" size="sm" onClick={onCancel} disabled={loading}>
                Hủy bỏ
              </Button>
            )}
            <Button
              variant="primary"
              size="sm"
              onClick={handleDryRun}
              disabled={!file || loading}
              loading={loading}
              className="ml-auto flex items-center gap-1.5"
            >
              <span>Kiểm tra tệp (Xem trước)</span>
              <ArrowRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}

      {/* ================= STEP 2: Dry-run Result ================= */}
      {step === 2 && dryRunResult && (
        <div className="flex flex-col gap-4">
          {/* Summary Box */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3.5 rounded-lg bg-surface border border-line-subtle text-xs">
            <div className="flex flex-col">
              <span className="text-text-muted">Tổng số dòng:</span>
              <span className="text-sm font-bold font-mono">{dryRunResult.total_rows}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-text-muted">Hợp lệ:</span>
              <span className="text-sm font-bold font-mono text-status-correct-text">
                {dryRunResult.valid_rows}
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-text-muted">Dòng lỗi:</span>
              <span
                className={`text-sm font-bold font-mono ${
                  dryRunResult.error_rows > 0 ? 'text-status-wrong-text' : 'text-text-muted'
                }`}
              >
                {dryRunResult.error_rows}
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-text-muted">Ước tính xử lý:</span>
              <span className="text-sm font-bold font-mono text-brand">
                ~{dryRunResult.estimated_hash_seconds}s
              </span>
            </div>
          </div>

          {/* Error Banner if any */}
          {dryRunResult.error_rows > 0 ? (
            <div className="p-3 rounded-md bg-status-wrong-bg border border-status-wrong-border text-status-wrong-text text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>
                Phát hiện <strong>{dryRunResult.error_rows}</strong> dòng có lỗi. Nút xác nhận bị
                vô hiệu hóa cho đến khi tệp được sửa sạch hoàn toàn.
              </span>
            </div>
          ) : (
            <div className="p-3 rounded-md bg-status-correct-bg border border-status-correct-border text-status-correct-text text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>
                Tất cả <strong>{dryRunResult.valid_rows}</strong> dòng đều hợp lệ! Bạn có thể xác nhận
                để lưu học sinh vào hệ thống.
              </span>
            </div>
          )}

          {/* Details Table */}
          <div className="max-h-72 overflow-y-auto border border-line-subtle rounded-lg">
            <Table>
              <thead>
                <tr>
                  <th className="w-16">Dòng</th>
                  <th>Họ và tên</th>
                  <th>Tên đăng nhập</th>
                  <th>Mã lớp</th>
                  <th>Trạng thái</th>
                  <th>Chi tiết lỗi</th>
                </tr>
              </thead>
              <tbody>
                {dryRunResult.rows.map((row) => {
                  const isErr = row.status === 'error';
                  return (
                    <tr
                      key={row.row_number}
                      className={isErr ? 'bg-status-wrong-bg/30' : undefined}
                    >
                      <td className="font-mono text-xs">{row.row_number}</td>
                      <td className="font-medium text-xs">{row.full_name || '—'}</td>
                      <td className="font-mono text-xs text-text-secondary">{row.username || '—'}</td>
                      <td className="font-mono text-xs">{row.class_code || '—'}</td>
                      <td>
                        {isErr ? (
                          <Badge variant="danger" size="sm">
                            LỖI
                          </Badge>
                        ) : (
                          <Badge variant="brand" size="sm">
                            HỢP LỆ
                          </Badge>
                        )}
                      </td>
                      <td className="text-xs text-status-wrong-text">
                        {row.errors.map((e) => ERROR_LABELS[e] || e).join(', ')}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </Table>
          </div>

          <div className="flex items-center justify-between pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setStep(1)}
              disabled={loading}
              className="flex items-center gap-1.5"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Chọn tệp khác</span>
            </Button>

            <Button
              variant="primary"
              size="sm"
              onClick={handleConfirmCommit}
              // TC-3.4-04: Button disabled when any error row exists
              disabled={!dryRunResult.can_commit || dryRunResult.error_rows > 0 || loading}
              loading={loading}
            >
              Xác nhận nhập ({dryRunResult.valid_rows} học sinh)
            </Button>
          </div>
        </div>
      )}

      {/* ================= STEP 3: Success & Download Passwords ================= */}
      {step === 3 && commitResult && (
        <div className="flex flex-col gap-5">
          <div className="p-4 rounded-lg bg-status-correct-bg border border-status-correct-border text-status-correct-text flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 shrink-0 mt-0.5" />
            <div className="flex flex-col gap-1 text-xs">
              <span className="font-bold text-sm">Nhập học sinh thành công!</span>
              <span>
                Đã tạo thành công <strong>{commitResult.created_count}</strong> tài khoản học sinh.
              </span>
            </div>
          </div>

          {/* One-time Warning Banner */}
          <div className="p-3.5 rounded-lg bg-surface border border-brand/40 flex items-start gap-3">
            <ShieldAlert className="w-5 h-5 text-brand shrink-0 mt-0.5" />
            <div className="flex flex-col gap-1 text-xs">
              <span className="font-semibold text-text-primary">
                Cảnh báo bảo mật: Mật khẩu chỉ hiển thị một lần duy nhất!
              </span>
              <span className="text-text-muted">
                Vì lý do an toàn, hệ thống không lưu mật khẩu dạng bản rõ. Hãy tải tệp CSV về máy ngay
                để gửi cho học sinh.
              </span>
            </div>
          </div>

          {/* Passwords Table */}
          <div className="max-h-60 overflow-y-auto border border-line-subtle rounded-lg">
            <Table>
              <thead>
                <tr>
                  <th>Tên đăng nhập</th>
                  <th>Họ và tên</th>
                  <th>Lớp</th>
                  <th>Mật khẩu khởi tạo</th>
                </tr>
              </thead>
              <tbody>
                {commitResult.students.map((st) => (
                  <tr key={st.id}>
                    <td className="font-mono text-xs font-semibold">{st.username}</td>
                    <td className="text-xs">{st.full_name}</td>
                    <td className="font-mono text-xs">{st.class_code || '—'}</td>
                    <td className="font-mono text-xs font-bold text-brand">{st.password_plain}</td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </div>

          <div className="flex items-center justify-between pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownloadCsv}
              className="flex items-center gap-1.5"
            >
              <Download className="w-4 h-4 text-brand" />
              <span>Tải tệp CSV mật khẩu</span>
            </Button>

            <Button
              variant="primary"
              size="sm"
              onClick={() => {
                onSuccess?.();
              }}
            >
              Hoàn tất
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
