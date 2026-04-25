---
name: react-code-generation-pro
description: Advanced React code generation and optimization. Specialized in React components, hooks, state management, performance optimization, and modern React patterns.
---

# React Code Generation Pro - Advanced React Development Intelligence

Comprehensive React code generation system for modern web applications. Specialized in React 18+, hooks, performance optimization, and best practices for production-ready applications.

## When to Apply

Use this skill when:
- Generating React components and applications
- Implementing complex React patterns and hooks
- Optimizing React performance and bundle size
- Converting designs to React implementations
- Setting up React project architecture
- Implementing state management solutions

## React Architecture Patterns

### Component Architecture

#### Atomic Design Structure
```
src/
├── components/
│   ├── atoms/          # Basic UI components (Button, Input, Icon)
│   ├── molecules/      # Combined atoms (SearchForm, UserCard)
│   ├── organisms/      # Complex components (Header, Sidebar, Modal)
│   ├── templates/      # Page layouts
│   └── pages/          # Page components
├── hooks/              # Custom React hooks
├── contexts/          # React contexts
├── utils/              # Utility functions
└── types/              # TypeScript definitions
```

#### Component Design Patterns

**1. Function Component with Hooks (Recommended)**
```tsx
// Modern React component pattern
interface ButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
  disabled?: boolean;
  loading?: boolean;
}

const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  onClick,
  disabled = false,
  loading = false,
}) => {
  const [isHovered, setIsHovered] = useState(false);
  
  const handleClick = useCallback(() => {
    if (!disabled && !loading && onClick) {
      onClick();
    }
  }, [disabled, loading, onClick]);

  const baseClasses = 'inline-flex items-center justify-center font-medium transition-colors duration-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2';
  
  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
  };
  
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${disabled || loading ? 'opacity-50 cursor-not-allowed' : ''}`}
      onClick={handleClick}
      disabled={disabled || loading}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {loading ? (
        <>
          <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          Loading...
        </>
      ) : (
        children
      )}
    </button>
  );
};
```

**2. Custom Hook Pattern**
```tsx
// Custom hook for API data fetching
interface UseApiOptions<T> {
  url: string;
  initialData?: T;
  autoFetch?: boolean;
}

interface UseApiResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

function useApi<T = any>({
  url,
  initialData = null,
  autoFetch = true,
}: UseApiOptions<T>): UseApiResult<T> {
  const [data, setData] = useState<T | null>(initialData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, [url]);

  useEffect(() => {
    if (autoFetch) {
      fetchData();
    }
  }, [fetchData, autoFetch]);

  return { data, loading, error, refetch: fetchData };
}

// Usage in component
const UserProfile: React.FC<{ userId: string }> = ({ userId }) => {
  const { data: user, loading, error, refetch } = useApi<User>({
    url: `/api/users/${userId}`,
  });

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!user) return <div>User not found</div>;

  return (
    <div className="user-profile">
      <h1>{user.name}</h1>
      <p>{user.email}</p>
      <button onClick={refetch}>Refresh</button>
    </div>
  );
};
```

### State Management Patterns

#### Context API for Global State
```tsx
// Theme context example
interface ThemeContextType {
  theme: 'light' | 'dark';
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  const toggleTheme = useCallback(() => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  }, []);

  const value = useMemo(() => ({ theme, toggleTheme }), [theme, toggleTheme]);

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
```

#### Zustand for Complex State (Alternative to Redux)
```tsx
// store/userStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UserState {
  user: User | null;
  isAuthenticated: boolean;
  login: (user: User) => void;
  logout: () => void;
  updateUser: (updates: Partial<User>) => void;
}

export const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      login: (user) => set({ user, isAuthenticated: true }),
      logout: () => set({ user: null, isAuthenticated: false }),
      updateUser: (updates) => set((state) => ({
        user: state.user ? { ...state.user, ...updates } : null,
      })),
    }),
    {
      name: 'user-storage',
    }
  )
);
```

## React Performance Optimization

### Memoization Strategies

#### Component Memoization
```tsx
// Optimize expensive components
const ExpensiveComponent = memo(({ data, onItemClick }: ExpensiveComponentProps) => {
  console.log('ExpensiveComponent rendered');
  
  return (
    <div>
      {data.map(item => (
        <div key={item.id} onClick={() => onItemClick(item.id)}>
          {item.name}
        </div>
      ))}
    </div>
  );
});

// Parent component
const ParentComponent = () => {
  const [data, setData] = useState([]);
  const [filter, setFilter] = useState('');
  
  // Memoize callback to prevent unnecessary re-renders
  const handleItemClick = useCallback((id: string) => {
    console.log('Item clicked:', id);
  }, []);
  
  // Memoize filtered data
  const filteredData = useMemo(() => {
    return data.filter(item => item.name.toLowerCase().includes(filter.toLowerCase()));
  }, [data, filter]);
  
  return (
    <div>
      <input 
        value={filter} 
        onChange={(e) => setFilter(e.target.value)} 
        placeholder="Filter items..."
      />
      <ExpensiveComponent 
        data={filteredData} 
        onItemClick={handleItemClick}
      />
    </div>
  );
};
```

#### Custom Hook Optimization
```tsx
// Optimized form handling hook
function useForm<T extends Record<string, any>>(initialValues: T) {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState<Partial<T>>({});
  const [touched, setTouched] = useState<Partial<Record<keyof T, boolean>>>({});

  const setValue = useCallback((name: keyof T, value: any) => {
    setValues(prev => ({ ...prev, [name]: value }));
  }, []);

  const setError = useCallback((name: keyof T, error: string) => {
    setErrors(prev => ({ ...prev, [name]: error }));
  }, []);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setValue(name as keyof T, value);
  }, [setValue]);

  const handleBlur = useCallback((e: React.FocusEvent<HTMLInputElement>) => {
    const { name } = e.target;
    setTouched(prev => ({ ...prev, [name]: true }));
  }, []);

  const reset = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
  }, [initialValues]);

  return {
    values,
    errors,
    touched,
    handleChange,
    handleBlur,
    setValue,
    setError,
    reset,
  };
}
```

### Bundle Size Optimization

#### Code Splitting
```tsx
// Lazy loading components
const LazyComponent = lazy(() => import('./LazyComponent'));
const HeavyComponent = lazy(() => import('./HeavyComponent'));

