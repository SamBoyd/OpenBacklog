import React, { useState, useMemo, useEffect } from 'react';
import { InitiativeDto } from '#types';
import { CheckboxInput, Input } from '#components/reusable/Input';
import { useInitiativesContext } from '#contexts/InitiativesContext';

interface SelectInitiativesToAddProps {
    selectedInitiatives: InitiativeDto[];
    onInitiativesChange: (initiatives: InitiativeDto[]) => void;
    idPrefix: string;
}

const SelectInitiativesToAdd: React.FC<SelectInitiativesToAddProps> = ({
    selectedInitiatives,
    onInitiativesChange,
    idPrefix,
}) => {
    const [searchTerm, setSearchTerm] = useState('');
    const { initiativesData } = useInitiativesContext();

    const { selectedAndFiltered, unselectedAndFiltered }: { selectedAndFiltered: InitiativeDto[], unselectedAndFiltered: InitiativeDto[] } = useMemo(() => {
        if (!initiativesData) return { selectedAndFiltered: [], unselectedAndFiltered: [] };

        const selectedInitiativesIds = selectedInitiatives.map(init => init.id);
        const lowerSearchTerm = searchTerm.toLowerCase().trim();

        const matchesSearch = (init: InitiativeDto) =>
            lowerSearchTerm === '' ||
            (init.title.toLowerCase() + ' ' + init.identifier.toLowerCase()).includes(lowerSearchTerm);

        const selectedAndFiltered = initiativesData.filter(matchesSearch).filter(init => selectedInitiativesIds.includes(init.id));
        const unselectedAndFiltered = initiativesData.filter(matchesSearch).filter(init => !selectedInitiativesIds.includes(init.id));

        return { selectedAndFiltered, unselectedAndFiltered };
    }, [initiativesData, searchTerm, selectedInitiatives]);

    const handleCheckboxAdd = (init: InitiativeDto) => {
        onInitiativesChange([...selectedInitiatives, init]);
    }

    const handleCheckboxRemove = (init: InitiativeDto) => {
        onInitiativesChange(selectedInitiatives.filter(x => x.id !== init.id));
    }

    return (
        <div className="space-y-1">
            <h3 className="text-md font-medium">Select Initiatives to Add (Optional):</h3>

            <div className="border border-border rounded p-2 bg-background">
                <Input
                    placeholder="Search initiatives by title or identifier..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                />

                <div className="p-2">
                    {selectedAndFiltered.map((init: InitiativeDto) => (
                        <div key={init.id} className="flex items-center">
                            <CheckboxInput
                                id={`init-checkbox-${idPrefix}-${init.id}`}
                                checked={true}
                                onChange={() => handleCheckboxRemove(init)}
                                className="w-fit mr-2"
                            />
                            <label htmlFor={`init-checkbox-${idPrefix}-${init.id}`} className="text-foreground text-sm/6">
                                <span className="text-muted">{init.identifier}</span> {init.title}
                            </label>
                        </div>
                    ))}
                </div>

                <div className="max-h-40 overflow-y-auto rounded p-2 bg-background">
                    {unselectedAndFiltered.map((init: InitiativeDto) => (
                        <div key={init.id} className="flex items-center">
                            <CheckboxInput
                                id={`init-checkbox-${idPrefix}-${init.id}`}
                                checked={false}
                                onChange={() => handleCheckboxAdd(init)}
                                className="w-fit mr-2"
                            />
                            <label htmlFor={`init-checkbox-${idPrefix}-${init.id}`} className="text-foreground text-sm/6">
                                <span className="text-muted">{init.identifier}</span> {init.title}
                            </label>
                        </div>
                    ))}


                    {unselectedAndFiltered.length === 0 && selectedInitiatives.length === 0 && (
                        <p className="text-muted-foreground text-sm">
                            {searchTerm ? 'No initiatives match your search.' : 'No initiatives available to add.'}
                        </p>
                    )}
                </div>
            </div>
        </div>
    );
};

export default SelectInitiativesToAdd;
