import React, { act } from 'react';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import { useInitiativeGroups, InitiativeGroupsProvider } from '#hooks/useInitiativeGroups.js';
import { GroupDto, GroupType, InitiativeDto, WorkspaceDto } from '#types';


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

vi.mock('#api/groups', () => ({
    getGroups: vi.fn(),
    getGroupById: vi.fn(),
    postGroup: vi.fn(),
    deleteGroup: vi.fn(),
}));

vi.mock('#api/initiatives', () => ({
    postInitiative: vi.fn(),
    addInitiativeToGroup: vi.fn(),
    removeInitiativeFromGroup: vi.fn(),
    initiativeFromData: vi.fn(),
}));

// Import the mock functions for setup
import { getGroups, getGroupById, postGroup, deleteGroup } from '#api/groups';
import { postInitiative, addInitiativeToGroup, removeInitiativeFromGroup } from '#api/initiatives';

const createTestQueryClient = () => new QueryClient({
    defaultOptions: {
        queries: {
            retry: false,
        },
    },
});

describe('useInitiativeGroups integration tests', () => {
    let testInitiative: InitiativeDto;
    let queryClient: QueryClient; // Declare queryClient in the describe scope
    let mockGroups: GroupDto[] = [];
    let mockGroupIdCounter = 1;
    let mockInitiativeIdCounter = 1;

    const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
        // queryClient is now sourced from the beforeEach hook in the describe block
        return (
            <QueryClientProvider client={queryClient}>
                <InitiativeGroupsProvider>
                    {children}
                </InitiativeGroupsProvider>
            </QueryClientProvider>
        );
    };

    const createMockInitiative = (overrides: Partial<InitiativeDto> = {}): InitiativeDto => ({
        id: `initiative-${mockInitiativeIdCounter++}`,
        identifier: `TEST-${mockInitiativeIdCounter}`,
        user_id: 'user-1',
        title: 'Test Initiative',
        description: 'Test description',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        status: 'TO_DO',
        type: null,
        tasks: [],
        has_pending_job: false,
        ...overrides,
    });

    const createMockGroup = (overrides: Partial<GroupDto> = {}): GroupDto => ({
        id: `group-${mockGroupIdCounter++}`,
        user_id: 'user-1',
        workspace_id: '5f8a85c0-5974-4444-9875-ae5c56014fee',
        name: 'Test Group',
        description: 'Test description',
        group_type: GroupType.EXPLICIT,
        group_metadata: null,
        query_criteria: null,
        parent_group_id: null,
        initiatives: [],
        ...overrides,
    });

    beforeAll(async () => {
        testInitiative = createMockInitiative({
            title: 'Integration Test Initiative',
            description: 'Created for useInitiativeGroups integration test',
            status: 'TO_DO',
        });
    });

    beforeEach(() => { // Initialize queryClient before each test
        queryClient = createTestQueryClient();
        mockGroups = [];
        mockGroupIdCounter = 1;
        mockInitiativeIdCounter = 1;

        // Setup mock implementations
        (getGroups as any).mockImplementation(() => Promise.resolve([...mockGroups]));
        
        (getGroupById as any).mockImplementation((id: string) => {
            const group = mockGroups.find(g => g.id === id);
            if (!group) {
                throw new Error('Group not found');
            }
            return Promise.resolve(group);
        });
        
        (postGroup as any).mockImplementation((groupData: Partial<GroupDto>) => {
            const newGroup = createMockGroup(groupData);
            if (groupData.id) {
                // Update existing
                const index = mockGroups.findIndex(g => g.id === groupData.id);
                if (index >= 0) {
                    mockGroups[index] = { ...mockGroups[index], ...newGroup };
                    return Promise.resolve(mockGroups[index]);
                }
            }
            // Create new
            mockGroups.push(newGroup);
            return Promise.resolve(newGroup);
        });
        
        (deleteGroup as any).mockImplementation((id: string) => {
            mockGroups = mockGroups.filter(g => g.id !== id);
            return Promise.resolve();
        });
        
        (postInitiative as any).mockImplementation((data: any) => {
            return Promise.resolve(createMockInitiative(data));
        });
        
        (addInitiativeToGroup as any).mockImplementation((initiativeId: string, groupId: string) => {
            const group = mockGroups.find(g => g.id === groupId);
            if (group && !group.initiatives?.some(i => i.id === initiativeId)) {
                group.initiatives = group.initiatives || [];
                group.initiatives.push(testInitiative);
            }
            return Promise.resolve();
        });
        
        (removeInitiativeFromGroup as any).mockImplementation((initiativeId: string, groupId: string) => {
            const group = mockGroups.find(g => g.id === groupId);
            if (group && group.initiatives) {
                group.initiatives = group.initiatives.filter(i => i.id !== initiativeId);
            }
            return Promise.resolve();
        });
    });

    afterEach(() => {
        // Clean up mocks
        vi.clearAllMocks();
    });

    it('should create and read a new explicit group', async () => {
        const { result } = renderHook(() => useInitiativeGroups(), { wrapper: TestWrapper });

        await waitFor(() => expect(result.current.loading).toBe(false));

        const groupDetails = {
            name: 'Test Group',
            description: 'A group created for integration testing',
        };

        let createdGroup: GroupDto | undefined;
        await act(async () => {
            createdGroup = await result.current.createNewExplicitGroup(groupDetails);
        });

        // With optimistic updates, the group should be available in cache after mutation
        await waitFor(() => {
            expect(result.current.allGroupsInWorkspace.some(g => g.name === groupDetails.name)).toBe(true);
        });

        expect(createdGroup).toBeDefined();
        expect(createdGroup?.name).toBe(groupDetails.name);
        expect(createdGroup?.group_type).toBe(GroupType.EXPLICIT);

        // Add the initiative to the group
        let groupWithInitiative: GroupDto | undefined;
        await act(async () => {
            if (createdGroup && testInitiative) {
                groupWithInitiative = await result.current.addInitiativeToExplicitGroup(testInitiative, createdGroup);
            } else {
                throw new Error('Group or initiative not found');
            }
        });

        expect(groupWithInitiative).toBeDefined();
        // The GroupDto returned by addInitiativeToExplicitGroup should have the initiatives populated.
        // We need to ensure GroupDto can have an 'initiatives' field.
        // Assuming GroupDto from apiGetGroupById (called by the hook) includes initiatives.
        expect(groupWithInitiative?.initiatives).toBeDefined();
        expect(groupWithInitiative?.initiatives?.some(i => i.id === testInitiative.id)).toBe(true);
        expect(groupWithInitiative?.initiatives?.find(i => i.id === testInitiative.id)?.title).toBe(testInitiative.title);

    });

    it('should remove an initiative from an explicit group', async () => {
        const initiativeToRemove = await postInitiative({
            title: 'Initiative To Remove',
            description: 'This initiative will be removed from a group.',
            status: 'TO_DO',
        });

        const { result: scopedResult, rerender: scopedRerender } = renderHook(
            () => useInitiativeGroups(),
            {
                wrapper: TestWrapper,
                initialProps: { },
            }
        );
        await waitFor(() => expect(scopedResult.current.loading).toBe(false));

        // General hook for performing actions and general assertions
        const { result: generalResult } = renderHook(() => useInitiativeGroups(), { wrapper: TestWrapper });
        await waitFor(() => {
            if (!generalResult.current) {
                throw new Error("generalResult.current is null during initial setup.");
            }
            expect(generalResult.current.loading).toBe(false);
        });

        const groupDetails = {
            name: 'Group For Removal Test',
            description: 'A group to test removing initiatives',
        };

        let createdGroup: GroupDto | undefined;
        // Create group using the general hook
        await act(async () => {
            createdGroup = await generalResult.current.createNewExplicitGroup(groupDetails);
        });

        expect(createdGroup).toBeDefined();
        if (!createdGroup) throw new Error("Group creation failed");

        // Add the initiative to the group using the general hook
        let groupWithInitiative: GroupDto | undefined;
        await act(async () => {
            groupWithInitiative = await generalResult.current.addInitiativeToExplicitGroup(initiativeToRemove!, createdGroup!);
        });

        expect(groupWithInitiative).toBeDefined();
        expect(groupWithInitiative?.initiatives?.some(i => i.id === initiativeToRemove.id)).toBe(true);

        // Remove the initiative from the group using the general hook
        let groupAfterRemoval: GroupDto | undefined;
        await act(async () => {
            groupAfterRemoval = await generalResult.current.removeInitiativeFromExplicitGroup(initiativeToRemove!, createdGroup!);
        });

        expect(groupAfterRemoval).toBeDefined();
        expect(groupAfterRemoval?.initiatives?.some(i => i.id === initiativeToRemove.id)).toBe(false);

        // Check allGroupsInWorkspace from the same general hook instance
        // Mutations should update cache optimistically, and generalResult should update immediately.
        // Add a waitFor to ensure the state has propagated.
        await waitFor(() => {
            const finalGroupState = generalResult.current.allGroupsInWorkspace.find(g => g.id === createdGroup?.id);
            expect(finalGroupState?.initiatives?.some(i => i.id === initiativeToRemove.id)).toBe(false);
        });
    });

    it('should update an existing group', async () => {
        const { result } = renderHook(() => useInitiativeGroups(), { wrapper: TestWrapper });

        await waitFor(() => expect(result.current.loading).toBe(false));

        // First create a group
        const groupDetails = {
            name: 'Original Group Name',
            description: 'Original description',
        };

        let createdGroup: GroupDto | undefined;
        await act(async () => {
            createdGroup = await result.current.createNewExplicitGroup(groupDetails);
        });

        expect(createdGroup).toBeDefined();
        if (!createdGroup) throw new Error('Group creation failed');

        // Update the group
        const updatedGroupData: GroupDto = {
            ...createdGroup,
            name: 'Updated Group Name',
            description: 'Updated description',
        };

        let updatedGroup: GroupDto | undefined;
        await act(async () => {
            updatedGroup = await result.current.updateGroup(updatedGroupData);
        });

        expect(updatedGroup).toBeDefined();
        expect(updatedGroup?.name).toBe('Updated Group Name');
        expect(updatedGroup?.description).toBe('Updated description');
        expect(updatedGroup?.id).toBe(createdGroup.id);

        // Verify cache updates
        await waitFor(() => {
            const groupInCache = result.current.allGroupsInWorkspace.find(g => g.id === createdGroup?.id);
            expect(groupInCache?.name).toBe('Updated Group Name');
            expect(groupInCache?.description).toBe('Updated description');
        });
    });

    it('should delete a group', async () => {
        const { result } = renderHook(() => useInitiativeGroups(), { wrapper: TestWrapper });

        await waitFor(() => expect(result.current.loading).toBe(false));

        // First create a group
        const groupDetails = {
            name: 'Group To Delete',
            description: 'This group will be deleted',
        };

        let createdGroup: GroupDto | undefined;
        await act(async () => {
            createdGroup = await result.current.createNewExplicitGroup(groupDetails);
        });

        expect(createdGroup).toBeDefined();
        if (!createdGroup) throw new Error('Group creation failed');

        // Verify group exists in cache
        await waitFor(() => {
            expect(result.current.allGroupsInWorkspace.some(g => g.id === createdGroup?.id)).toBe(true);
        });

        // Delete the group
        await act(async () => {
            await result.current.deleteGroup(createdGroup!);
        });

        // Verify group is removed from cache
        await waitFor(() => {
            expect(result.current.allGroupsInWorkspace.some(g => g.id === createdGroup?.id)).toBe(false);
        });
    });

    it('should create a smart group', async () => {
        const { result } = renderHook(() => useInitiativeGroups(), { wrapper: TestWrapper });

        await waitFor(() => expect(result.current.loading).toBe(false));

        const smartGroupData: GroupDto = createMockGroup({
            name: 'Smart Group Test',
            description: 'A smart group for testing',
            group_type: GroupType.SMART,
            query_criteria: {
                status: 'TO_DO',
                _keywords: 'important',
            },
        });

        let createdSmartGroup: GroupDto | undefined;
        await act(async () => {
            createdSmartGroup = await result.current.createNewSmartGroup(smartGroupData);
        });

        expect(createdSmartGroup).toBeDefined();
        expect(createdSmartGroup?.name).toBe('Smart Group Test');
        expect(createdSmartGroup?.group_type).toBe(GroupType.SMART);
        expect(createdSmartGroup?.query_criteria).toEqual({
            status: 'TO_DO',
            _keywords: 'important',
        });

        // Verify smart group appears in cache
        await waitFor(() => {
            const groupInCache = result.current.allGroupsInWorkspace.find(g => g.id === createdSmartGroup?.id);
            expect(groupInCache).toBeDefined();
            expect(groupInCache?.group_type).toBe(GroupType.SMART);
        });
    });

    it('should update a smart group', async () => {
        const { result } = renderHook(() => useInitiativeGroups(), { wrapper: TestWrapper });

        await waitFor(() => expect(result.current.loading).toBe(false));

        // First create a smart group
        const smartGroupData: GroupDto = createMockGroup({
            name: 'Original Smart Group',
            description: 'Original smart group description',
            group_type: GroupType.SMART,
            query_criteria: {
                status: 'TO_DO',
            },
        });

        let createdSmartGroup: GroupDto | undefined;
        await act(async () => {
            createdSmartGroup = await result.current.createNewSmartGroup(smartGroupData);
        });

        expect(createdSmartGroup).toBeDefined();
        if (!createdSmartGroup) throw new Error('Smart group creation failed');

        // Update the smart group
        const updatedSmartGroupData: GroupDto = {
            ...createdSmartGroup,
            name: 'Updated Smart Group',
            description: 'Updated smart group description',
            query_criteria: {
                status: 'IN_PROGRESS',
                _keywords: 'urgent',
            },
        };

        let updatedSmartGroup: GroupDto | undefined;
        await act(async () => {
            updatedSmartGroup = await result.current.updateSmartGroup(updatedSmartGroupData);
        });

        expect(updatedSmartGroup).toBeDefined();
        expect(updatedSmartGroup?.name).toBe('Updated Smart Group');
        expect(updatedSmartGroup?.description).toBe('Updated smart group description');
        expect(updatedSmartGroup?.group_type).toBe(GroupType.SMART);
        expect(updatedSmartGroup?.query_criteria).toEqual({
            status: 'IN_PROGRESS',
            _keywords: 'urgent',
        });

        // Verify cache updates
        await waitFor(() => {
            const groupInCache = result.current.allGroupsInWorkspace.find(g => g.id === createdSmartGroup?.id);
            expect(groupInCache?.name).toBe('Updated Smart Group');
            expect(groupInCache?.query_criteria).toEqual({
                status: 'IN_PROGRESS',
                _keywords: 'urgent',
            });
        });
    });

    it('should find groups by IDs using findGroupsByIds', async () => {
        const { result } = renderHook(() => useInitiativeGroups(), { wrapper: TestWrapper });

        await waitFor(() => expect(result.current.loading).toBe(false));

        // Create multiple groups
        const group1Details = { name: 'Group 1', description: 'First group' };
        const group2Details = { name: 'Group 2', description: 'Second group' };

        let group1: GroupDto | undefined;
        let group2: GroupDto | undefined;

        await act(async () => {
            group1 = await result.current.createNewExplicitGroup(group1Details);
            group2 = await result.current.createNewExplicitGroup(group2Details);
        });

        expect(group1).toBeDefined();
        expect(group2).toBeDefined();
        if (!group1 || !group2) throw new Error('Group creation failed');

        // Wait for both groups to appear in cache
        await waitFor(() => {
            expect(result.current.allGroupsInWorkspace.some(g => g.id === group1?.id)).toBe(true);
            expect(result.current.allGroupsInWorkspace.some(g => g.id === group2?.id)).toBe(true);
        });

        // Test finding groups by IDs
        const foundGroups = result.current.findGroupsByIds([group1.id, group2.id]);
        expect(foundGroups).toHaveLength(2);
        expect(foundGroups.some(g => g.id === group1?.id)).toBe(true);
        expect(foundGroups.some(g => g.id === group2?.id)).toBe(true);

        // Test with non-existent ID
        const mixedResults = result.current.findGroupsByIds([group1.id, 'non-existent-id']);
        expect(mixedResults).toHaveLength(1);
        expect(mixedResults[0].id).toBe(group1.id);

        // Test with empty array
        const emptyResults = result.current.findGroupsByIds([]);
        expect(emptyResults).toHaveLength(0);

        // Test with only non-existent IDs
        const noResults = result.current.findGroupsByIds(['non-existent-1', 'non-existent-2']);
        expect(noResults).toHaveLength(0);
    });
});
