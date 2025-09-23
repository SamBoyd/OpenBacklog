// components/reusable/InitiativeFilter.tsx
import React from 'react';
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/react'
import { ChevronDownIcon } from '@heroicons/react/20/solid'
import { useInitiativesContext } from '#contexts/InitiativesContext';
import { InitiativeDto } from '#types';

interface InitiativeFilterProps {
    onSelect: (initiativeId?: string) => void;
};

const InitiativeFilter = ({ onSelect }: InitiativeFilterProps) => {
    const { initiativesData, shouldShowSkeleton, error } = useInitiativesContext();
    const [selectedInitiativeTitle, setSelectedInitiativeTitle] = React.useState<string | undefined>(undefined);

    const handleSelect = (selected?: InitiativeDto) => {
        setSelectedInitiativeTitle(selected ? selected.title : undefined);
        onSelect(selected ? selected.id : undefined);
    };

    return (
        <Menu as="div" className="relative inline-block text-left w-full">
            <MenuButton className='w-full'>
                <div
                    className="flex w-full items-center p-2 gap-1 cursor-pointer border rounded-md"

                >
                    <span>Initiative</span>
                    <span>-</span>
                    <div className="flex-grow flex justify-start">
                        {shouldShowSkeleton ? (
                            <span>Loading...</span>
                        ) : error ? (
                            <span>Error</span>
                        ) : null}
                        {selectedInitiativeTitle ? (
                            <span>{selectedInitiativeTitle}</span>
                        ) : (
                            <span>Filter by initiative</span>
                        )}
                    </div>
                    <div>
                        <ChevronDownIcon
                            aria-hidden="true"
                            className="-mr-1 size-5"
                        />
                    </div>
                </div>
            </MenuButton>

            <MenuItems
                transition
                className="absolute right-0 z-10 mt-2 w-full origin-top-right rounded-md shadow-lg ring-1 focus:outline-none data-[closed]:scale-95 data-[closed]:transform data-[closed]:opacity-0 data-[enter]:duration-100 data-[leave]:duration-75 data-[enter]:ease-out data-[leave]:ease-in"
            >
                <div className="py-1">
                    {initiativesData?.map(initiative => (
                        <MenuItem key={initiative.id}>
                            <a
                                onClick={() => handleSelect(initiative)}
                                className="block px-4 py-2 text-sm cursor-pointer"
                            >
                                {initiative.title}
                            </a>
                        </MenuItem>
                    ))}

                    {/* Clear selection */}
                    {selectedInitiativeTitle && (
                        <MenuItem>
                            <a
                                onClick={() => handleSelect(undefined)}
                                className="block px-4 py-2 text-sm cursor-pointer"
                            >
                                Clear selection
                            </a>
                        </MenuItem>
                    )}
                </div>
            </MenuItems>
        </Menu>
    );
};

export default InitiativeFilter;