const App = () => {
  const [showHeavy, setShowHeavy] = useState(false);

  return (
    <div>
      <Suspense fallback={<div>Loading...</div>}>
        <LazyComponent />
      </Suspense>
      
      <button onClick={() => setShowHeavy(true)}>
        Load Heavy Component
      </button>
      
      {showHeavy && (
        <Suspense fallback={<div>Loading heavy component...</div>}>
          <HeavyComponent />
        </Suspense>
      )}
    </div>
  );
};
```

#### Dynamic Imports
```tsx
// Dynamic import for conditional loading
const loadChartLibrary = async () => {
  const { Chart } = await import('heavy-chart-library');
  return Chart;
};

const ChartComponent = () => {
  const [Chart, setChart] = useState<any>(null);

  useEffect(() => {
    loadChartLibrary().then(setChart);
  }, []);

  if (!Chart) return <div>Loading chart...</div>;

  return <Chart data={chartData} />;
};
```

## React Testing Patterns

### Component Testing
```tsx
// __tests__/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '../Button';

describe('Button', () => {
  test('renders button with text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  test('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  test('shows loading state', () => {
    render(<Button loading>Click me</Button>);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
```

### Hook Testing
```tsx
// __tests__/useApi.test.tsx
import { renderHook, act } from '@testing-library/react-hooks';
import { useApi } from '../useApi';

describe('useApi', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  test('fetches data successfully', async () => {
    const mockData = { id: 1, name: 'Test' };
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
    });

    const { result, waitForNextUpdate } = renderHook(() =>
      useApi({ url: '/api/test' })
    );

    expect(result.current.loading).toBe(true);
    
    await waitForNextUpdate();
    
    expect(result.current.loading).toBe(false);
    expect(result.current.data).toEqual(mockData);
    expect(result.current.error).toBeNull();
  });
});
```

## React Best Practices

### TypeScript Integration
```tsx
// Strong typing for components
interface UserCardProps {
  user: {
    id: string;
    name: string;
    email: string;
    avatar?: string;
  };
  onEdit: (user: User) => void;
  onDelete: (id: string) => void;
}

const UserCard: React.FC<UserCardProps> = ({ user, onEdit, onDelete }) => {
  return (
    <div className="user-card">
      <img src={user.avatar || '/default-avatar.png'} alt={user.name} />
      <h3>{user.name}</h3>
      <p>{user.email}</p>
      <div className="actions">
        <button onClick={() => onEdit(user)}>Edit</button>
        <button onClick={() => onDelete(user.id)}>Delete</button>
      </div>
    </div>
  );
};
```

### Error Boundaries
```tsx
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <h2>Something went wrong</h2>
          <p>{this.state.error?.message}</p>
          <button onClick={() => this.setState({ hasError: false, error: undefined })}>
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### Performance Monitoring
```tsx
// Custom hook for performance monitoring
function usePerformanceMonitoring(componentName: string) {
  useEffect(() => {
    const startTime = performance.now();
    
    return () => {
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      
      if (renderTime > 16) { // More than 1 frame at 60fps
        console.warn(`${componentName} took ${renderTime.toFixed(2)}ms to render`);
      }
    };
  });
}

// Usage
const ExpensiveComponent = () => {
  usePerformanceMonitoring('ExpensiveComponent');
  
  return <div>Expensive content</div>;
};
```

## React Project Setup Templates

### Next.js Project Structure
```
my-nextjs-app/
├── app/                    # App router (Next.js 13+)
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home page
│   ├── about/
│   │   └── page.tsx       # About page
│   └── api/              # API routes
├── components/           # Shared components
├── lib/                 # Utility functions
├── hooks/               # Custom hooks
├── contexts/           # React contexts
├── styles/              # Global styles
├── types/               # TypeScript types
└── public/              # Static assets
```

### Create React App Structure
```
my-react-app/
├── src/
│   ├── components/       # Reusable components
│   ├── pages/           # Page components
│   ├── hooks/           # Custom hooks
│   ├── contexts/        # React contexts
│   ├── utils/           # Utility functions
│   ├── services/        # API services
│   ├── types/           # TypeScript types
│   ├── App.tsx          # Root component
│   └── index.tsx        # Entry point
├── public/             # Static assets
└── tests/              # Test files
```

## React Ecosystem Integration

### Styling Solutions
- **CSS Modules**: Scoped CSS for components
- **Styled Components**: CSS-in-JS solution
- **Tailwind CSS**: Utility-first CSS framework
- **Emotion**: Another CSS-in-JS library

### State Management
- **Context API**: Built-in React state management
- **Zustand**: Lightweight state management
- **Redux Toolkit**: Full-featured state management
- **Jotai**: Atomic state management

### Routing
- **React Router**: Standard React routing
- **Next.js Router**: File-based routing
- **TanStack Router**: Type-safe routing

### Forms
- **React Hook Form**: Performant form handling
- **Formik**: Alternative form library
- **Final Form**: Another form solution

This React-specific skill provides comprehensive guidance for generating high-quality React applications with modern patterns, performance optimization, and testing best practices.