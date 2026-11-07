/**
 * Mock data for UI showcase, development and component demonstration.
 */

export const mockQuestions = Array.from({ length: 25 }, (_, i) => {
  const num = i + 1;
  let status: 'unanswered' | 'answered' | 'flagged' = 'unanswered';
  if (num <= 10) status = 'answered';
  else if (num === 11 || num === 15) status = 'flagged';

  return {
    id: `q-${num}`,
    number: num,
    status,
    point: 0.2,
  };
});

export const mockStudentRoster = [
  { id: '1', code: 'HS2025-001', name: 'Nguyễn Văn An', gender: 'Nam', dob: '15/03/2007', class: '12A1', status: 'Hoạt động' },
  { id: '2', code: 'HS2025-002', name: 'Trần Thị Bình', gender: 'Nữ', dob: '22/07/2007', class: '12A1', status: 'Hoạt động' },
  { id: '3', code: 'HS2025-003', name: 'Lê Hoàng Cường', gender: 'Nam', dob: '04/11/2007', class: '12A1', status: 'Chưa kích hoạt' },
  { id: '4', code: 'HS2025-004', name: 'Phạm Minh Đức', gender: 'Nam', dob: '19/01/2007', class: '12A1', status: 'Hoạt động' },
  { id: '5', code: 'HS2025-005', name: 'Vũ Ngọc Hân', gender: 'Nữ', dob: '30/09/2007', class: '12A1', status: 'Hoạt động' },
];

export const mockClasses = [
  { id: 'c1', name: 'Chuyên Toán 12T1', grade: 12, totalStudents: 35, activeExams: 3 },
  { id: 'c2', name: 'Chuyên Tin 12Tin', grade: 12, totalStudents: 32, activeExams: 4 },
  { id: 'c3', name: 'Toán 11A1 Cơ Bản', grade: 11, totalStudents: 40, activeExams: 1 },
];
