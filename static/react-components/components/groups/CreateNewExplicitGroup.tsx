import React, { useEffect, useState, useRef } from 'react';
import { GroupDto, InitiativeDto } from '#types';
import { Button } from '#components/reusable/Button';
import { useInitiativeGroups } from '#hooks/useInitiativeGroups';
import { useInitiativesContext } from '#contexts/InitiativesContext';
import { Input } from '#components/reusable/Input';
import ResizingTextInput from '#components/reusable/ResizingTextInput';
import SelectInitiativesToAdd from './SelectInitiativesToAdd';

// Mock current user for creating groups - replace with actual user data source if available
const MOCK_USER_ID = 'mock-user-id-123';

type CreateNewExplicitGroupProps = {
    onClose: () => void;
    onGroupChanged: (group: Partial<GroupDto>) => void;
};

/**
 * A dialog component for creating a new explicit group.
 * It allows users to specify a name, description, and select initiatives to include.
 */
const CreateNewExplicitGroup: React.FC<CreateNewExplicitGroupProps> = ({
    onClose,
    onGroupChanged,
}) => {
    const [groupName, setGroupName] = useState('');
    const [groupDescription, setGroupDescription] = useState('');
    const [selectedInitiatives, setSelectedInitiatives] = useState<InitiativeDto[]>([]);

    const prevGroupNameRef = useRef(groupName);
    const prevGroupDescriptionRef = useRef(groupDescription);
    const prevSelectedInitiativesRef = useRef(selectedInitiatives);

    // Check for changes in the group name, description, or selected initiatives
    useEffect(() => {
        const groupNameChanged = groupName !== prevGroupNameRef.current;
        const groupDescriptionChanged = groupDescription !== prevGroupDescriptionRef.current;

        const prevIds = prevSelectedInitiativesRef.current.map(init => init.id).sort().join(',');
        const currentIds = selectedInitiatives.map(init => init.id).sort().join(',');
        const selectedInitiativesChanged = prevIds !== currentIds;

        if (groupNameChanged || groupDescriptionChanged || selectedInitiativesChanged) {
            onGroupChanged({
                id: 'new-group',
                name: groupName,
                description: groupDescription,
                initiatives: selectedInitiatives,
            });
        }

        // Update previous values
        prevGroupNameRef.current = groupName;
        prevGroupDescriptionRef.current = groupDescription;
        prevSelectedInitiativesRef.current = selectedInitiatives;
    }, [groupName, groupDescription, selectedInitiatives, onGroupChanged]);

    return (
        <div>
            <div className="space-y-3">
                <Input
                    type="text"
                    placeholder="Explicit Group Name"
                    value={groupName}
                    onChange={(e) => setGroupName(e.target.value)}
                    className="w-full p-2 border rounded bg-input text-foreground"
                />

                <ResizingTextInput
                    placeholder="Explicit Group Description (Optional)"
                    value={groupDescription}
                    onChange={(e) => setGroupDescription(e)}
                    className="w-full p-2 border rounded bg-input text-foreground"
                />

                <SelectInitiativesToAdd
                    selectedInitiatives={selectedInitiatives}
                    onInitiativesChange={setSelectedInitiatives}
                    idPrefix="new-group"
                />
            </div>
        </div>
    );
};

export default CreateNewExplicitGroup;
