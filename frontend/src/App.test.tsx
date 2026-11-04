import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from './App';

describe('TC-0.1-01: Frontend App Initial Rendering', () => {
  it('renders application heading correctly', () => {
    render(<App />);
    expect(screen.getByText('Quiz Toán - Tin')).toBeInTheDocument();
    expect(screen.getByText(/Hệ thống kiểm tra trực tuyến nội bộ/i)).toBeInTheDocument();
  });
});

