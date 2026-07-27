import '@testing-library/jest-dom/vitest'

// jsdom doesn't implement matchMedia; stub it so components reading
// prefers-color-scheme (e.g. for chart colours) don't crash under test.
window.matchMedia ??= (query: string) => ({
  matches: false,
  media: query,
  onchange: null,
  addListener: () => {},
  removeListener: () => {},
  addEventListener: () => {},
  removeEventListener: () => {},
  dispatchEvent: () => false,
})
