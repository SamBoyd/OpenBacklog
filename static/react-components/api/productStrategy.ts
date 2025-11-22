import { loadAndValidateJWT } from '#api/jwt'

export interface VisionUpdateRequest {
  vision_text: string;
}

export interface VisionDto {
  id: string;
  workspace_id: string;
  vision_text: string;
  created_at: string;
  updated_at: string;
}

export interface PillarCreateRequest {
  name: string;
  description?: string | null;
}

export interface PillarDto {
  id: string;
  workspace_id: string;
  name: string;
  description: string | null;
  display_order: number;
  outcome_ids: string[];
  created_at: string;
  updated_at: string;
}

export async function getWorkspaceVision(
  workspaceId: string
): Promise<VisionDto | null> {
  const response = await fetch(`/api/workspaces/${workspaceId}/vision`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error('Failed to fetch workspace vision');
  }

  return response.json();
}

export async function upsertWorkspaceVision(
  workspaceId: string,
  request: VisionUpdateRequest
): Promise<VisionDto> {
  const response = await fetch(`/api/workspaces/${workspaceId}/vision`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to save workspace vision');
  }

  return response.json();
}

export async function getStrategicPillars(
  workspaceId: string
): Promise<PillarDto[]> {
  const response = await fetch(`/api/workspaces/${workspaceId}/pillars`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch strategic pillars');
  }

  return response.json();
}

export async function createStrategicPillar(
  workspaceId: string,
  request: PillarCreateRequest
): Promise<PillarDto> {
  const response = await fetch(`/api/workspaces/${workspaceId}/pillars`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create strategic pillar');
  }

  return response.json();
}

export interface PillarUpdateRequest {
  name: string;
  description?: string | null;
}

export async function updateStrategicPillar(
  workspaceId: string,
  pillarId: string,
  request: PillarUpdateRequest
): Promise<PillarDto> {
  const response = await fetch(`/api/workspaces/${workspaceId}/pillars/${pillarId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update strategic pillar');
  }

  return response.json();
}

export async function deleteStrategicPillar(
  workspaceId: string,
  pillarId: string
): Promise<void> {
  const response = await fetch(`/api/workspaces/${workspaceId}/pillars/${pillarId}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to delete strategic pillar');
  }
}

export interface PillarOrderItem {
  id: string;
  display_order: number;
}

export interface PillarReorderRequest {
  pillars: PillarOrderItem[];
}

export async function reorderStrategicPillars(
  workspaceId: string,
  request: PillarReorderRequest
): Promise<PillarDto[]> {
  const response = await fetch(`/api/workspaces/${workspaceId}/pillars/reorder`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to reorder strategic pillars');
  }

  return response.json();
}

export interface OutcomeCreateRequest {
  name: string;
  description?: string | null;
  pillar_ids?: string[];
}

export interface OutcomeDto {
  id: string;
  workspace_id: string;
  name: string;
  description: string | null;
  display_order: number;
  pillar_ids: string[];
  created_at: string;
  updated_at: string;
}

export async function getProductOutcomes(
  workspaceId: string
): Promise<OutcomeDto[]> {
  const response = await fetch(`/api/workspaces/${workspaceId}/outcomes`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch product outcomes');
  }

  return response.json();
}

export async function createProductOutcome(
  workspaceId: string,
  request: OutcomeCreateRequest
): Promise<OutcomeDto> {
  const response = await fetch(`/api/workspaces/${workspaceId}/outcomes`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create product outcome');
  }

  return response.json();
}

export interface OutcomeUpdateRequest {
  name: string;
  description?: string | null;
  pillar_ids?: string[];
}

export async function updateProductOutcome(
  workspaceId: string,
  outcomeId: string,
  request: OutcomeUpdateRequest
): Promise<OutcomeDto> {
  const response = await fetch(`/api/workspaces/${workspaceId}/outcomes/${outcomeId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update product outcome');
  }

  return response.json();
}

export async function deleteProductOutcome(
  workspaceId: string,
  outcomeId: string
): Promise<void> {
  const response = await fetch(`/api/workspaces/${workspaceId}/outcomes/${outcomeId}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to delete product outcome');
  }
}

export interface OutcomeOrderItem {
  id: string;
  display_order: number;
}

export interface OutcomeReorderRequest {
  outcomes: OutcomeOrderItem[];
}

export async function reorderProductOutcomes(
  workspaceId: string,
  request: OutcomeReorderRequest
): Promise<OutcomeDto[]> {
  const response = await fetch(`/api/workspaces/${workspaceId}/outcomes/reorder`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to reorder product outcomes');
  }

  return response.json();
}

export interface ThemeCreateRequest {
  name: string;
  description: string;
  outcome_ids?: string[];
}

export interface ThemeDto {
  id: string;
  workspace_id: string;
  name: string;
  description: string;
  outcome_ids: string[];
  hero_ids: string[];
  villain_ids: string[];
  created_at: string;
  updated_at: string;
}

/**
 * Extended theme data for roadmap overview display.
 * Inherits narrative context (hero_ids, villain_ids) from ThemeDto
 * and adds arc-specific fields for progress tracking.
 */
