import React, { useEffect, useMemo } from 'react';
import { UnifiedSuggestion, useSuggestionsToBeResolved } from '#contexts/SuggestionsToBeResolvedContext';
import { buildBasePath } from '#hooks/diffs/basePath';
import { useInitiativesContext } from '#contexts/InitiativesContext';
import { DeleteInitiativeDiffView } from './diffs/DeleteInitiativeDiffView';
import DiffItemView from './reusable/DiffItemView';
import { InitiativeStatus, ManagedEntityAction, TaskStatus, UpdateInitiativeModel } from '#types';
import UpdateInitiativeDiffView from './UpdateInitiativeDiffView';
import { useInitiativeDiff } from '#hooks/diffs/useInitiativeDiff';

interface ViewInitiativeDiffProps {
	initiativeId: string;
}

/**
 * Container component that manages all business logic and state for ViewInitiativeDiff
 */
const ViewInitiativeDiff: React.FC<ViewInitiativeDiffProps> = ({ initiativeId }) => {
	const { initiativesData } = useInitiativesContext();
	const {
		suggestions,
		entitySuggestions,
		fieldSuggestions,
		resolutions,
		resolve,
		rollback,
		acceptAll,
		rejectAll,
		rollbackAll,
		getResolutionState,
		isFullyResolved,
		saveSuggestions,
		isSaving
	} = useSuggestionsToBeResolved();
	

	const initiative = useMemo(() => (initiativesData || []).find(i => i.id === initiativeId) || null, [initiativesData, initiativeId]);
	const basePath = buildBasePath(initiative?.identifier || '');
	const entitySuggestion: UnifiedSuggestion | undefined = Object.values(entitySuggestions).find(s => s.path === basePath);

	const taskEntitySuggestions: UnifiedSuggestion[] = useMemo(() => {
		return Object.values(entitySuggestions)
			.filter(s => s.path.startsWith(`${basePath}.tasks`))
			.filter(s => s.type === 'entity');
	}, [entitySuggestions, basePath]);

	const taskEntityResolutions = useMemo(() => {
		return taskEntitySuggestions.map(s => getResolutionState(s.path));
	}, [taskEntitySuggestions, getResolutionState]);

	useEffect(() => {
		const initiativeSuggestions = Object.values(suggestions).filter(s => s.path.startsWith(basePath));
		console.log('[ViewInitiativeDiff] initiativeSuggestions', initiativeSuggestions);
	}, [suggestions, initiative, basePath]);

	if (!initiative || !entitySuggestion) return null;

	if (entitySuggestion.action === ManagedEntityAction.DELETE) {
        return (
			<DiffItemView
				identifier={initiative?.identifier}
				status={initiative?.status ? InitiativeStatus[initiative.status as unknown as keyof typeof InitiativeStatus] : ''}
				loading={isSaving}
				hasChanged={true}
				error={null}
				createdAt={initiative?.created_at}
				updatedAt={initiative?.updated_at}
				allResolved={isFullyResolved(entitySuggestion.path)}
				onAcceptAll={() => acceptAll(entitySuggestion.path)}
				onRejectAll={() => rejectAll(entitySuggestion.path)}
				onRollbackAll={() => rollbackAll(entitySuggestion.path)}
				onSave={saveSuggestions}
				dataTestId="view-initiative-diff"
			>
                <DeleteInitiativeDiffView
                    initiativeData={initiative}
                    onAccept={() => resolve(entitySuggestion.path, true)}
                    onReject={() => resolve(entitySuggestion.path, false)}
                    onRollback={() => rollback(entitySuggestion.path)}
                    isResolved={getResolutionState(entitySuggestion.path).isResolved}
                    accepted={getResolutionState(entitySuggestion.path).isAccepted}
                />
            </DiffItemView>
        );
    }

	if (entitySuggestion.action === ManagedEntityAction.CREATE) {
		// WE have a CreateInitiativeDiffView component
		// but currently with the initiative_id based path
		// and the create initiative model not having an id
		// there is no way for the user to navigate to the
		// new initiative.

		return (
			<div>
				Can't navigate to the new initiative.
			</div>
		);
	}

	// Assume the suggestion is an ManagedEntityAction.UPDATE

	const { 
		titleDiff, 
		descriptionDiff, 
		hasTitleDiff, 
		hasDescriptionDiff 
	} = useInitiativeDiff(
		initiative, 
		entitySuggestion.suggestedValue as UpdateInitiativeModel
	);

	const initiativeResolutions = useMemo(() => {
		return Object.fromEntries(
			Object.entries(resolutions)
				.filter(([key]) => key.startsWith(entitySuggestion.path))
				.map(([key, value]) => [key, value])
		);
	}, [resolutions, entitySuggestion.path]);


	const isUpdateFullyResolved = useMemo(() => {
		return isFullyResolved(entitySuggestion.path);
	}, [entitySuggestion.path, isFullyResolved]);


	return (
		<UpdateInitiativeDiffView
			initiative={initiative}
			suggestion={entitySuggestion}
			resolutions={initiativeResolutions}

			titleDiff={titleDiff}
			descriptionDiff={descriptionDiff}

			shouldShowTitleDiff={hasTitleDiff}
			shouldShowDescriptionDiff={hasDescriptionDiff}
			hasTasksDiff={entitySuggestions.some(s => s.path.startsWith(`${basePath}.tasks`))}

			allResolved={isUpdateFullyResolved}
			loading={isSaving}

			onAcceptField={(field) => resolve(`${basePath}.${field}`, true)}
			onRejectField={(field) => resolve(`${basePath}.${field}`, false)}
			onRollbackField={(field) => rollback(`${basePath}.${field}`)}

			onAcceptAll={() => acceptAll(entitySuggestion.path)}
			onRejectAll={() => rejectAll(entitySuggestion.path)}
			onRollbackAll={() => rollbackAll(entitySuggestion.path)}
			onSave={saveSuggestions}
		/>
	);
};

export default ViewInitiativeDiff;
