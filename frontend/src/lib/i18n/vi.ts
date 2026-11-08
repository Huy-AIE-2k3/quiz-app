/**
 * Centralized Vietnamese localization dictionary and date/time formatters.
 * Enforces standardized UI copy across application.
 */

export const VI = {
  common: {
    appName: 'Quiz Toán - Tin',
    systemTitle: 'MATHRIX QUIZ',
    loading: 'Đang tải dữ liệu...',
    saving: 'Đang lưu...',
    saved: 'Đã lưu',
    error: 'Đã có lỗi xảy ra',
    retry: 'Thử lại',
    reload: 'Tải lại trang',
    confirm: 'Xác nhận',
    cancel: 'Hủy bỏ',
    back: 'Quay lại',
    save: 'Lưu thay đổi',
    close: 'Đóng',
    submit: 'Nộp bài',
    search: 'Tìm kiếm...',
  },
  auth: {
    loginTitle: 'Đăng nhập hệ thống',
    loginSubtitle: 'Dành cho giáo viên quản trị và học sinh',
    username: 'Tên đăng nhập',
    password: 'Mật khẩu',
    signIn: 'Đăng nhập',
    signOut: 'Đăng xuất',
    signingIn: 'Đang đăng nhập...',
    loginSuccess: 'Đăng nhập thành công',
    sessionExpired: 'Phiên làm việc đã hết hạn. Vui lòng đăng nhập lại.',
    unauthorized: 'Vui lòng đăng nhập để tiếp tục.',
    forbidden: 'Bạn không có quyền truy cập vào trang này.',
    storageWarning:
      'Trình duyệt đang chặn bộ nhớ cục bộ (Private Mode / Cookies bị tắt). Đóng tab sẽ làm mất phiên đăng nhập!',
  },
  server: {
    wakingTitle: 'Đang kết nối máy chủ...',
    wakingMessage:
      'Máy chủ đám mây đang thức dậy sau thời gian nghỉ. Quá trình này có thể mất tới ~1 phút.',
    unreachableTitle: 'Không thể kết nối máy chủ',
    unreachableMessage:
      'Máy chủ không phản hồi sau 90 giây. Vui lòng kiểm tra lại mạng hoặc thử lại.',
    updateTitle: 'Bản cập nhật mới',
    updateMessage:
      'Hệ thống vừa có phiên bản cập nhật mới. Bấm tải lại để cập nhật giao diện mà không làm mất dữ liệu nháp.',
  },
  network: {
    offline: 'Mất kết nối mạng Internet. Bài làm đang được lưu tạm trên máy.',
    online: 'Đã khôi phục kết nối mạng.',
    timeout: 'Yêu cầu hết thời gian chờ (15s). Vui lòng thử lại.',
    tooManyRequests: 'Thao tác quá nhanh. Vui lòng chờ ít giây trước khi thử lại.',
    serverError: 'Lỗi máy chủ (500). Đội ngũ kỹ thuật đã được thông báo.',
    badGateway: 'Máy chủ tạm thời gián đoạn (502/503). Đang tự động thử lại...',
  },
  roles: {
    admin: 'Quản trị viên / Giáo viên',
    student: 'Học sinh',
    guest: 'Khách',
  },
  exam: {
    timeRemaining: 'Thời gian còn lại',
    submittedSuccess: 'Nộp bài thành công!',
    autosaveDraft: 'Bản nháp đã lưu an toàn trên máy.',
  },
} as const;

/**
 * Formats a Date using the standard Vietnam locale and timezone (Asia/Ho_Chi_Minh).
 */
export function formatDateTime(
  date: Date | string | number,
  options?: Intl.DateTimeFormatOptions
): string {
  const d = date instanceof Date ? date : new Date(date);
  if (isNaN(d.getTime())) return '';

  const defaultOptions: Intl.DateTimeFormatOptions = {
    timeZone: 'Asia/Ho_Chi_Minh',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
    ...options,
  };

  return new Intl.DateTimeFormat('vi-VN', defaultOptions).format(d);
}

/**
 * Formats seconds into human-readable Vietnamese duration (e.g. 90m -> "1 giờ 30 phút").
 */
export function formatDuration(totalSeconds: number): string {
  if (totalSeconds <= 0) return '0 giây';
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  const parts: string[] = [];
  if (hours > 0) parts.push(`${hours} giờ`);
  if (minutes > 0) parts.push(`${minutes} phút`);
  if (seconds > 0 && hours === 0) parts.push(`${seconds} giây`);

  return parts.join(' ');
}
