import React from 'react';
import { InitiativeDto, GroupDto, InitiativeStatus, GroupType } from '#types';
import InitiativesListView from './InitiativesListView';
import { useNavigate } from 'react-router';
import ExplicitGroup from './groups/ExplicitGroup';
import SmartGroup from './groups/SmartGroup';

interface GroupInitiativesDisplayProps {
    group: GroupDto;
    allInitiatives: InitiativeDto[];
    selectedStatuses: InitiativeStatus[];
}

const GroupInitiativesDisplay: React.FC<GroupInitiativesDisplayProps> = ({
    group,
    allInitiatives,
    selectedStatuses,
}) => {
    const navigate = useNavigate();

    // Navigate to initiative detail when clicked
    const handleCardClick = (initiativeId: string) => {
        const initiative = allInitiatives?.find(i => i.id === initiativeId);
        if (!initiative) return;

        navigate(`/workspace/initiatives/${initiativeId}`);
    };
    
    return (
        <div key={group.id} className="p-0.5 bg-gradient-to-br from-border/15 via-border/15 to-transparent rounded-lg shadow-sm hover:shadow-md transition-shadow duration-300">
            {group.group_type === GroupType.EXPLICIT ? (
                <ExplicitGroup
                    group={group}
                    onInitiativeClick={(initiative: InitiativeDto) => handleCardClick(initiative.id)}
                    selectedStatuses={selectedStatuses}
                />
            ) : (
                <SmartGroup
                    group={group}
                    onInitiativeClick={(initiative: InitiativeDto) => handleCardClick(initiative.id)}
                    selectedStatuses={selectedStatuses}
                />
            )}
        </div>
    );
};

export default GroupInitiativesDisplay;