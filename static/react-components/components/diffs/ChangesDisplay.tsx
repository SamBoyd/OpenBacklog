import React, { useCallback } from 'react';
import { useNavigate } from 'react-router';

import { useInitiativesContext } from '#contexts/InitiativesContext';
import { useAiImprovementsContext } from '#contexts/AiImprovementsContext';

import {
    InitiativeLLMResponse,
    ManagedEntityAction,
    ManagedInitiativeModel,
    LENS,
} from '#types';

import { CircleDot, CircleDotDashed, CircleOff } from 'lucide-react';


const ICON_SIZE = 12;

const ListItem = ({
    managedInitiative,
    first,
    last,
}: {
    managedInitiative: ManagedInitiativeModel,
    first: boolean,
    last: boolean,
}) => {
    const navigate = useNavigate();

    const {
        initiativesData,
    } = useInitiativesContext();


    if (!managedInitiative) return null;

    const getTitleForDelete = (identifier: string) => {
        const initiative = initiativesData?.find((i) => i.identifier === identifier);
        return initiative?.title;
    }

    return (
            <div
            className={`cursor-pointer bg-primary/10 hover:bg-primary/20 rounded-sm`}
        >
            <div className="relative px-2 py-0.5">
                {managedInitiative.action === ManagedEntityAction.CREATE && (
                    <div
                        className={`relative flex items-center`}
                        onClick={() => navigate(`/workspace/initiatives/`)}
                    >
                        <div className='w-3 h-3 text-muted-foreground mr-1'><CircleDot size={ICON_SIZE} /></div>
                        <span className=" text-xs text-muted-foreground text-ellipsis truncate">
                            {managedInitiative.title}
                        </span>
                        <div className="flex-grow"></div>
                        <div className='text-xs text-muted/20'>created</div>
                    </div>
                )}

                {managedInitiative.action === ManagedEntityAction.UPDATE && (
                    <div
                        className={`relative flex items-center`}
                        onClick={() => navigate(`/workspace/initiatives/${managedInitiative.identifier}`)}
                    >
                        <div className='w-3 h-3 text-muted-foreground mr-1'><CircleDotDashed size={ICON_SIZE} /></div>
                        <span className=" text-xs text-muted-foreground text-ellipsis truncate">
                            {managedInitiative.title}
                        </span>
                        <div className="flex-grow"></div>
                        <div className='text-xs text-muted/20'>updated</div>
                    </div>
                )}

                {managedInitiative.action === ManagedEntityAction.DELETE && (
                    <div className={`relative flex items-center`}>
                        <div className='w-3 h-3 text-muted-foreground mr-1'><CircleOff size={ICON_SIZE} /></div>
                        <div className=" text-xs text-muted-foreground text-ellipsis truncate">
                            {getTitleForDelete(managedInitiative.identifier)}
                        </div>
                        <div className="flex-grow"></div>
                        <div className='text-xs text-muted/20'>deleted</div>
                    </div>
                )}
            </div>
        </div>
    )
}

const ChangesDisplay = () => {
    const {
        initiativeImprovements,
        isEntityLocked
    } = useAiImprovementsContext();

    if (Object.values(initiativeImprovements).length === 0) return null;

    return (
        <div className={`
            m-4
            overflow-hidden 
            ${isEntityLocked ? 'opacity-50' : ''}
            flex flex-col gap-1

        `}>
            <div className="px-2 py-1.5 mb-2 text-xs text-muted/20 border-b border-border/50 ">
                Suggested Changes
            </div>
            {Object.values(initiativeImprovements).map((i: ManagedInitiativeModel, index: number) =>
                <ListItem key={index} managedInitiative={i} first={index === 0} last={index === Object.values(initiativeImprovements).length - 1} />
            )}
        </div>
    );
};

export default ChangesDisplay;
