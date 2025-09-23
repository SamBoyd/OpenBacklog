import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'

const originalConsoleInfo = console.info;
const originalConsoleError = console.error;

// runs a clean after each test case (e.g. clearing jsdom)
afterEach(() => {
  cleanup();
  console.info = vi.fn()
  console.error = vi.fn();
})

afterAll(() => {
    console.info = originalConsoleInfo
    console.error = originalConsoleError;
});
