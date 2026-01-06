import React, {
  createContext,
  useState,
  useEffect,
  useCallback,
  useMemo,
  ReactNode,
  useContext,
} from 'react';

/**
 * Theme options for the application
 */
export enum Theme {
  LIGHT = 'light',
  DARK = 'dark',
}

export type CompactnessLevel = 'spacious' | 'normal' | 'compact';

export interface UserPreferences {
  theme: Theme;
  filterTasksToInitiative: string | null;
  selectedGroupIds: string[];
  selectedInitiativeStatuses: string[];
  selectedTaskStatuses: string[];
  selectedThemeIds: string[];
  compactnessLevel: CompactnessLevel;
  initiativesShowListView: boolean;
  tasksShowListView: boolean;
  viewInitiativeShowListView: boolean;
}

/**
 * Type validator functions for localStorage values
 */
type TypeValidator<T> = (value: unknown) => value is T;

/**
 * Interface for cached data with TTL
 */
interface CachedData<T> {
  value: T;
  timestamp: number;
  ttl?: number; // TTL in milliseconds, optional for permanent cache
}

/**
 * Safe storage utility for localStorage operations with type validation, user-scoping, and TTL support
 */
export class SafeStorage {
  /**
   * Safely retrieves and validates a value from localStorage
   * @param key - The localStorage key
   * @param validator - Function to validate the type
   * @param defaultValue - Default value to return if validation fails
   * @returns The validated value or default value
   */
  static safeGet<T>(key: string, validator: TypeValidator<T>, defaultValue: T): T {
    if (typeof window === 'undefined') {
      return defaultValue;
    }

    try {
      const storedValue = localStorage.getItem(key);
      if (storedValue === null) {
        return defaultValue;
      }

      // Try to parse as JSON first
      let parsedValue: unknown;
      try {
        parsedValue = JSON.parse(storedValue);
      } catch {
        // If JSON parsing fails, use the raw string
        parsedValue = storedValue;
      }

      // Validate the type
      if (validator(parsedValue)) {
        return parsedValue;
      } else {
        console.warn(`Invalid type for localStorage key "${key}". Using default value.`);
        // Set the default value back to localStorage to fix the corrupted state
        this.safeSet(key, defaultValue);
        return defaultValue;
      }
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error);
      // Set the default value back to localStorage
      this.safeSet(key, defaultValue);
      return defaultValue;
    }
  }

  /**
   * Safely sets a value in localStorage
   * @param key - The localStorage key
   * @param value - The value to store
   */
  static safeSet<T>(key: string, value: T): void {
    if (typeof window === 'undefined') {
      return;
    }

    try {
      const serializedValue = typeof value === 'string' ? value : JSON.stringify(value);
      localStorage.setItem(key, serializedValue);
    } catch (error) {
      console.error(`Error writing to localStorage key "${key}":`, error);
    }
  }

  /**
   * Safely retrieves a user-scoped cached value with TTL support
   * @param baseKey - The base localStorage key
   * @param userId - The user ID to scope the cache to
   * @param validator - Function to validate the cached value type
   * @param defaultValue - Default value to return if cache is invalid/expired
   * @returns The cached value or default value
   */
  static safeGetUserScoped<T>(
    baseKey: string,
    userId: string | null,
    validator: TypeValidator<T>,
    defaultValue: T
  ): T {
    if (typeof window === 'undefined' || !userId) {
      return defaultValue;
    }

    const key = `${baseKey}-${userId}`;
    return this.safeGetWithTTL(key, validator, defaultValue);
  }

  /**
   * Safely sets a user-scoped cached value with TTL
   * @param baseKey - The base localStorage key
   * @param userId - The user ID to scope the cache to
   * @param value - The value to cache
   * @param ttlMs - Time to live in milliseconds (optional, no expiry if not provided)
   */
  static safeSetUserScoped<T>(
    baseKey: string,
    userId: string | null,
    value: T,
    ttlMs?: number
  ): void {
    if (typeof window === 'undefined' || !userId) {
      return;
    }

    const key = `${baseKey}-${userId}`;
    this.safeSetWithTTL(key, value, ttlMs);
  }

  /**
   * Safely retrieves a cached value with TTL support
   * @param key - The localStorage key
   * @param validator - Function to validate the cached value type
   * @param defaultValue - Default value to return if cache is invalid/expired
   * @returns The cached value or default value
   */
  static safeGetWithTTL<T>(
    key: string,
    validator: TypeValidator<T>,
    defaultValue: T
  ): T {
    if (typeof window === 'undefined') {
      return defaultValue;
    }

    try {
      const storedValue = localStorage.getItem(key);
      if (storedValue === null) {
        return defaultValue;
      }

      const cachedData: CachedData<T> = JSON.parse(storedValue);

      // Check if cache has expired
      if (cachedData.ttl && (Date.now() - cachedData.timestamp) > cachedData.ttl) {
        // Cache expired, remove it and return default
        localStorage.removeItem(key);
        return defaultValue;
      }

      // Validate the cached value
      if (validator(cachedData.value)) {
        return cachedData.value;
      } else {
        console.warn(`Invalid cached value type for key "${key}". Using default value.`);
        localStorage.removeItem(key);
        return defaultValue;
      }
    } catch (error) {
      console.error(`Error reading cached value for key "${key}":`, error);
      // Remove corrupted cache entry
      try {
        localStorage.removeItem(key);
      } catch (removeError) {
        console.error(`Error removing corrupted cache for key "${key}":`, removeError);
      }
      return defaultValue;
    }
  }

  /**
   * Safely sets a cached value with TTL
   * @param key - The localStorage key
   * @param value - The value to cache
   * @param ttlMs - Time to live in milliseconds (optional, no expiry if not provided)
   */
  static safeSetWithTTL<T>(key: string, value: T, ttlMs?: number): void {
    if (typeof window === 'undefined') {
      return;
    }

    try {
      const cachedData: CachedData<T> = {
        value,
        timestamp: Date.now(),
        ...(ttlMs ? { ttl: ttlMs } : {})
      };
      
      const serializedValue = JSON.stringify(cachedData);
      localStorage.setItem(key, serializedValue);
    } catch (error) {
      console.error(`Error caching value for key "${key}":`, error);
    }
  }

  /**
   * Clears all cached data for a specific user
   * @param userId - The user ID whose cache should be cleared
   */
  static clearUserCache(userId: string | null): void {
    if (typeof window === 'undefined' || !userId) {
      return;
    }

    try {
      const keys = Object.keys(localStorage);
      const userCacheKeys = keys.filter(key => key.includes(`-${userId}`));
      
      userCacheKeys.forEach(key => {
        try {
          localStorage.removeItem(key);
        } catch (error) {
          console.error(`Error removing cache key "${key}":`, error);
        }
      });
      
      console.debug(`Cleared ${userCacheKeys.length} cache entries for user ${userId}`);
    } catch (error) {
      console.error(`Error clearing user cache for user ${userId}:`, error);
    }
  }

  /**
   * Clears all expired cache entries from localStorage
   */
  static clearExpiredCache(): void {
    if (typeof window === 'undefined') {
      return;
    }

    try {
      const keys = Object.keys(localStorage);
      let clearedCount = 0;

      keys.forEach(key => {
        try {
          const storedValue = localStorage.getItem(key);
          if (!storedValue) return;

          const cachedData: CachedData<unknown> = JSON.parse(storedValue);
          
          // Check if this is a TTL cache entry and if it's expired
          if (cachedData.ttl && (Date.now() - cachedData.timestamp) > cachedData.ttl) {
            localStorage.removeItem(key);
            clearedCount++;
          }
        } catch (error) {
          // Not a valid cache entry or corrupted, skip
        }
      });

      if (clearedCount > 0) {
        console.debug(`Cleared ${clearedCount} expired cache entries`);
      }
    } catch (error) {
      console.error('Error clearing expired cache:', error);
    }
  }
}

