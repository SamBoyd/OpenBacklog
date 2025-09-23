import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ActiveEntityProvider, useActiveEntity } from './useActiveEntity';
import React from 'react';

// Helper component to wrap the hook with the provider
const wrapper = ({ children }: { children: React.ReactNode }) => (
    <ActiveEntityProvider>{children}</ActiveEntityProvider>
);


describe.skip('useActiveEntity', () => {
    it('should set the active entity to the initiative id', () => {
        const { result } = renderHook(() => useActiveEntity(), { wrapper });

        act(() => {
            result.current.setActiveInitiative('initiative-123');
        });

        expect(result.current.activeInitiativeId).toBe('initiative-123');
        expect(result.current.activeTaskId).toBeNull();
    })

    it('should set the active entity to the task id', () => {
        const { result } = renderHook(() => useActiveEntity(), { wrapper });

        act(() => {
            result.current.setActiveTask('task-456');
        });

        expect(result.current.activeTaskId).toBe('task-456');
        expect(result.current.activeInitiativeId).toBeNull();
    })

    it('should clear the active entity when initiative was active', () => {
        const { result } = renderHook(() => useActiveEntity(), { wrapper });

        // Set an initial active entity
        act(() => {
            result.current.setActiveInitiative('initiative-789');
        });
        expect(result.current.activeInitiativeId).toBe('initiative-789'); // Verify it's set

        // Clear the active entity
        act(() => {
            result.current.clearActiveEntity();
        });

        expect(result.current.activeInitiativeId).toBeNull();
        expect(result.current.activeTaskId).toBeNull();
    })

    it('should clear the active entity when task was active', () => {
        const { result } = renderHook(() => useActiveEntity(), { wrapper });

        // Set an initial active entity
        act(() => {
            result.current.setActiveTask('task-abc');
        });
        expect(result.current.activeTaskId).toBe('task-abc'); // Verify it's set

        // Clear the active entity
        act(() => {
            result.current.clearActiveEntity();
        });

        expect(result.current.activeInitiativeId).toBeNull();
        expect(result.current.activeTaskId).toBeNull();
    })

    it('should switch from initiative to task', () => {
        const { result } = renderHook(() => useActiveEntity(), { wrapper });

        act(() => {
            result.current.setActiveInitiative('initiative-1');
        });
        expect(result.current.activeInitiativeId).toBe('initiative-1');
        expect(result.current.activeTaskId).toBeNull();

        act(() => {
            result.current.setActiveTask('task-1');
        });
        expect(result.current.activeInitiativeId).toBeNull();
        expect(result.current.activeTaskId).toBe('task-1');
    })

    it('should switch from task to initiative', () => {
        const { result } = renderHook(() => useActiveEntity(), { wrapper });

        act(() => {
            result.current.setActiveTask('task-2');
        });
        expect(result.current.activeTaskId).toBe('task-2');
        expect(result.current.activeInitiativeId).toBeNull();


        act(() => {
            result.current.setActiveInitiative('initiative-2');
        });
        expect(result.current.activeTaskId).toBeNull();
        expect(result.current.activeInitiativeId).toBe('initiative-2');
    })

    it('should throw an error if used outside of provider', () => {
        // Hide console error for this specific test
        const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => { });

        expect(() => renderHook(() => useActiveEntity())).toThrow(
            'useActiveEntity must be used within an ActiveEntityProvider'
        );

        // Restore console error
        consoleErrorSpy.mockRestore();
    });
});