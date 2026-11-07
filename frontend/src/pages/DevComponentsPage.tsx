import React, { useState } from 'react';
import {
  Button,
  Input,
  Textarea,
  Select,
  Checkbox,
  Radio,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Badge,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  Tabs,
  TabList,
  TabTrigger,
  TabContent,
  Modal,
  ConfirmDialog,
  useToast,
  Skeleton,
  EmptyState,
  ErrorState,
  Banner,
  FileDropzone,
  Pagination,
  MathText,
  Timer,
  SaveIndicator,
  SaveStatus,
  QuestionNav,
  QuestionNavItem,
} from '../components';
import { mockStudentRoster, mockQuestions } from '../data/mockData';
import { Moon, Sun, Search, Send, Key, FileText } from 'lucide-react';

export interface DevComponentsPageProps {}

export const DevComponentsPage: React.FC<DevComponentsPageProps> = () => {
  const { toast } = useToast();
  const [isDark, setIsDark] = useState(true);

  // Component states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('saved');
  const [timerSeconds, setTimerSeconds] = useState<number>(600);
  const [currentQuestion, setCurrentQuestion] = useState<number>(1);
  const [questions, setQuestions] = useState<readonly QuestionNavItem[]>(mockQuestions);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [droppedFile, setDroppedFile] = useState<File | null>(null);
  const [submitCounter, setSubmitCounter] = useState(0);

  const toggleTheme = () => {
    setIsDark(!isDark);
    if (!isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  const handleSimulateAsyncSubmit = async () => {
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setSubmitCounter((c) => c + 1);
    toast.success('Submit thành công! Chống bấm đúp đã hoạt động.');
  };

  const handleToggleFlag = () => {
    setQuestions((prev) =>
      prev.map((q) =>
        q.number === currentQuestion
          ? {
              ...q,
              status: q.status === 'flagged' ? 'unanswered' : 'flagged',
            }
          : q
      )
    );
  };

  const handleMarkAnswered = () => {
    setQuestions((prev) =>
      prev.map((q) =>
        q.number === currentQuestion
          ? {
              ...q,
              status: 'answered',
            }
          : q
      )
    );
  };

  return (
    <div className="min-h-screen bg-canvas text-text-primary p-6 md:p-12 transition-colors">
      <div className="max-w-6xl mx-auto space-y-12">
        {/* Header & Theme Switcher */}
        <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-line-subtle">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-display font-bold text-2xl text-text-primary">
                Mathrix UI Component Showroom
              </span>
              <Badge variant="brand" size="sm">
                /dev/components
              </Badge>
            </div>
            <p className="text-xs font-mono text-text-muted">
              Hệ thống Design System Emerald Precision (0 mã màu hardcode, 100% tokens WCAG AA)
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={toggleTheme}
              iconLeft={isDark ? <Sun className="w-4 h-4 text-brand" /> : <Moon className="w-4 h-4" />}
            >
              {isDark ? 'Giao diện Sáng' : 'Giao diện Tối'}
            </Button>
          </div>
        </header>

        {/* 1. BUTTONS */}
        <section className="space-y-4 text-left">
          <div className="flex items-center justify-between border-b border-line-subtle pb-2">
            <h2 className="font-display font-semibold text-lg text-text-primary">
              1. Button (Các biến thể, Kích cỡ, Chống bấm đúp)
            </h2>
            <span className="text-xs font-mono text-text-muted">TC-1.5-01, TC-1.5-02</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle as="h4">Variants & Sizes</CardTitle>
                <CardDescription>Primary, Secondary, Outline, Ghost, Danger</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-3 items-center">
                  <Button variant="primary">Primary</Button>
                  <Button variant="secondary">Secondary</Button>
                  <Button variant="outline">Outline</Button>
                  <Button variant="ghost">Ghost</Button>
                  <Button variant="danger">Danger</Button>
                </div>
                <div className="flex flex-wrap gap-3 items-center pt-2">
                  <Button size="sm">Small</Button>
                  <Button size="md">Medium</Button>
                  <Button size="lg">Large</Button>
                  <Button disabled>Disabled</Button>
                  <Button loading>Loading</Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle as="h4">Chống bấm đúp (Anti-Double-Click)</CardTitle>
                <CardDescription>
                  Tự động khóa nút khi async handler đang chạy (Đã gọi: {submitCounter} lần)
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button
                  variant="primary"
                  type="submit"
                  iconLeft={<Send className="w-4 h-4" />}
                  onClick={handleSimulateAsyncSubmit}
                >
                  Nhấn thử nghiệm gửi (Async 1.5s)
                </Button>
                <p className="text-xs font-mono text-text-muted">
                  * Khi bấm đúp thật nhanh, chỉ có 1 request duy nhất được thực thi.
                </p>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* 2. FORM CONTROLS */}
        <section className="space-y-4 text-left">
          <div className="flex items-center justify-between border-b border-line-subtle pb-2">
            <h2 className="font-display font-semibold text-lg text-text-primary">
              2. Form Controls (Input, Textarea, Select, Checkbox, Radio)
            </h2>
            <span className="text-xs font-mono text-text-muted">A11y Label & Error Link</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle as="h4">Input & Textarea</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Input
                  label="Tên đăng nhập"
                  placeholder="Nhập mã định danh..."
                  iconLeft={<Search className="w-4 h-4" />}
                  helperText="Ví dụ: GV_TOAN12 hoặc HS2025"
                />
                <Input
                  label="Mật khẩu"
                  type="password"
                  isPasswordToggle
                  placeholder="••••••••••••"
                  iconLeft={<Key className="w-4 h-4" />}
                />
                <Input
                  label="Trường hợp lỗi"
                  error="Mã lớp không hợp lệ hoặc đã tồn tại"
                  defaultValue="12A1-ERROR"
                />
                <Textarea
                  label="Ghi chú bài thi"
                  placeholder="Nhập ghi chú cho học sinh..."
                  showCount
                  maxLength={200}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle as="h4">Select, Checkbox & Radio</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Select
                  label="Khối lớp"
                  placeholder="Chọn khối..."
                  options={[
                    { value: '10', label: 'Khối 10 (Toán & Tin)' },
                    { value: '11', label: 'Khối 11 (Toán & Tin)' },
                    { value: '12', label: 'Khối 12 (Toán & Tin Ôn Thi TN)' },
                  ]}
                />
                <div className="space-y-2 pt-2">
                  <Checkbox
                    label="Tự động công bố kết quả sau khi thi"
                    description="Học sinh xem được phổ điểm và đáp án ngay sau khi nộp bài."
                    defaultChecked
                  />
                  <Checkbox
                    label="Xáo trộn câu hỏi và các phương án"
                    description="Mỗi học sinh nhận mã đề ngẫu nhiên với thứ tự câu khác nhau."
                  />
                </div>
                <div className="pt-2 border-t border-line-subtle space-y-2">
                  <span className="text-xs font-mono font-medium text-text-secondary">
                    Hình thức nộp bài:
                  </span>
                  <div className="space-y-1.5">
                    <Radio name="sub" label="Trực tuyến qua trình duyệt (Mặc định)" defaultChecked />
                    <Radio name="sub" label="Nộp file mã nguồn / tự luận kèm theo" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* 3. EXAM MODULES: TIMER, SAVE INDICATOR, QUESTION NAV */}
        <section className="space-y-4 text-left">
          <div className="flex items-center justify-between border-b border-line-subtle pb-2">
            <h2 className="font-display font-semibold text-lg text-text-primary">
              3. Thành phần Phòng thi (Timer, SaveIndicator, Bento QuestionNav)
            </h2>
            <span className="text-xs font-mono text-text-muted">TC-1.5-06</span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-6 space-y-6">
              {/* Timer Controls */}
              <Card>
                <CardHeader>
                  <CardTitle as="h4">Đồng hồ thi (Monotonic Countdown)</CardTitle>
                  <CardDescription>
                    Tự đổi màu/icon khi &lt; 5m (warning) và &lt; 1m (critical); hỗ trợ người mù màu
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center gap-4">
                    <Timer remainingSeconds={timerSeconds} />
                  </div>

                  <div className="flex flex-wrap gap-2 pt-2">
                    <Button size="sm" variant="outline" onClick={() => setTimerSeconds(600)}>
                      Đặt 10 phút (&gt;5m)
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => setTimerSeconds(240)}>
                      Đặt 4 phút (&lt;5m)
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => setTimerSeconds(45)}>
                      Đặt 45 giây (&lt;1m)
                    </Button>
                    <Button size="sm" variant="danger" onClick={() => setTimerSeconds(0)}>
                      Đặt 0s (Hết giờ)
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* SaveIndicator */}
              <Card>
                <CardHeader>
                  <CardTitle as="h4">Chỉ báo trạng thái lưu (SaveIndicator)</CardTitle>
                  <CardDescription>Tự lưu Outbox, cảnh báo mất mạng, aria-live</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center gap-3">
                    <SaveIndicator
                      status={saveStatus}
                      lastSavedAt={new Date()}
                      onRetry={() => {
                        setSaveStatus('saving');
                        setTimeout(() => setSaveStatus('saved'), 1000);
                      }}
                    />
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <Button size="sm" variant="outline" onClick={() => setSaveStatus('saved')}>
                      Trạng thái: Đã lưu
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => setSaveStatus('saving')}>
                      Trạng thái: Đang lưu...
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => setSaveStatus('offline')}>
                      Trạng thái: Offline
                    </Button>
                    <Button size="sm" variant="danger" onClick={() => setSaveStatus('error')}>
                      Trạng thái: Lỗi lưu
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="lg:col-span-6">
              {/* QuestionNav Palette */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle as="h4">Bento Question Palette</CardTitle>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" onClick={handleMarkAnswered}>
                        Lưu câu {currentQuestion}
                      </Button>
                      <Button size="sm" variant="outline" onClick={handleToggleFlag}>
                        Đánh dấu [F]
                      </Button>
                    </div>
                  </div>
                  <CardDescription>
                    Điều hướng câu hỏi trong bài kiểm tra (Đang chọn câu {currentQuestion})
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <QuestionNav
                    questions={questions}
                    currentQuestion={currentQuestion}
                    onSelectQuestion={(num) => setCurrentQuestion(num)}
                  />
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        {/* 4. FEEDBACK: MODAL, TOAST, BANNER, EMPTY & ERROR STATE */}
        <section className="space-y-4 text-left">
          <div className="flex items-center justify-between border-b border-line-subtle pb-2">
            <h2 className="font-display font-semibold text-lg text-text-primary">
              4. Phản hồi người dùng (Modal, Toast, Banner, Empty &amp; Error State)
            </h2>
            <span className="text-xs font-mono text-text-muted">Focus trap &amp; Alert</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle as="h4">Hộp thoại &amp; Toasts</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-wrap gap-2">
                  <Button variant="outline" size="sm" onClick={() => setIsModalOpen(true)}>
                    Mở Hộp thoại (Modal)
                  </Button>
                  <Button variant="danger" size="sm" onClick={() => setIsConfirmOpen(true)}>
                    Mở Xác nhận Nộp bài
                  </Button>
                </div>

                <div className="pt-2 border-t border-line-subtle flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => toast.success('Đã lưu bài làm thành công!')}
                  >
                    Toast Thành công
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => toast.warning('Sắp hết giờ làm bài (còn 5 phút)!')}
                  >
                    Toast Cảnh báo
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => toast.error('Mất kết nối với máy chủ!')}
                  >
                    Toast Lỗi
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle as="h4">Banners thông báo</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Banner
                  variant="offline"
                  title="Mất mạng"
                  message="Mọi câu trả lời đang được lưu tạm trên máy của bạn."
                />
                <Banner
                  variant="wake"
                  title="Máy chủ"
                  message="Đang đánh thức máy chủ Docker Sandbox..."
                />
                <Banner
                  variant="info"
                  title="Nội quy"
                  message="Không chuyển tab trong suốt thời gian làm bài."
                />
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            <EmptyState
              title="Chưa có đề thi nào"
              description="Hãy bấm nút bên dưới để bắt đầu soạn đề kiểm tra Toán hoặc Tin học mới."
              action={
                <Button size="sm" iconLeft={<FileText className="w-4 h-4" />}>
                  Soạn đề mới
                </Button>
              }
            />
            <ErrorState
              title="Không thể tải danh sách lớp"
              message="Đường truyền mạng gặp sự cố hoặc máy chủ phản hồi chậm. Vui lòng bấm thử lại."
              onRetry={() => toast.info('Đang kết nối lại...')}
            />
          </div>
        </section>

        {/* 5. DATA PRESENTATION: TABLE, TABS, FILE DROPZONE, PAGINATION */}
        <section className="space-y-4 text-left">
          <div className="flex items-center justify-between border-b border-line-subtle pb-2">
            <h2 className="font-display font-semibold text-lg text-text-primary">
              5. Hiển thị Dữ liệu (Table, Tabs, FileDropzone, Pagination)
            </h2>
            <span className="text-xs font-mono text-text-muted">Data Tables &amp; Files</span>
          </div>

          <Card>
            <CardHeader>
              <CardTitle as="h4">Danh sách Học sinh (Table Component)</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Mã định danh</TableHead>
                    <TableHead>Họ và Tên</TableHead>
                    <TableHead>Lớp</TableHead>
                    <TableHead>Ngày sinh</TableHead>
                    <TableHead>Trạng thái</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mockStudentRoster.map((s) => (
                    <TableRow key={s.id}>
                      <TableCell className="font-mono text-xs text-text-secondary">{s.code}</TableCell>
                      <TableCell className="font-semibold text-text-primary">{s.name}</TableCell>
                      <TableCell className="font-mono text-xs">{s.class}</TableCell>
                      <TableCell className="font-mono text-xs text-text-muted">{s.dob}</TableCell>
                      <TableCell>
                        <Badge variant={s.status === 'Hoạt động' ? 'brand' : 'warning'} size="sm" dot>
                          {s.status}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              <Pagination
                currentPage={currentPage}
                totalPages={5}
                totalItems={25}
                pageSize={5}
                onPageChange={(p) => setCurrentPage(p)}
              />
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle as="h4">Tabs Component</CardTitle>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="math">
                  <TabList ariaLabel="Chọn phân môn khảo sát">
                    <TabTrigger value="math">Toán Học (12T1)</TabTrigger>
                    <TabTrigger value="cs">Tin Học (Python)</TabTrigger>
                    <TabTrigger value="settings">Cấu hình đề</TabTrigger>
                  </TabList>
                  <TabContent value="math" className="pt-3 text-xs font-sans text-text-secondary">
                    Gồm 4 phần: Trắc nghiệm 4 lựa chọn, Đúng/Sai 4 ý, Trả lời ngắn số học và Tự luận.
                  </TabContent>
                  <TabContent value="cs" className="pt-3 text-xs font-sans text-text-secondary">
                    Chấm mã nguồn tự động qua Docker Sandbox với 5 testcases chuẩn hóa.
                  </TabContent>
                  <TabContent value="settings" className="pt-3 text-xs font-sans text-text-secondary">
                    Thời lượng: 90 phút. Tự động thu bài khi hết giờ.
                  </TabContent>
                </Tabs>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle as="h4">FileDropzone Component</CardTitle>
              </CardHeader>
              <CardContent>
                <FileDropzone
                  accept=".py,.cpp,.csv"
                  maxSizeMb={5}
                  currentFile={droppedFile}
                  onFileSelect={(f) => setDroppedFile(f)}
                  helperText="Chấp nhận .py, .cpp hoặc .csv tối đa 5MB"
                />
              </CardContent>
            </Card>
          </div>
        </section>

        {/* 6. SKELETON LOADING */}
        <section className="space-y-4 text-left">
          <div className="flex items-center justify-between border-b border-line-subtle pb-2">
            <h2 className="font-display font-semibold text-lg text-text-primary">
              6. Skeleton Loading
            </h2>
            <span className="text-xs font-mono text-text-muted">Pulse Animation</span>
          </div>

          <Card>
            <CardContent className="space-y-3 pt-4">
              <div className="flex items-center gap-3">
                <Skeleton variant="circle" />
                <div className="flex-1 space-y-1.5">
                  <Skeleton variant="text" width="40%" />
                  <Skeleton variant="text" width="65%" />
                </div>
              </div>
              <Skeleton variant="rect" height="60px" />
            </CardContent>
          </Card>
        </section>

        {/* 7. MATHTEXT (MARKDOWN + LATEX + CODE) */}
        <section className="space-y-4 text-left">
          <div className="flex items-center justify-between border-b border-line-subtle pb-2">
            <h2 className="font-display font-semibold text-lg text-text-primary">
              7. MathText (Hiển thị Markdown, LaTeX &amp; Code Tin Học An Toàn)
            </h2>
            <span className="text-xs font-mono text-text-muted">Giai đoạn 1.6</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle as="h4">Toán Học: LaTeX Inline &amp; Block Display</CardTitle>
                <CardDescription>
                  Hỗ trợ công thức inline $x^2+y^2=r^2$ và khối tích phân KaTeX
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <MathText
                  content={`Cho hàm số $y = f(x)$ xác định trên $\\mathbb{R}$. Tính tích phân:

$$\\int_0^1 (3x^2 - 2x + 1)\\,dx = \\left[ x^3 - x^2 + x \\right]_0^1 = 1$$

Với $\\text{đa thức } P(x) = x^4 + 2x^2 + 1$, ta có $P(x) \\ge 1, \\forall x$.`}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle as="h4">Tin Học: Mã Nguồn Python / C++</CardTitle>
                <CardDescription>Cuộn ngang độc lập, không phá vỡ bố cục trên màn hình nhỏ</CardDescription>
              </CardHeader>
              <CardContent>
                <MathText
                  content={`\`\`\`python
def find_prime_factors(n: int) -> list[int]:
    factors = []
    d = 2
    while d * d <= n:
        while (n % d) == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors

# Testcase: print(find_prime_factors(1234567890))
\`\`\``}
                />
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle as="h4">Chống XSS &amp; Lọc Ảnh Trái Phép</CardTitle>
                <CardDescription>Chặn đứng script độc hại và ảnh ngoài nguồn R2</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <MathText
                  content={`Ảnh ngoài nguồn: ![Ảnh tấn công](https://evil.example.com/exploit.png)

Ảnh hợp lệ: ![Ảnh R2](/assets/logo.png)

Liên kết nguy hiểm đã được vô hiệu hóa: [Bấm vào đây](javascript:alert(1))`}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle as="h4">Xử Lý Lỗi Cú Pháp LaTeX Tại Chỗ</CardTitle>
                <CardDescription>Không làm chết ứng dụng, báo lỗi màu đỏ tại vị trí sai</CardDescription>
              </CardHeader>
              <CardContent>
                <MathText
                  content={`Công thức sai cú pháp: $\\frac{1}{$ nhưng công thức đúng kế tiếp vẫn hiển thị bình thường: $E = mc^2$.`}
                />
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Dialogs */}
        <Modal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          title="Thông tin cấu hình phòng thi"
          description="Kiểm tra các thông số trước khi mở ca thi cho học sinh."
          footer={
            <Button size="sm" onClick={() => setIsModalOpen(false)}>
              Đã hiểu
            </Button>
          }
        >
          <div className="space-y-2 text-xs font-sans text-text-secondary">
            <p>• Mã phòng: <strong>PHONG-TOAN-12</strong></p>
            <p>• Số lượng thí sinh: <strong>35 học sinh</strong></p>
            <p>• Chế độ: <strong>Nghiêm ngặt (Ghi nhận chuyển tab)</strong></p>
          </div>
        </Modal>

        <ConfirmDialog
          isOpen={isConfirmOpen}
          onClose={() => setIsConfirmOpen(false)}
          onConfirm={() => {
            setIsConfirmOpen(false);
            toast.success('Đã nộp bài thi thành công!');
          }}
          title="Xác nhận nộp bài thi sớm?"
          description="Bạn còn 3 câu chưa hoàn thành. Bạn có chắc chắn muốn nộp bài ngay bây giờ không?"
          confirmText="Nộp bài ngay"
          variant="danger"
        />
      </div>
    </div>
  );
};
