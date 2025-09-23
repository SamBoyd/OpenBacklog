# Optimistic Updates Patterns

This document describes reusable patterns for implementing optimistic updates across different hooks in the application.

## Overview

Optimistic updates provide immediate UI feedback by updating the cache before the API call completes. This eliminates UI lag and creates a more responsive user experience, especially for operations like adding, updating, or deleting items in lists.

## Core Implementation: `useOptimisticMutation`

The `useOptimisticMutation` hook (located in `hooks/useOptimisticMutation.tsx`) provides a generalized pattern for implementing optimistic updates with automatic rollback on errors.

### Key Features

- **Immediate Cache Updates**: Updates occur before API calls complete
- **Automatic Rollback**: Failed operations automatically restore previous state
- **Query Cancellation**: Prevents race conditions by canceling outgoing queries
- **Separate Server Response Handling**: Properly applies server-computed fields 
- **Type Safety**: Full TypeScript support with generic types
- **Reusable Helpers**: Utility functions for common patterns

## Implementation Patterns

### Pattern 1: Basic Entity Update

For simple entity updates (like task title changes):

```typescript
const updateMutation = useOptimisticMutation<EntityDto, Error, Partial<EntityDto>>({
    mutationFn: updateEntityApi,
    queryKeysToCancel: (variables) => [['entities', entityId]],
    createOptimisticData: (variables, context) => {
        const existingEntity = context?.previousData?.find(e => e.id === variables.id);
        return existingEntity ? { ...existingEntity, ...variables } : null;
    },
    updateCache: (optimisticEntity) => {
        updateEntityInCache(optimisticEntity);
    },
    captureContext: () => ({
        previousData: queryClient.getQueryData(['entities']),
    }),
    rollbackCache: (context) => {
        if (context.previousData) {
            queryClient.setQueryData(['entities'], context.previousData);
        }
    },
});
```

### Pattern 2: List Operations (Add/Remove)

For operations that modify lists (like adding checklist items):

```typescript
const addItemMutation = useOptimisticMutation<ItemDto, Error, CreateItemRequest>({
    mutationFn: createItemApi,
    queryKeysToCancel: (variables) => [['items', variables.parentId]],
    createOptimisticData: (variables) => ({
        id: `temp-${Date.now()}`, // Temporary ID
        ...variables,
        created_at: new Date().toISOString(),
    }),
    updateCache: (optimisticItem) => {
        queryClient.setQueryData(['items', optimisticItem.parentId], (oldData = []) => 
            [...oldData, optimisticItem]
        );
    },
    onSuccessCallback: (realItem, variables) => {
        // Replace temporary item with real server response
        queryClient.setQueryData(['items', realItem.parentId], (oldData = []) =>
            oldData.map(item => 
                item.id === `temp-${variables.timestamp}` ? realItem : item
            )
        );
    },
});
```

### Pattern 3: Server Response Handling

**Critical Pattern**: Separate optimistic updates from server response handling to preserve computed fields:

```typescript
const updateMutation = useOptimisticMutation<TaskDto, Error, Partial<TaskDto>>({
    mutationFn: postTask,
    
    // Optimistic update - immediate UI feedback
    createOptimisticData: (variables, context) => {
        const existingTask = findExistingTask(variables.id);
        return existingTask ? { ...existingTask, ...variables } : null;
    },
    updateCache: (optimisticTask) => {
        // Quick update for immediate feedback
        updateTaskInCache(optimisticTask);
    },
    
    // Server response - preserve computed fields
    updateCacheWithServerResponse: (serverTask) => {
        // Server response includes computed fields like:
        // - updated_at timestamp
        // - database-generated IDs  
        // - computed order/position values
        // - server-validated data
        updateTaskInCache(serverTask); // Use full server response
    },
    
    // ... rest of config
});
```

### Pattern 4: Create Operations with Temporary IDs

For create operations where optimistic item needs temp ID replacement:

