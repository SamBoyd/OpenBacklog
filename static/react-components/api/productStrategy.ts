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
