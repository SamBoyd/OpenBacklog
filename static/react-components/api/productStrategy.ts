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
  anti_strategy?: string | null;
}

export interface PillarDto {
  id: string;
  workspace_id: string;
  name: string;
  description: string | null;
  anti_strategy: string | null;
  display_order: number;
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
      Authorization: `Bearer ${loadAndValidateJWT()}`,
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
      Authorization: `Bearer ${loadAndValidateJWT()}`,
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
      Authorization: `Bearer ${loadAndValidateJWT()}`,
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
      Authorization: `Bearer ${loadAndValidateJWT()}`,
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
  anti_strategy?: string | null;
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
      Authorization: `Bearer ${loadAndValidateJWT()}`,
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
      'Content-Type': 'application/json',
      Authorization: `Bearer ${loadAndValidateJWT()}`,
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
      Authorization: `Bearer ${loadAndValidateJWT()}`,
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
  metrics?: string | null;
  time_horizon_months?: number | null;
  pillar_ids?: string[];
}

export interface OutcomeDto {
  id: string;
  workspace_id: string;
  name: string;
  description: string | null;
  metrics: string | null;
  time_horizon_months: number | null;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export async function getProductOutcomes(
  workspaceId: string
): Promise<OutcomeDto[]> {
  const response = await fetch(`/api/workspaces/${workspaceId}/outcomes`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${loadAndValidateJWT()}`,
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
      Authorization: `Bearer ${loadAndValidateJWT()}`,
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create product outcome');
  }

  return response.json();
}
