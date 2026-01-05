import React, { useMemo } from 'react';
import { useNavigate } from 'react-router';
import { useWorkspaces } from '#hooks/useWorkspaces';
import { useProductVision } from '#hooks/useProductVision';
import { useStrategicPillars } from '#hooks/useStrategicPillars';
import { useProductOutcomes } from '#hooks/useProductOutcomes';
import { useRoadmapWithInitiatives } from '#hooks/useRoadmapWithInitiatives';
import StrategyFlowCanvas from '#components/strategyFlowSpike/StrategyFlowCanvas';
import {
  VisionNodeData,
  PillarNodeData,
  OutcomeNodeData,
  ThemeNodeData,
  InitiativeNodeData,
  EntityType,
  InitiativeStatus,
} from '#components/strategyFlowSpike/types';
import { Skeleton } from '#components/reusable/Skeleton';
import { InitiativeStatus as FullInitiativeStatus } from '#types';

/**
 * Maps full initiative status to canvas initiative status.
 * Filters out completed/archived initiatives.
 * @param {string} status - Full initiative status
 * @returns {InitiativeStatus | null} Canvas status or null if should be filtered
 */
function mapInitiativeStatus(status: string): InitiativeStatus | null {
  switch (status) {
    case FullInitiativeStatus.BACKLOG:
      return 'BACKLOG';
    case FullInitiativeStatus.TO_DO:
      return 'TO_DO';
    case FullInitiativeStatus.IN_PROGRESS:
    case FullInitiativeStatus.BLOCKED:
      return 'IN_PROGRESS';
    case FullInitiativeStatus.DONE:
    case FullInitiativeStatus.ARCHIVED:
      return null;
    default:
      return 'TO_DO';
  }
}

/**
 * Strategy Flow Page component.
 * Fetches all strategic entities and displays them in an interactive canvas visualization.
 * Shows the complete product strategy: Vision → Pillars → Outcomes → Themes → Initiatives.
 *
 * @returns {React.ReactElement} The strategy flow page
 */
