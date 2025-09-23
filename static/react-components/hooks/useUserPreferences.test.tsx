import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, RenderHookResult } from '@testing-library/react';
import { useUserPreferences, Theme } from './useUserPreferences';
import { UserPreferencesProvider } from '#hooks/useUserPreferences';

// Mock localStorage
const localStorageMock = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    clear: vi.fn(),
};

describe.skip('useUserPreferences', () => {
    beforeEach(() => {
        // Reset all mocks before each test
        vi.clearAllMocks();

        // Setup localStorage mock
        global.localStorage = localStorageMock as any;

        // Reset document body classes
        document.body.className = '';
    });

    describe.skip('Provider', () => {
        it('should initialize with light theme when no localStorage value exists', () => {
            localStorageMock.getItem.mockReturnValue(null);

            const { result } = renderHook(() => useUserPreferences(), {
                wrapper: UserPreferencesProvider,
            });

            expect(result.current.preferences.theme).toBe(Theme.LIGHT);
            expect(document.body.classList.contains('dark')).toBe(false);
        });

        it('should initialize with dark theme when localStorage has dark theme', () => {
            localStorageMock.getItem.mockReturnValue(Theme.DARK);

            const { result } = renderHook(() => useUserPreferences(), {
                wrapper: UserPreferencesProvider,
            });

            expect(result.current.preferences.theme).toBe(Theme.DARK);
            expect(document.body.classList.contains('dark')).toBe(true);
        });

        it('should not add dark class when root element has dark class already', () => {
            document.body.classList.add('dark');

            const { result } = renderHook(() => useUserPreferences(), {
                wrapper: UserPreferencesProvider,
            });

            expect(result.current.preferences.theme).toBe(Theme.DARK);
            // expect only one dark class
            expect(document.body.classList.length).toBe(1);
            expect(document.body.classList.contains('dark')).toBe(true);
        });

        it('should toggle theme and update localStorage', () => {
            localStorageMock.getItem.mockReturnValue(Theme.LIGHT);

            const { result } = renderHook(() => useUserPreferences(), {
                wrapper: UserPreferencesProvider,
            });

            act(() => {
                result.current.toggleTheme();
            });

            expect(result.current.preferences.theme).toBe(Theme.DARK);
            expect(localStorageMock.setItem).toHaveBeenCalledWith('theme', Theme.DARK);
        });

        it('should update document body class when theme changes', () => {
            localStorageMock.getItem.mockReturnValue(Theme.LIGHT);

            const { result } = renderHook(() => useUserPreferences(), {
                wrapper: UserPreferencesProvider,
            });

            act(() => {
                result.current.toggleTheme();
            });

            expect(document.body.classList.contains('dark')).toBe(true);
        });

        it('should remove dark class when switching to light theme', () => {
            localStorageMock.getItem.mockReturnValue(Theme.DARK);

            const { result } = renderHook(() => useUserPreferences(), {
                wrapper: UserPreferencesProvider,
            });

            act(() => {
                result.current.toggleTheme();
            });

            expect(document.body.classList.contains('dark')).toBe(false);
        });

        it('should persist and toggle initiativesShowListView', () => {
            localStorageMock.getItem.mockImplementation((key) => {
                if (key === 'initiativesShowListView') return 'false';
                return null;
            });

            const { result } = renderHook(() => useUserPreferences(), {
                wrapper: UserPreferencesProvider,
            });

            expect(result.current.preferences.initiativesShowListView).toBe(false);

            act(() => {
                result.current.updateInitiativesShowListView(true);
            });

            expect(result.current.preferences.initiativesShowListView).toBe(true);
            expect(localStorageMock.setItem).toHaveBeenCalledWith('initiativesShowListView', 'true');
        });

        it('should persist and toggle tasksShowListView', () => {
            localStorageMock.getItem.mockImplementation((key) => {
                if (key === 'tasksShowListView') return 'false';
                return null;
            });

            const { result } = renderHook(() => useUserPreferences(), {
                wrapper: UserPreferencesProvider,
            });

            expect(result.current.preferences.tasksShowListView).toBe(false);

            act(() => {
                result.current.updateTasksShowListView(true);
            });

            expect(result.current.preferences.tasksShowListView).toBe(true);
            expect(localStorageMock.setItem).toHaveBeenCalledWith('tasksShowListView', 'true');
        });

        it('should persist and toggle viewInitiativeShowListView', () => {
            localStorageMock.getItem.mockImplementation((key) => {
                if (key === 'viewInitiativeShowListView') return 'true';
                return null;
            });

            const { result } = renderHook(() => useUserPreferences(), {
                wrapper: UserPreferencesProvider,
            });

            expect(result.current.preferences.viewInitiativeShowListView).toBe(true);

            act(() => {
                result.current.updateViewInitiativeShowListView(false);
            });

            expect(result.current.preferences.viewInitiativeShowListView).toBe(false);
            expect(localStorageMock.setItem).toHaveBeenCalledWith('viewInitiativeShowListView', 'false');
        });
    });

    describe.skip('Hook', () => {

        it('should provide access to preferences and toggleTheme function', () => {
            const { result } = renderHook(() => useUserPreferences(), {
                wrapper: UserPreferencesProvider,
            });

            expect(result.current).toHaveProperty('preferences');
            expect(result.current).toHaveProperty('toggleTheme');
            expect(typeof result.current.toggleTheme).toBe('function');
        });
    });
});