```typescript
const createMutation = useOptimisticMutation<ItemDto, Error, CreateItemRequest>({
    mutationFn: createItemApi,
    
    createOptimisticData: (variables) => ({
        id: `temp-${Date.now()}`, // Temporary ID
        ...variables,
        created_at: new Date().toISOString(), // Optimistic timestamp
        order: 0, // Optimistic guess
    }),
    
    updateCache: (optimisticItem) => {
        // Add optimistic item to list
        queryClient.setQueryData(['items'], (oldData = []) => [...oldData, optimisticItem]);
    },
    
    updateCacheWithServerResponse: (serverItem) => {
        // Replace temp item with real server response
        queryClient.setQueryData(['items'], (oldData = []) =>
            oldData.map(item => 
                item.id.toString().startsWith('temp-') && item.title === serverItem.title
                    ? serverItem // Replace with real ID and computed fields
                    : item
            )
        );
    },
});
```

### Pattern 5: Multi-Cache Updates

For operations that affect multiple cache keys:

```typescript
const cacheUpdater = createEntityListCacheUpdater<TaskDto>([
    ['tasks'],
    ['tasks', initiativeId],
    ['initiatives', initiativeId, 'tasks'],
]);

const serverResponseUpdater = createServerResponseUpdater<TaskDto>([
    ['tasks'],
    ['tasks', initiativeId], 
    ['initiatives', initiativeId, 'tasks'],
]);

const updateMutation = useOptimisticMutation({
    updateCache: cacheUpdater,
    updateCacheWithServerResponse: serverResponseUpdater,
    // ... other config
});
```

## Applying Patterns to Existing Hooks

### useInitiatives Hook

Example implementation for optimistic initiative updates:

```typescript
// In contexts/InitiativesContext.tsx
import { useOptimisticMutation } from '#hooks/useOptimisticMutation';

const updateInitiativeMutation = useOptimisticMutation<
    InitiativeDto, 
    Error, 
    Partial<InitiativeDto>
>({
    mutationFn: postInitiative,
    queryKeysToCancel: (variables) => [
        ['initiatives'],
        ['initiatives', variables.id],
    ],
    createOptimisticData: (variables, context) => {
        const existingInitiatives = queryClient.getQueryData<InitiativeDto[]>(['initiatives']);
        const existingInitiative = existingInitiatives?.find(i => i.id === variables.id);
        return existingInitiative ? { ...existingInitiative, ...variables } : null;
    },
    updateCache: (optimisticInitiative) => {
        // Update main initiatives list
        queryClient.setQueryData<InitiativeDto[]>(['initiatives'], (oldData = []) =>
            oldData.map(initiative => 
                initiative.id === optimisticInitiative.id ? optimisticInitiative : initiative
            )
        );
        // Update single initiative cache
        queryClient.setQueryData(['initiatives', optimisticInitiative.id], optimisticInitiative);
    },
    captureContext: () => ({
        previousInitiatives: queryClient.getQueryData<InitiativeDto[]>(['initiatives']),
    }),
    rollbackCache: (context) => {
        if (context.previousInitiatives) {
            queryClient.setQueryData(['initiatives'], context.previousInitiatives);
        }
    },
});
```

### useWorkspaces Hook

Example for workspace operations:

```typescript
// In hooks/useWorkspaces.tsx
const updateWorkspaceMutation = useOptimisticMutation<
    WorkspaceDto,
    Error,
    Partial<WorkspaceDto>
>({
    mutationFn: updateWorkspaceApi,
    queryKeysToCancel: () => [['workspaces']],
    createOptimisticData: (variables, context) => {
        const existingWorkspace = context?.previousWorkspaces?.find(w => w.id === variables.id);
        return existingWorkspace ? { ...existingWorkspace, ...variables } : null;
    },
    updateCache: createEntityListCacheUpdater<WorkspaceDto>([['workspaces']]),
    captureContext: () => ({
        previousWorkspaces: queryClient.getQueryData<WorkspaceDto[]>(['workspaces']),
    }),
    rollbackCache: createEntityListRollback(
        context => [['workspaces']],
        context => context.previousWorkspaces
    ),
});
```

