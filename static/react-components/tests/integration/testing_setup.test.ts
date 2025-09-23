import { vi } from "vitest";
import { getPostgrestClient } from "./utils";


vi.mock('#api/api-utils', () => {
    return {
        loadAndValidateJWT: vi.fn(),
        getPostgrestClient: vi.fn().mockImplementation(() => getPostgrestClient()),
        withApiCall: vi.fn(),
    }
})

describe.skip('postgrestClient', () => {
    it('should be able to retrieve the  schema', async () => {
        const response = await getPostgrestClient().from('initiative').select('*').limit(1);

        expect(response.status).toBe(200);
        expect(response.data).toBeDefined();
        expect(response.data?.length).toBe(0);
    })
})

