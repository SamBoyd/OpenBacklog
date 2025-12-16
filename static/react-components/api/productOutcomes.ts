import { loadAndValidateJWT } from '#api/jwt'

export interface OutcomeCreateRequest {
  name: string;
  description?: string | null;
  pillar_ids?: string[];
}

export interface OutcomeDto {
  id: string;
  workspace_id: string;
  identifier: string;
  name: string;
  description: string | null;
  display_order: number;
  pillar_ids: string[];
  theme_ids: string[];
  created_at: string;
  updated_at: string;
}

export interface OutcomeUpdateRequest {
  name: string;
  description?: string | null;
  pillar_ids?: string[];
}

export interface OutcomeOrderItem {
  id: string;
  display_order: number;
}

export interface OutcomeReorderRequest {
  outcomes: OutcomeOrderItem[];
}

/**
 * Fetches all product outcomes for a workspace using PostgREST.
 * Includes populated pillar_ids and theme_ids from junction tables.
 * @param {string} workspaceId - The workspace ID
 * @returns {Promise<OutcomeDto[]>} List of outcomes ordered by display_order
 */
export async function getProductOutcomes(
  workspaceId: string
): Promise<OutcomeDto[]> {
  const { getPostgrestClient, withApiCall } = await import('#api/api-utils');

  return withApiCall(async () => {
    const response = await getPostgrestClient()
      .from('product_outcomes')
      .select(`
        *,
        outcome_pillar_links(pillar_id),
        theme_outcome_links(theme_id)
      `)
      .eq('workspace_id', workspaceId)
      .order('display_order');

    if (response.error) {
      throw new Error(`Error loading product outcomes: ${response.error.message}`);
    }

    // Transform junction table data to ID arrays
    return response.data.map((outcome: any) => ({
      ...outcome,
      pillar_ids: outcome.outcome_pillar_links?.map((link: any) => link.pillar_id) || [],
      theme_ids: outcome.theme_outcome_links?.map((link: any) => link.theme_id) || [],
      outcome_pillar_links: undefined,
      theme_outcome_links: undefined,
    }));
  });
}

/**
 * Creates a new product outcome for a workspace.
 * @param {string} workspaceId - The workspace ID
 * @param {OutcomeCreateRequest} request - Request containing name, description, and optional pillar_ids
 * @returns {Promise<OutcomeDto>} The created outcome
 */
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

/**
 * Updates an existing product outcome.
 * @param {string} workspaceId - The workspace ID
 * @param {string} outcomeId - The outcome ID to update
 * @param {OutcomeUpdateRequest} request - Request containing updated fields
 * @returns {Promise<OutcomeDto>} The updated outcome
 */
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

/**
 * Deletes a product outcome.
 * @param {string} workspaceId - The workspace ID
 * @param {string} outcomeId - The outcome ID to delete
 * @returns {Promise<void>}
 */
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

/**
 * Reorders product outcomes by updating their display order.
 * @param {string} workspaceId - The workspace ID
 * @param {OutcomeReorderRequest} request - Request with new display orders for all outcomes
 * @returns {Promise<OutcomeDto[]>} List of reordered outcomes
 */
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
