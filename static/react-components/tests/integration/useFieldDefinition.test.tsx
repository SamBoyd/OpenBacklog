import React, { act } from 'react';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from "vitest";
import { getPostgrestClient } from "./utils";
import { useFieldDefinitions } from '#hooks/useFieldDefinitions';
import { CreateFieldDefinitionDto, EntityType, FieldType, WorkspaceDto } from '#types';
import { execSync } from 'child_process';

vi.mock('#api/api-utils', () => {
    return {
        loadAndValidateJWT: vi.fn(),
        getPostgrestClient: vi.fn().mockImplementation(() => getPostgrestClient()),
        withApiCall: vi.fn().mockImplementation((fn) => fn()),
    }
})

vi.mock('#services/workspaceApi', () => {
    const mockWorkspace: WorkspaceDto = {
        id: '5f8a85c0-5974-4444-9875-ae5c56014fee',
        name: 'Test Workspace',
        description: 'This is a test workspace',
        icon: 'https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png',
    }
    
    return {
        fetchWorkspaces: vi.fn().mockResolvedValue([mockWorkspace]),
        createWorkspace: vi.fn().mockResolvedValue(mockWorkspace),
        setCurrentWorkspace: vi.fn(),
        getCurrentWorkspaceFromCookie: vi.fn().mockReturnValue(mockWorkspace),
        fetchCurrentWorkspace: vi.fn().mockResolvedValue(mockWorkspace),
    }
});

const createTestQueryClient = () => new QueryClient({
    defaultOptions: {
        queries: {
            retry: false, // Prevent retries during tests
        },
    },
});

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const queryClient = createTestQueryClient();
    return <QueryClientProvider client={queryClient}> {children} </QueryClientProvider>;
};

describe.skip('useFieldDefinition integration tests', () => {
    afterAll(async () => {
        // Run cleanup script
        execSync('bash tests/cleanup_db.sh');
    });

    it('should fetch and create field definitions', async () => {
        const { result } = renderHook(() => useFieldDefinitions({}), { wrapper: TestWrapper });

        await waitFor(() => expect(result.current.loading).toBe(false));

        expect(result.current.fieldDefinitions).toEqual([]);


        const testFieldDefinition: CreateFieldDefinitionDto = {
            name: 'test field definition',
            field_type: FieldType.TEXT,
            config: {},
            entity_type: EntityType.INITIATIVE,
            key: 'test_field_definition'
        }

        // Create the field definition and wait for it to be created
        await act(async () => {
            await result.current.createFieldDefinition(testFieldDefinition);
        });

        // Wait for the field definitions to be updated in the query cache
        await waitFor(() => {
            expect(result.current.fieldDefinitions.length).toBeGreaterThan(0);
        }, { timeout: 2000 });  

        // Now check that the created field definition is in the array
        expect(result.current.fieldDefinitions).toContainEqual(expect.objectContaining({
            name: testFieldDefinition.name,
            field_type: testFieldDefinition.field_type,
            entity_type: testFieldDefinition.entity_type,
            key: testFieldDefinition.key,
        }));
    });
});
