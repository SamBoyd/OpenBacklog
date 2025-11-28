import { loadAndValidateJWT } from '#api/jwt'
import { StrategicInitiativeDto } from '#types';

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

export interface HeroRef {
  id: string;
  name: string;
  identifier: string;
  description: string | null;
  is_primary: boolean;
}

export interface VillainRef {
  id: string;
  name: string;
  identifier: string;
  description: string;
  villain_type: string;
  severity: number;
  is_defeated: boolean;
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
  // Embedded heroes and villains (populated by PostgREST queries)
  heroes?: HeroRef[];
  villains?: VillainRef[];
}

/**
 * Theme data enriched with narrative context for roadmap overview display.
 * Extends ThemeDto with embedded heroes and villains populated from hero_ids and villain_ids.
 * Used for displaying themes in prioritized/unprioritized roadmap sections.
 */
export interface ArcDto extends ThemeDto {
  // Inherits all ThemeDto fields including embedded heroes and villains
  // No additional fields - this is now effectively an alias for ThemeDto with narratives
}

/**
 * Fetches all roadmap themes for a workspace with embedded heroes and villains.
 * @param {string} workspaceId - The workspace ID
 * @returns {Promise<ThemeDto[]>} List of themes with heroes and villains
 */
export async function getRoadmapThemes(
  workspaceId: string
): Promise<ThemeDto[]> {
  const { getPostgrestClient, withApiCall } = await import('#api/api-utils');

  return withApiCall(async () => {
    const response = await getPostgrestClient()
      .from('roadmap_themes')
      .select(`
        *,
        roadmap_theme_heroes(
          hero:hero_id(
            id,
            name,
            identifier,
            description,
            is_primary
          )
        ),
        roadmap_theme_villains(
          villain:villain_id(
            id,
            name,
            identifier,
            description,
            villain_type,
            severity,
            is_defeated
          )
        )
      `)
      .eq('workspace_id', workspaceId);

    if (response.error) {
      console.error('Error loading roadmap themes', response.error);
      throw new Error(`Error loading roadmap themes: ${response.error.message}`);
    }

    // Transform the response to extract heroes and villains from junction tables
    return response.data.map((theme: any) => ({
      ...theme,
      heroes: theme.roadmap_theme_heroes?.map((rth: any) => rth.hero).filter(Boolean) || [],
      villains: theme.roadmap_theme_villains?.map((rtv: any) => rtv.villain).filter(Boolean) || [],
      roadmap_theme_heroes: undefined,
      roadmap_theme_villains: undefined,
    }));
  });
}

/**
 * Fetches a single roadmap theme by ID with embedded heroes and villains.
 * @param {string} workspaceId - The workspace ID
 * @param {string} themeId - The theme ID
 * @returns {Promise<ThemeDto>} Theme with heroes and villains
 */
export async function getRoadmapThemeById(
  workspaceId: string,
  themeId: string
): Promise<ThemeDto> {
  const { getPostgrestClient, withApiCall } = await import('#api/api-utils');

  return withApiCall(async () => {
    const response = await getPostgrestClient()
      .from('roadmap_themes')
      .select(`
        *,
        roadmap_theme_heroes(
          hero:hero_id(
            id,
            name,
            identifier,
            description,
            is_primary
          )
        ),
        roadmap_theme_villains(
          villain:villain_id(
            id,
            name,
            identifier,
            description,
            villain_type,
            severity,
            is_defeated
          )
        )
      `)
      .eq('workspace_id', workspaceId)
      .eq('id', themeId)
      .maybeSingle();

    if (response.error) {
      console.error('Error loading roadmap theme', response.error);
      throw new Error(`Error loading roadmap theme: ${response.error.message}`);
    }

    if (!response.data) {
      throw new Error('Roadmap theme not found');
    }

    const theme = response.data;

    // Transform the response to extract heroes and villains from junction tables
    return {
      ...theme,
      heroes: theme.roadmap_theme_heroes?.map((rth: any) => rth.hero).filter(Boolean) || [],
      villains: theme.roadmap_theme_villains?.map((rtv: any) => rtv.villain).filter(Boolean) || [],
      roadmap_theme_heroes: undefined,
      roadmap_theme_villains: undefined,
    };
  });
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

export async function getStrategicInitiative(
  initiativeId: string
): Promise<StrategicInitiativeDto | null> {
  const { getPostgrestClient, withApiCall } = await import('#api/api-utils');

  return withApiCall(async () => {
    const response = await getPostgrestClient()
      .from('strategic_initiatives')
      .select(`
        *,
        initiative:initiative_id(*),
        pillar:pillar_id(*),
        theme:theme_id(*),
        strategic_initiative_heroes(
          hero:hero_id(id, name, identifier, description, is_primary)
        ),
        strategic_initiative_villains(
          villain:villain_id(id, name, identifier, description, villain_type, severity, is_defeated)
        ),
        strategic_initiative_conflicts(
          conflict:conflict_id(id, identifier, hero_id, villain_id, description, status, story_arc_id, resolved_at, resolved_by_initiative_id)
        )
      `)
      .eq('initiative_id', initiativeId)
      .maybeSingle();

    if (response.error) throw new Error(response.error.message);
    if (!response.data) return null;

    // Transform junction table data to embedded arrays
    return {
      ...response.data,
      heroes: response.data.strategic_initiative_heroes?.map((sih: any) => sih.hero).filter(Boolean) || [],
      villains: response.data.strategic_initiative_villains?.map((siv: any) => siv.villain).filter(Boolean) || [],
      conflicts: response.data.strategic_initiative_conflicts?.map((sic: any) => sic.conflict).filter(Boolean) || [],
    };
  });
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

/**
 * Fetches strategic initiatives for a theme with full Initiative data including tasks.
 * This provides complete context for displaying story arcs with their initiatives.
 * @param {string} workspaceId - The workspace ID
 * @param {string} themeId - The theme ID
 * @returns {Promise<StrategicInitiativeDto[]>} Strategic initiatives with embedded initiative and task data
 */
export async function getStrategicInitiativesByTheme(
  workspaceId: string,
  themeId: string
): Promise<StrategicInitiativeDto[]> {
  const { getPostgrestClient, withApiCall } = await import('#api/api-utils');

  return withApiCall(async () => {
    const response = await getPostgrestClient()
      .from('strategic_initiatives')
      .select(`
        *,
        initiative:initiative_id(
          *,
          tasks:task(
            *,
            checklist(*)
          ),
          orderings(*)
        )
      `)
      .eq('workspace_id', workspaceId)
      .eq('theme_id', themeId);

    if (response.error) {
      console.error('Error loading strategic initiatives by theme', response.error);
      throw new Error(`Error loading strategic initiatives by theme: ${response.error.message}`);
    }

    return response.data as StrategicInitiativeDto[];
  });
}