/**
 * Type validators for user preferences
 */
const validators = {
  theme: (value: unknown): value is Theme =>
    typeof value === 'string' && Object.values(Theme).includes(value as Theme),

  filterTasksToInitiative: (value: unknown): value is string | null =>
    value === null || typeof value === 'string',


  selectedGroupIds: (value: unknown): value is string[] =>
    Array.isArray(value) && value.every(item => typeof item === 'string'),

  selectedInitiativeStatuses: (value: unknown): value is string[] =>
    Array.isArray(value) && value.every(item => typeof item === 'string'),

  selectedTaskStatuses: (value: unknown): value is string[] =>
    Array.isArray(value) && value.every(item => typeof item === 'string'),

  selectedThemeIds: (value: unknown): value is string[] =>
    Array.isArray(value) && value.every(item => typeof item === 'string'),

  compactnessLevel: (value: unknown): value is CompactnessLevel =>
    typeof value === 'string' && ['spacious', 'normal', 'compact'].includes(value),

  initiativesShowListView: (value: unknown): value is boolean =>
    typeof value === 'boolean',

  tasksShowListView: (value: unknown): value is boolean =>
    typeof value === 'boolean',

  viewInitiativeShowListView: (value: unknown): value is boolean =>
    typeof value === 'boolean',
};

