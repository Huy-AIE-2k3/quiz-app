import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from './App'

describe('App component', () => {
  it('renders MATHRIX title and system status', () => {
    render(<App />)
    expect(screen.getByText('MATHRIX')).toBeInTheDocument()
    expect(screen.getByText('MATHRIX SYSTEM ONLINE')).toBeInTheDocument()
  })
})