export interface ArcDto extends ThemeDto {
  // Runtime populated heroes and villains objects (for display purposes)
  heroes?: Array<{ id: string; name: string }>;
  villains?: Array<{ id: string; name: string }>;
  status: 'in_progress' | 'complete' | 'planned';
  progress_percentage?: number;
  scenes_completed?: number;
  scenes_total?: number;
  started_quarter?: string; // e.g., "Q1 2024"
  expected_quarter?: string; // e.g., "Q2 2024"
}

export async function getRoadmapThemes(
  workspaceId: string
): Promise<ThemeDto[]> {
  const response = await fetch(`/api/workspaces/${workspaceId}/themes`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch roadmap themes');
  }

  return response.json();
}

export async function createRoadmapTheme(
  workspaceId: string,
  request: ThemeCreateRequest
): Promise<ThemeDto> {
  const response = await fetch(`/api/workspaces/${workspaceId}/themes`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create roadmap theme');
  }

  return response.json();
}

export interface ThemeUpdateRequest {
  name: string;
  description: string;
  outcome_ids?: string[];
}

export async function updateRoadmapTheme(
  workspaceId: string,
  themeId: string,
  request: ThemeUpdateRequest
): Promise<ThemeDto> {
  const response = await fetch(`/api/workspaces/${workspaceId}/themes/${themeId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update roadmap theme');
  }

  return response.json();
}

export async function deleteRoadmapTheme(
  workspaceId: string,
  themeId: string
): Promise<void> {
  const response = await fetch(`/api/workspaces/${workspaceId}/themes/${themeId}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to delete roadmap theme');
  }
}

export interface ThemeOrderItem {
  id: string;
  display_order: number;
}

export interface ThemeReorderRequest {
  themes: ThemeOrderItem[];
}

export async function reorderRoadmapThemes(
  workspaceId: string,
  request: ThemeReorderRequest
): Promise<ThemeDto[]> {
  const response = await fetch(`/api/workspaces/${workspaceId}/themes/reorder`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to reorder roadmap themes');
  }

  return response.json();
}

export async function getPrioritizedThemes(
  workspaceId: string
): Promise<ThemeDto[]> {
  const response = await fetch(`/api/workspaces/${workspaceId}/themes/prioritized`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch prioritized roadmap themes');
  }

  return response.json();
}

export async function getUnprioritizedThemes(
  workspaceId: string
): Promise<ThemeDto[]> {
  const response = await fetch(`/api/workspaces/${workspaceId}/themes/unprioritized`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch unprioritized roadmap themes');
  }

  return response.json();
}

export interface ThemePrioritizeRequest {
  position: number;
}

export async function prioritizeTheme(
  workspaceId: string,
  themeId: string,
  request: ThemePrioritizeRequest
): Promise<ThemeDto> {
  const response = await fetch(`/api/workspaces/${workspaceId}/themes/${themeId}/prioritize`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to prioritize roadmap theme');
  }

  return response.json();
}

export async function deprioritizeTheme(
  workspaceId: string,
  themeId: string
): Promise<ThemeDto> {
  const response = await fetch(`/api/workspaces/${workspaceId}/themes/${themeId}/deprioritize`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to deprioritize roadmap theme');
  }

  return response.json();
}

export interface StrategicInitiativeCreateRequest {
  pillar_id?: string | null;
  theme_id?: string | null;
  description?: string | null;
  narrative_intent?: string | null;
}

export interface StrategicInitiativeDto {
  id: string;
  initiative_id: string;
  workspace_id: string;
  pillar_id: string | null;
  theme_id: string | null;
  description: string | null;
  narrative_intent: string | null;
  created_at: string;
  updated_at: string;
}

export async function getStrategicInitiative(
  initiativeId: string
): Promise<StrategicInitiativeDto | null> {
  const response = await fetch(`/api/initiatives/${initiativeId}/strategic-context`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error('Failed to fetch strategic initiative');
  }

  return response.json();
}

export async function createStrategicInitiative(
  initiativeId: string,
  request: StrategicInitiativeCreateRequest
): Promise<StrategicInitiativeDto> {
  const response = await fetch(`/api/initiatives/${initiativeId}/strategic-context`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create strategic initiative');
  }

  return response.json();
}

export interface StrategicInitiativeUpdateRequest {
  pillar_id?: string | null;
  theme_id?: string | null;
  description?: string | null;
  narrative_intent?: string | null;
}

export async function updateStrategicInitiative(
  initiativeId: string,
  request: StrategicInitiativeUpdateRequest
): Promise<StrategicInitiativeDto> {
  const response = await fetch(`/api/initiatives/${initiativeId}/strategic-context`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update strategic initiative');
  }

  return response.json();
}

export async function getStrategicInitiativesByTheme(
  workspaceId: string,
  themeId: string
): Promise<StrategicInitiativeDto[]> {
  const { getPostgrestClient, withApiCall } = await import('#api/api-utils');

  return withApiCall(async () => {
    const response = await getPostgrestClient()
      .from('strategic_initiatives')
      .select('*, initiative(id, identifier, title)')
      .eq('workspace_id', workspaceId)
      .eq('theme_id', themeId);

    if (response.error) {
      console.error('Error loading strategic initiatives by theme', response.error);
      throw new Error('Error loading strategic initiatives by theme');
    }

    return response.data as StrategicInitiativeDto[];
  });
}
