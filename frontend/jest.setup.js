import '@testing-library/jest-dom';

// Mock DOM APIs
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock WebContainer API
jest.mock('@webcontainer/api', () => ({
  WebContainer: {
    boot: jest.fn().mockResolvedValue({
      fs: {
        mkdir: jest.fn().mockResolvedValue(undefined),
        writeFile: jest.fn().mockResolvedValue(undefined),
        readFile: jest.fn().mockResolvedValue(''),
        readdir: jest.fn().mockResolvedValue([]),
      },
      spawn: jest.fn().mockResolvedValue({
        output: {
          pipeTo: jest.fn(),
        },
        exit: Promise.resolve(0),
      }),
      port: {
        waitForPort: jest.fn().mockResolvedValue('http://localhost:3000'),
      },
      mount: jest.fn().mockResolvedValue(undefined),
      teardown: jest.fn().mockResolvedValue(undefined),
    }),
  },
}));