/**
 * Default preferences for use when no saved values exist or validation fails
 */
const defaultPreferences: UserPreferences = {
  theme: Theme.DARK,
  filterTasksToInitiative: null,
  selectedGroupIds: ['all-pseudo-group'],
  selectedInitiativeStatuses: ['BACKLOG', 'TO_DO', 'IN_PROGRESS'],
  selectedTaskStatuses: ['BACKLOG', 'TO_DO', 'IN_PROGRESS'],
  selectedThemeIds: ['all-prioritized-themes'],
  compactnessLevel: 'normal',
  initiativesShowListView: false,
  tasksShowListView: false,
  viewInitiativeShowListView: true,
};

// Default preferences for use when no saved values exist
const loadPreferencesFromLocalStorage = (): UserPreferences => {
  return {
    theme: SafeStorage.safeGet('theme', validators.theme, defaultPreferences.theme),
    filterTasksToInitiative: SafeStorage.safeGet('filterTasksToInitiative', validators.filterTasksToInitiative, defaultPreferences.filterTasksToInitiative),
    selectedGroupIds: SafeStorage.safeGet('selectedGroupIds', validators.selectedGroupIds, defaultPreferences.selectedGroupIds),
    selectedInitiativeStatuses: SafeStorage.safeGet('selectedInitiativeStatuses', validators.selectedInitiativeStatuses, defaultPreferences.selectedInitiativeStatuses),
    selectedTaskStatuses: SafeStorage.safeGet('selectedTaskStatuses', validators.selectedTaskStatuses, defaultPreferences.selectedTaskStatuses),
    selectedThemeIds: SafeStorage.safeGet('selectedThemeIds', validators.selectedThemeIds, defaultPreferences.selectedThemeIds),
    compactnessLevel: SafeStorage.safeGet('ui-compactness-level', validators.compactnessLevel, defaultPreferences.compactnessLevel),
    initiativesShowListView: SafeStorage.safeGet('initiativesShowListView', validators.initiativesShowListView, defaultPreferences.initiativesShowListView),
    tasksShowListView: SafeStorage.safeGet('tasksShowListView', validators.tasksShowListView, defaultPreferences.tasksShowListView),
    viewInitiativeShowListView: SafeStorage.safeGet('viewInitiativeShowListView', validators.viewInitiativeShowListView, defaultPreferences.viewInitiativeShowListView),
  };
};

export interface UserPreferencesContextType {
  preferences: UserPreferences;
  toggleTheme: () => void;
  updateFilterTasksToInitiative: (initiativeId: string | null) => void;
  updateSelectedGroups: (groupIds: string[]) => void;
  updateSelectedInitiativeStatuses: (statuses: string[]) => void;
  updateSelectedTaskStatuses: (statuses: string[]) => void;
  updateSelectedThemes: (themeIds: string[]) => void;
  updateCompactnessLevel: (level: CompactnessLevel) => void;
  updateInitiativesShowListView: (show: boolean) => void;
  updateTasksShowListView: (show: boolean) => void;
  updateViewInitiativeShowListView: (show: boolean) => void;
}

