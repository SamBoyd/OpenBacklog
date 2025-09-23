import React, { useState, useMemo, useEffect } from 'react';
import { GroupDto } from '#types';
import { CheckboxInput, Input } from '#components/reusable/Input';
import { useInitiativeGroups } from '#hooks/useInitiativeGroups';

interface SelectGroupsToAddProps {
    allGroups: GroupDto[];
    selectedGroups: GroupDto[];
    onGroupsChange: (initiatives: GroupDto[]) => void;
    idPrefix: string;
}

const SelectGroupsToAdd: React.FC<SelectGroupsToAddProps> = ({
    allGroups,
    selectedGroups,
    onGroupsChange,
    idPrefix,
}) => {
    const [searchTerm, setSearchTerm] = useState('');

    const { selectedAndFiltered, unselectedAndFiltered}: { selectedAndFiltered: GroupDto[], unselectedAndFiltered: GroupDto[]} = useMemo(() => {
        if (!allGroups) return { selectedAndFiltered: [], unselectedAndFiltered: [] };

        const selectedGroupsIds = selectedGroups.map(group => group.id);
        const lowerSearchTerm = searchTerm.toLowerCase().trim();

        const matchesSearch = (group: GroupDto) =>
            lowerSearchTerm === '' ||
            (group.name.toLowerCase() + ' ' + (group.description ?? '').toLowerCase()).includes(lowerSearchTerm);

        const selectedAndFiltered = allGroups.filter(matchesSearch).filter(group => selectedGroupsIds.includes(group.id));
        const unselectedAndFiltered = allGroups.filter(matchesSearch).filter(group => !selectedGroupsIds.includes(group.id));

        return { selectedAndFiltered, unselectedAndFiltered };
    }, [allGroups, searchTerm, selectedGroups]);

    const handleCheckboxAdd = (group: GroupDto) => {
        onGroupsChange([...selectedGroups, group]);
    }

    const handleCheckboxRemove = (group: GroupDto) => {
        onGroupsChange(selectedGroups.filter(x => x.id !== group.id));
    }

    return (
        <div className="space-y-1">
            <h3 className="text-md font-medium">Select groups to add:</h3>

            <Input
                placeholder="Search groups..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full p-2 border border-border rounded bg-input text-foreground mb-2"
            />

            <div className="max-h-40 overflow-y-auto border border-border rounded p-2 bg-background">
                {selectedAndFiltered.map((group: GroupDto) => (
                    <div key={group.id} className="flex items-center">
                        <CheckboxInput
                            id={`group-checkbox-${idPrefix}-${group.id}`}
                            checked={true}
                            onChange={() => handleCheckboxRemove(group)}
                            className="w-fit mr-2"
                        />
                        <label htmlFor={`group-checkbox-${idPrefix}-${group.id}`} className="text-foreground text-sm">
                            {group.name}
                        </label>
                    </div>
                ))}

                {unselectedAndFiltered.map((group: GroupDto) => (
                    <div key={group.id} className="flex items-center">
                        <CheckboxInput
                            id={`group-checkbox-${idPrefix}-${group.id}`}
                            checked={false}
                            onChange={() => handleCheckboxAdd(group)}
                            className="w-fit mr-2"
                        />
                        <label htmlFor={`group-checkbox-${idPrefix}-${group.id}`} className="text-foreground text-sm">
                            {group.name}
                        </label>
                    </div>
                ))}


                {unselectedAndFiltered.length === 0 && selectedGroups.length === 0 && (
                    <p className="text-muted-foreground text-sm">
                        {searchTerm ? 'No groups match your search.' : 'No groups available to add.'}
                    </p>
                )}
            </div>
        </div>
    );
};

export default SelectGroupsToAdd;