## Helper Functions

### Available Helpers

1. **`createEntityListCacheUpdater<T>`** - Updates entities in multiple cache keys for optimistic updates
2. **`createServerResponseUpdater<T>`** - Updates entities with server response data  
3. **`createServerResponseReplacer<T>`** - Replaces optimistic items (with temp IDs) with server responses
4. **`createEntityListRollback<T>`** - Creates rollback function for reverting optimistic updates

### Usage Examples

```typescript
// For simple entity updates
const optimisticUpdater = createEntityListCacheUpdater<TaskDto>([
    ['tasks'], ['tasks', initiativeId]
]);
const serverUpdater = createServerResponseUpdater<TaskDto>([
    ['tasks'], ['tasks', initiativeId]  
]);

// For create operations with temp IDs
const serverReplacer = createServerResponseReplacer<ItemDto>(
    [['items'], ['items', parentId]],
    (item, variables) => item.id, // Get optimistic ID
    (item) => item.id // Get entity ID
);

// For error rollback
const rollback = createEntityListRollback<TaskDto>(
    context => context.queryKeys,
    context => context.previousData
);
```

## Best Practices

### 1. Always Provide Rollback

```typescript
// ✅ Good - includes rollback
captureContext: () => ({ previousData: getCurrentData() }),
rollbackCache: (context) => { restoreData(context.previousData); },

// ❌ Bad - no rollback on error
// If API fails, optimistic update remains, causing inconsistent state
```

### 2. Cancel Outgoing Queries

```typescript
// ✅ Good - prevents race conditions
queryKeysToCancel: (variables) => [['entities', variables.id]],

// ❌ Bad - outgoing queries might overwrite optimistic updates
queryKeysToCancel: () => [],
```

### 3. Handle Temporary IDs

```typescript
// ✅ Good - replaces temp ID with real server ID
createOptimisticData: (variables) => ({
    id: `temp-${Date.now()}`,
    ...variables
}),
onSuccessCallback: (serverData, variables) => {
    // Replace temporary item with real server response
    replaceInCache(`temp-${variables.timestamp}`, serverData);
},
```

### 4. Update All Relevant Caches

```typescript
// ✅ Good - updates all affected cache keys
const cacheKeys = [
    ['entities'],
    ['entities', entityId],
    ['parent', parentId, 'entities'],
];

// ❌ Bad - only updates one cache, others become stale
const cacheKeys = [['entities']];
```

### 5. Distinguish Optimistic vs Server Updates

```typescript
// ✅ Good - separate handling for optimistic and server data
updateCache: (optimisticData) => {
    // Fast update for immediate feedback
    // May have temp IDs, optimistic guesses
    updateCacheImmediately(optimisticData);
},
updateCacheWithServerResponse: (serverData) => {
    // Authoritative update with computed fields
    // Real IDs, server timestamps, validated data
    replaceWithServerData(serverData);
},

// ❌ Bad - same function for both, loses server-computed fields
updateCache: (data) => {
    // Can't distinguish between optimistic and server data
    // Server-computed fields may be lost
    updateCache(data);
},
```

### 6. Handle Temporary IDs Properly

```typescript
// ✅ Good - properly replaces temp IDs with server IDs
createOptimisticData: () => ({ id: `temp-${Date.now()}`, ...data }),
updateCacheWithServerResponse: (serverItem) => {
    replaceItemWithTempId(serverItem); // Finds and replaces temp item
},

// ❌ Bad - temp items remain in cache with fake IDs
// Server response gets added as separate item, creating duplicates
```

## Testing Optimistic Updates

### Test Structure