// Create the context with a default value
const UserPreferencesContext = createContext<UserPreferencesContextType>({
  preferences: defaultPreferences,
  toggleTheme: () => { console.warn('UserPreferencesProvider not found'); },
  updateFilterTasksToInitiative: () => { console.warn('UserPreferencesProvider not found'); },
  updateSelectedGroups: () => { console.warn('UserPreferencesProvider not found'); },
  updateSelectedInitiativeStatuses: () => { console.warn('UserPreferencesProvider not found'); },
  updateSelectedTaskStatuses: () => { console.warn('UserPreferencesProvider not found'); },
  updateSelectedThemes: () => { console.warn('UserPreferencesProvider not found'); },
  updateCompactnessLevel: () => { console.warn('UserPreferencesProvider not found'); },
  updateInitiativesShowListView: () => { console.warn('UserPreferencesProvider not found'); },
  updateTasksShowListView: () => { console.warn('UserPreferencesProvider not found'); },
  updateViewInitiativeShowListView: () => { console.warn('UserPreferencesProvider not found'); },
});

export interface UserPreferencesProviderProps {
  initialPreferences?: UserPreferences;
  children: ReactNode;
}

/**
 * Provider component that manages and distributes user preferences state.
 * @param {UserPreferencesProviderProps} props - Component props.
 * @param {ReactNode} props.children - Child components to be wrapped by the provider.
 * @returns {React.ReactElement} The provider component.
 */
