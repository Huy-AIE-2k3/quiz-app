import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from './App';

describe('TC-0.1-01: Frontend App Initial Rendering', () => {
  it('renders application heading correctly', () => {
    render(<App />);
    expect(screen.getByText('MATHRIX')).toBeInTheDocument();
    expect(screen.getByText(/Test đến đâu/i)).toBeInTheDocument();
    expect(screen.getByText(/hiểu mình đến đó/i)).toBeInTheDocument();
  });
});