```typescript
it('should apply optimistic updates immediately', async () => {
    // Setup: Mock API with delay
    mockApi.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve(serverResponse), 100))
    );
    
    // Act: Trigger optimistic update
    act(() => {
        result.current.mutate(updateData);
    });
    
    // Assert: Verify immediate update (before API completes)
    expect(result.current.data).toEqual(expectedOptimisticState);
    
    // Wait for API and verify final state
    await waitFor(() => expect(mockApi).toHaveBeenCalled());
    expect(result.current.data).toEqual(expectedFinalState);
});
```

### Test Rollback Behavior

```typescript
it('should rollback on API error', async () => {
    mockApi.mockRejectedValue(new Error('API Error'));
    
    const initialState = result.current.data;
    
    await act(async () => {
        try {
            await result.current.mutate(updateData);
        } catch (error) {
            // Expected to fail
        }
    });
    
    // Verify state was rolled back
    expect(result.current.data).toEqual(initialState);
});
```

### Test Server Response Handling

```typescript
it('should preserve server-computed fields', async () => {
    const serverResponse = {
        id: 'real-uuid',
        title: 'User Input',
        created_at: '2025-01-15T10:00:00Z', // Server timestamp
        updated_at: '2025-01-15T10:00:00Z', // Server timestamp
        order: 5, // Server computed
        validation_hash: 'abc123' // Server computed
    };
    
    mockApi.mockResolvedValue(serverResponse);
    
    await act(async () => {
        await result.current.mutate({ title: 'User Input' });
    });
    
    // Verify ALL server fields are preserved
    expect(result.current.data).toMatchObject(serverResponse);
    
    // Verify computed fields specifically
    expect(result.current.data.created_at).toBe('2025-01-15T10:00:00Z');
    expect(result.current.data.order).toBe(5);
    expect(result.current.data.validation_hash).toBe('abc123');
});
```

### Test Temporary ID Replacement

```typescript
it('should replace temporary IDs with server IDs', async () => {
    const serverResponse = { id: 'real-uuid', title: 'New Item' };
    mockApi.mockResolvedValue(serverResponse);
    
    // Start optimistic creation
    const mutationPromise = act(async () => {
        return result.current.mutateAsync({ title: 'New Item' });
    });
    
    // Verify temp ID exists immediately
    expect(result.current.data[0].id).toMatch(/^temp-/);
    
    // Wait for server response
    await mutationPromise;
    
    // Verify temp ID was replaced with real ID
    expect(result.current.data[0].id).toBe('real-uuid');
    expect(result.current.data).toHaveLength(1); // No duplicates
});
```

### Test API Call Parameters

```typescript
it('should call API with exact parameters', async () => {
    const variables = { id: '123', title: 'Updated' };
    
    await act(async () => {
        await result.current.mutateAsync(variables);
    });
    
    // Verify API was called with exact variables
    expect(mockMutationFn).toHaveBeenCalledTimes(1);
    expect(mockMutationFn).toHaveBeenCalledWith(variables);
});
```

## Performance Benefits

- **Perceived Performance**: UI updates appear 200-500ms faster
- **Reduced Loading States**: Less need for loading spinners on mutations  
- **Better UX**: Users can continue working while API calls complete
- **Error Recovery**: Automatic rollback maintains data consistency

## Migration Checklist

When adding optimistic updates to existing hooks:

- [ ] Import `useOptimisticMutation` 
- [ ] Replace `useMutation` with optimistic version
- [ ] Implement `createOptimisticData` function
- [ ] Define `queryKeysToCancel` to prevent races
- [ ] Add `captureContext` for rollback data
- [ ] Implement `rollbackCache` function
- [ ] Update cache consistently across all query keys
- [ ] Add tests for optimistic behavior and rollback
- [ ] Verify no breaking changes to existing API

## Common Pitfalls

1. **Forgetting Rollback**: Leads to inconsistent state on errors
2. **Race Conditions**: Not canceling queries causes overwrites
3. **Partial Cache Updates**: Some query keys get stale data
4. **Missing Context**: Can't rollback without previous state
5. **Complex State**: Hard to create accurate optimistic data

By following these patterns, you can implement consistent, reliable optimistic updates across all hooks in the application.