export const UserPreferencesProvider: React.FC<UserPreferencesProviderProps> = ({ children, initialPreferences }) => {
  // Initialize state with a default value first
  const [preferences, setPreferences] = useState<UserPreferences>(initialPreferences || defaultPreferences);
  const [isInitialLoad, setIsInitialLoad] = useState(true);

  // Load preferences from localStorage in an effect to ensure browser-only execution
  useEffect(() => {
    if (typeof window !== 'undefined' && !initialPreferences) {
      const loadedPrefs = loadPreferencesFromLocalStorage();
      setPreferences(loadedPrefs);
    }
  }, [initialPreferences]);

  // Toggle between light and dark themes
  const toggleTheme = useCallback(() => {
    setPreferences((prev) => {
      const newTheme = prev.theme === Theme.LIGHT ? Theme.DARK : Theme.LIGHT;
      return { ...prev, theme: newTheme };
    });
  }, []);

  const updateFilterTasksToInitiative = useCallback((filterTasksToInitiative: string | null) => {
    setPreferences((prev) => {
      return { ...prev, filterTasksToInitiative };
    });
  }, []);


  const updateSelectedGroups = useCallback((selectedGroupIds: string[]) => {
    setPreferences((prev) => {
      return { ...prev, selectedGroupIds };
    });
  }, []);

  const updateSelectedInitiativeStatuses = useCallback((selectedInitiativeStatuses: string[]) => {
    setPreferences((prev) => {
      return { ...prev, selectedInitiativeStatuses };
    });
  }, []);

  const updateSelectedTaskStatuses = useCallback((selectedTaskStatuses: string[]) => {
    setPreferences((prev) => {
      return { ...prev, selectedTaskStatuses };
    });
  }, []);

  const updateSelectedThemes = useCallback((selectedThemeIds: string[]) => {
    setPreferences((prev) => {
      return { ...prev, selectedThemeIds };
    });
  }, []);

  const updateCompactnessLevel = useCallback((level: CompactnessLevel) => {
    setPreferences((prev) => {
      return { ...prev, compactnessLevel: level };
    });
  }, []);

  const updateInitiativesShowListView = useCallback((initiativesShowListView: boolean) => {
    setPreferences((prev) => {
      return { ...prev, initiativesShowListView };
    });
  }, []);

  const updateTasksShowListView = useCallback((tasksShowListView: boolean) => {
    setPreferences((prev) => {
      return { ...prev, tasksShowListView };
    });
  }, []);

  const updateViewInitiativeShowListView = useCallback((viewInitiativeShowListView: boolean) => {
    setPreferences((prev) => {
      return { ...prev, viewInitiativeShowListView };
    });
  }, []);

  // Update localStorage and document class when theme changes
  useEffect(() => {
    if (isInitialLoad) {
      setIsInitialLoad(false);
      return;
    }

    if (typeof window !== 'undefined') {
      // Save to localStorage using safe storage utility
      SafeStorage.safeSet('theme', preferences.theme);
      SafeStorage.safeSet('filterTasksToInitiative', preferences.filterTasksToInitiative);
      SafeStorage.safeSet('selectedGroupIds', preferences.selectedGroupIds);
      SafeStorage.safeSet('selectedInitiativeStatuses', preferences.selectedInitiativeStatuses);
      SafeStorage.safeSet('selectedTaskStatuses', preferences.selectedTaskStatuses);
      SafeStorage.safeSet('selectedThemeIds', preferences.selectedThemeIds);
      SafeStorage.safeSet('ui-compactness-level', preferences.compactnessLevel);
      SafeStorage.safeSet('initiativesShowListView', preferences.initiativesShowListView);
      SafeStorage.safeSet('tasksShowListView', preferences.tasksShowListView);
      SafeStorage.safeSet('viewInitiativeShowListView', preferences.viewInitiativeShowListView);

      // Update document class for global CSS or Tailwind theming
      const root = document.body;
      if (preferences.theme === Theme.DARK) {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
    }
  }, [preferences]);

  // Memoize the context value to prevent unnecessary re-renders
  const value = useMemo(() => ({
    preferences,
    toggleTheme,
    updateFilterTasksToInitiative,
    updateSelectedGroups,
    updateSelectedInitiativeStatuses,
    updateSelectedTaskStatuses,
    updateSelectedThemes,
    updateCompactnessLevel,
    updateInitiativesShowListView,
    updateTasksShowListView,
    updateViewInitiativeShowListView,
  }), [preferences, toggleTheme, updateFilterTasksToInitiative, updateSelectedGroups, updateSelectedInitiativeStatuses, updateSelectedTaskStatuses, updateSelectedThemes, updateCompactnessLevel, updateInitiativesShowListView, updateTasksShowListView, updateViewInitiativeShowListView]);

  return (
    <UserPreferencesContext.Provider value={value}>
      {children}
    </UserPreferencesContext.Provider>
  );
};

export interface UseUserPreferencesReturn {
  preferences: UserPreferences;
  toggleTheme: () => void;
  updateFilterTasksToInitiative: (initiativeId: string | null) => void;
  updateSelectedGroups: (groupIds: string[]) => void;
  updateSelectedInitiativeStatuses: (statuses: string[]) => void;
  updateSelectedTaskStatuses: (statuses: string[]) => void;
  updateSelectedThemes: (themeIds: string[]) => void;
  updateCompactnessLevel: (level: CompactnessLevel) => void;
  updateInitiativesShowListView: (show: boolean) => void;
  updateTasksShowListView: (show: boolean) => void;
  updateViewInitiativeShowListView: (show: boolean) => void;
}

/**
 * Hook for accessing shared user preferences, including theme.
 * Must be used within a UserPreferencesProvider.
 * @returns {UseUserPreferencesReturn} Object containing user preferences and the theme toggle function.
 */
export function useUserPreferences(): UseUserPreferencesReturn {
  const context = useContext(UserPreferencesContext);

  // The context provides a default value, so technically context should never be undefined.
  // However, adding a check can be good practice for robustness or if you remove the default value later.
  if (context === undefined) {
    // This should ideally not happen if the default value is set in createContext
    throw new Error('useUserPreferences must be used within a UserPreferencesProvider');
  }

  return context;
}