const StrategyFlowPage: React.FC = () => {
  const navigate = useNavigate();
  const { currentWorkspace } = useWorkspaces();
  const workspaceId = currentWorkspace?.id || '';

  const { vision, isLoading: isLoadingVision } = useProductVision(workspaceId);
  const { pillars, isLoading: isLoadingPillars } = useStrategicPillars(workspaceId);
  const { outcomes, isLoading: isLoadingOutcomes } = useProductOutcomes(workspaceId);
  const {
    prioritizedThemes,
    unprioritizedThemes,
    isLoading: isLoadingThemes,
    isLoadingInitiatives,
  } = useRoadmapWithInitiatives(workspaceId);

  const allThemes = useMemo(
    () => [...prioritizedThemes, ...unprioritizedThemes],
    [prioritizedThemes, unprioritizedThemes]
  );

  const isLoading =
    isLoadingVision ||
    isLoadingPillars ||
    isLoadingOutcomes ||
    isLoadingThemes ||
    isLoadingInitiatives;

  // Build ID to identifier lookup maps
  const pillarIdToIdentifier = useMemo(() => {
    const map = new Map<string, string>();
    pillars.forEach((pillar) => {
      map.set(pillar.id, pillar.identifier);
    });
    return map;
  }, [pillars]);

  const outcomeIdToIdentifier = useMemo(() => {
    const map = new Map<string, string>();
    outcomes.forEach((outcome) => {
      map.set(outcome.id, outcome.identifier);
    });
    return map;
  }, [outcomes]);

  const themeIdToIdentifier = useMemo(() => {
    const map = new Map<string, string>();
    allThemes.forEach((theme) => {
      map.set(theme.id, theme.identifier);
    });
    return map;
  }, [allThemes]);

  // Transform vision data
  const visionNodeData: VisionNodeData | undefined = useMemo(() => {
    if (!vision) return undefined;
    // Split vision text: use first sentence as name, rest as description
    const visionText = vision.vision_text || '';
    const firstSentenceEnd = visionText.match(/[.!?]\s/);
    if (firstSentenceEnd) {
      return {
        name: visionText.substring(0, firstSentenceEnd.index! + 1).trim(),
        description: visionText.substring(firstSentenceEnd.index! + 1).trim(),
      };
    }
    return {
      name: 'Product Vision',
      description: visionText,
    };
  }, [vision]);

  // Transform pillars data
  const pillarNodes: PillarNodeData[] = useMemo(() => {
    return pillars.map((pillar) => ({
      identifier: pillar.identifier,
      name: pillar.name,
      description: pillar.description || '',
    }));
  }, [pillars]);

  // Transform outcomes data
  const outcomeNodes: OutcomeNodeData[] = useMemo(() => {
    return outcomes.map((outcome) => ({
      identifier: outcome.identifier,
      name: outcome.name,
      description: outcome.description || '',
      pillar_identifiers: outcome.pillar_ids
        .map((pillarId) => pillarIdToIdentifier.get(pillarId))
        .filter((id): id is string => id !== undefined),
    }));
  }, [outcomes, pillarIdToIdentifier]);

  // Transform themes data
  const themeNodes: ThemeNodeData[] = useMemo(() => {
    return allThemes.map((theme) => ({
      identifier: theme.identifier,
      name: theme.name,
      description: theme.description,
      outcome_identifiers: theme.outcome_ids
        .map((outcomeId) => outcomeIdToIdentifier.get(outcomeId))
        .filter((id): id is string => id !== undefined),
    }));
  }, [allThemes, outcomeIdToIdentifier]);

  // Transform initiatives data - flatten from all themes
  const initiativeNodes: InitiativeNodeData[] = useMemo(() => {
    const initiatives: InitiativeNodeData[] = [];

    allThemes.forEach((theme) => {
      theme.strategicInitiatives?.forEach((strategicInitiative) => {
        const initiative = strategicInitiative.initiative;
        if (!initiative) return;

        const mappedStatus = mapInitiativeStatus(initiative.status || '');
        if (!mappedStatus) return;

        const themeIdentifier = strategicInitiative.theme_id
          ? themeIdToIdentifier.get(strategicInitiative.theme_id) || null
          : null;

        initiatives.push({
          identifier: initiative.identifier || 'I-UNKNOWN',
          title: initiative.title || '',
          description: initiative.description || '',
          status: mappedStatus,
          theme_identifier: themeIdentifier,
          onNavigate: () => {
            navigate(`/workspace/initiatives/${initiative.id}`);
          },
        });
      });
    });

    return initiatives;
  }, [allThemes, themeIdToIdentifier]);

  // Handle node click navigation
  const handleNodeClick = (id: string, type: EntityType) => {
    switch (type) {
      case 'vision':
        // No navigation for vision (could show modal later)
        break;
      case 'pillar':
        // Navigate to Story Bible
        navigate('/workspace/story-bible?tab=pillars');
        break;
      case 'outcome':
        // Navigate to Story Bible
        navigate('/workspace/story-bible?tab=pillars');
        break;
      case 'theme':
        // Find theme by identifier and navigate to detail page
        const theme = [...prioritizedThemes, ...unprioritizedThemes].find((t) => t.identifier === id);
        if (theme) {
          navigate(`/workspace/story-bible/theme/${theme.id}`);
        }
        break;
      case 'initiative':
        // Find initiative by identifier and navigate to detail page
        const allThemes = [...prioritizedThemes, ...unprioritizedThemes];
        for (const theme of allThemes) {
          const strategicInitiative = theme.strategicInitiatives?.find(
            (si) => si.initiative?.identifier === id
          );
          if (strategicInitiative?.initiative?.id) {
            navigate(`/workspace/initiatives/${strategicInitiative.initiative.id}`);
            return;
          } else {
            console.error(`Initiative ${id} not found in any theme`);
          }
        }
        break;
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full bg-background">
        <div className="text-center space-y-4">
          <Skeleton type="text" width="w-64" />
          <Skeleton type="paragraph" />
        </div>
      </div>
    );
  }

  // Render canvas with transformed data
  return (
    <div className="absolute inset-0 w-full h-full">
      <StrategyFlowCanvas
        vision={visionNodeData}
        pillars={pillarNodes}
        outcomes={outcomeNodes}
        themes={themeNodes}
        initiatives={initiativeNodes}
        onNodeClick={handleNodeClick}
      />
    </div>
  );
};

export default StrategyFlowPage;

