import React, { useCallback, useState } from 'react';
import { MdLightbulb } from 'react-icons/md';
import { Skeleton } from './reusable/Skeleton';
import ResizingTextInput from './reusable/ResizingTextInput';
import { useStrategicInitiative } from '#hooks/useStrategicInitiative';
import { useStrategicPillars } from '#hooks/useStrategicPillars';
import { useRoadmapThemes } from '#hooks/useRoadmapThemes';
import { useWorkspaces } from '#hooks/useWorkspaces';

type StrategicContextDisplayProps = {
    initiativeId: string;
    loading?: boolean;
    testId?: string;
};

const StrategicContextDisplay: React.FC<StrategicContextDisplayProps> = ({
    initiativeId,
    loading = false,
    testId = 'strategic-context-section',
}) => {
    const {
        strategicInitiative,
        isLoading: isLoadingStrategicInit,
        updateStrategicInitiative,
        createStrategicInitiative,
    } = useStrategicInitiative(initiativeId);
    const { currentWorkspace } = useWorkspaces();
    const workspaceId = currentWorkspace?.id || '';
    const { pillars, isLoading: isLoadingPillars } = useStrategicPillars(workspaceId);
    const { themes, isLoading: isLoadingThemes } = useRoadmapThemes(workspaceId);

    const [localTextFields, setLocalTextFields] = useState<Record<string, string>>({});

    const isLoadingData = loading || isLoadingStrategicInit || isLoadingPillars || isLoadingThemes;

    const linkedPillar = strategicInitiative?.pillar_id
        ? pillars.find(p => p.id === strategicInitiative.pillar_id)
        : null;

    const linkedTheme = strategicInitiative?.theme_id
        ? themes.find(t => t.id === strategicInitiative.theme_id)
        : null;

    const saveField = useCallback((field: string, value: string | null) => {
        // When updating any field, preserve all other fields
        // because the backend update method sets ALL fields
        const updateData = {
            pillar_id: strategicInitiative?.pillar_id || null,
            theme_id: strategicInitiative?.theme_id || null,
            user_need: strategicInitiative?.user_need || null,
            connection_to_vision: strategicInitiative?.connection_to_vision || null,
            success_criteria: strategicInitiative?.success_criteria || null,
            out_of_scope: strategicInitiative?.out_of_scope || null,
            [field]: value || null,
        };

        if (strategicInitiative) {
            updateStrategicInitiative(updateData);
        } else {
            createStrategicInitiative(updateData);
        }
    }, [strategicInitiative, updateStrategicInitiative, createStrategicInitiative]);

    const handleTextFieldChange = (field: string, value: string) => {
        setLocalTextFields(prev => ({
            ...prev,
            [field]: value
        }));
    };

    const handleTextFieldBlur = (field: string) => {
        const localValue = localTextFields[field];
        if (localValue !== undefined) {
            const currentValue = strategicInitiative?.[field as keyof typeof strategicInitiative];
            if (currentValue !== (localValue || null)) {
                saveField(field, localValue);
            }
            setLocalTextFields(prev => {
                const newState = { ...prev };
                delete newState[field];
                return newState;
            });
        }
    };

    const handleSelectChange = (field: string, value: string) => {
        // When updating a select field, we need to preserve other fields
        // because the backend update method sets ALL fields
        const updateData = {
            pillar_id: strategicInitiative?.pillar_id || null,
            theme_id: strategicInitiative?.theme_id || null,
            user_need: strategicInitiative?.user_need || null,
            connection_to_vision: strategicInitiative?.connection_to_vision || null,
            success_criteria: strategicInitiative?.success_criteria || null,
            out_of_scope: strategicInitiative?.out_of_scope || null,
            [field]: value || null,
        };

        if (strategicInitiative) {
            updateStrategicInitiative(updateData);
        } else {
            createStrategicInitiative(updateData);
        }
    };

    const getTextFieldValue = (field: string): string => {
        if (localTextFields[field] !== undefined) {
            return localTextFields[field];
        }
        const value = strategicInitiative?.[field as keyof typeof strategicInitiative];
        return (typeof value === 'string' ? value : '') || '';
    };

    return (
        <div
            className="mb-6 pb-4 border-b border-border text-foreground"
            data-testid={testId}
        >
            <div className="flex flex-row gap-2 items-baseline font-light mb-3">
                <MdLightbulb className="text-lg" />
                <span className="ml-2.5">Strategic Context</span>
            </div>

            {isLoadingData ? (
                <div className="space-y-3">
                    <Skeleton type="text" className="h-6 w-48" />
                    <Skeleton type="text" className="h-20 w-full" />
                    <Skeleton type="text" className="h-20 w-full" />
                </div>
            ) : (
                <div className="space-y-4 ml-9">
                    <div>
                        <div className="text-sm font-medium text-muted-foreground mb-1">
                            Strategic Pillar
                        </div>
                        <select
                            value={strategicInitiative?.pillar_id || ''}
                            onChange={(e) => handleSelectChange('pillar_id', e.target.value)}
                            className="w-full rounded py-2 px-3 border border-primary/20 text-foreground focus:outline-none focus:ring-1 focus:ring-primary/50 focus:border-transparent bg-muted/5"
                            data-testid="strategic-context-pillar-select"
                        >
                            <option value="">None</option>
                            {pillars.map(pillar => (
                                <option key={pillar.id} value={pillar.id}>
                                    {pillar.name}
                                </option>
                            ))}
                        </select>
                        {linkedPillar?.description && (
                            <div className="text-sm text-muted-foreground mt-1">
                                {linkedPillar.description}
                            </div>
                        )}
                    </div>

                    <div>
                        <div className="text-sm font-medium text-muted-foreground mb-1">
                            Roadmap Theme
                        </div>
                        <select
                            value={strategicInitiative?.theme_id || ''}
                            onChange={(e) => handleSelectChange('theme_id', e.target.value)}
                            className="w-full rounded py-2 px-3 border border-primary/20 text-foreground focus:outline-none focus:ring-1 focus:ring-primary/50 focus:border-transparent bg-muted/5"
                            data-testid="strategic-context-theme-select"
                        >
                            <option value="">None</option>
                            {themes.map(theme => (
                                <option key={theme.id} value={theme.id}>
                                    {theme.name}
                                </option>
                            ))}
                        </select>
                        {linkedTheme?.problem_statement && (
                            <div className="text-sm text-muted-foreground mt-1">
                                {linkedTheme.problem_statement}
                            </div>
                        )}
                    </div>

                    <div>
                        <div className="text-sm font-medium text-muted-foreground mb-1">
                            User Need
                        </div>
                        <ResizingTextInput
                            value={getTextFieldValue('user_need')}
                            onChange={(value) => handleTextFieldChange('user_need', value)}
                            onBlur={() => handleTextFieldBlur('user_need')}
                            placeholder="Describe the user need this initiative addresses..."
                            testId="strategic-context-user-need"
                            className="text-base"
                            initialRows={3}
                        />
                    </div>

                    <div>
                        <div className="text-sm font-medium text-muted-foreground mb-1">
                            Connection to Vision
                        </div>
                        <ResizingTextInput
                            value={getTextFieldValue('connection_to_vision')}
                            onChange={(value) => handleTextFieldChange('connection_to_vision', value)}
                            onBlur={() => handleTextFieldBlur('connection_to_vision')}
                            placeholder="How does this initiative connect to the product vision..."
                            testId="strategic-context-connection-to-vision"
                            className="text-base"
                            initialRows={3}
                        />
                    </div>

                    <div>
                        <div className="text-sm font-medium text-muted-foreground mb-1">
                            Success Criteria
                        </div>
                        <ResizingTextInput
                            value={getTextFieldValue('success_criteria')}
                            onChange={(value) => handleTextFieldChange('success_criteria', value)}
                            onBlur={() => handleTextFieldBlur('success_criteria')}
                            placeholder="What does success look like for this initiative..."
                            testId="strategic-context-success-criteria"
                            className="text-base"
                            initialRows={3}
                        />
                    </div>

                    <div>
                        <div className="text-sm font-medium text-muted-foreground mb-1">
                            Out of Scope
                        </div>
                        <ResizingTextInput
                            value={getTextFieldValue('out_of_scope')}
                            onChange={(value) => handleTextFieldChange('out_of_scope', value)}
                            onBlur={() => handleTextFieldBlur('out_of_scope')}
                            placeholder="What is explicitly out of scope for this initiative..."
                            testId="strategic-context-out-of-scope"
                            className="text-base"
                            initialRows={3}
                        />
                    </div>
                </div>
            )}
        </div>
    );
};

export default StrategicContextDisplay;

