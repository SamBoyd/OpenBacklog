import { expect, test, vi } from 'vitest';
import { afterAll, afterEach, beforeAll } from 'vitest';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { postChecklistItem, deleteChecklistItem } from './checklistItems';

const jwtBuilder = require('jwt-builder');


export const restHandlers = []
const server = setupServer(...restHandlers);

const jwtWithExpiry = (expiry: number) => {
    return jwtBuilder({
        algorithm: 'HS256',
        secret: 'super-secret',
        nbf: true,
        exp: (new Date()).getTime() + expiry,
        iss: 'https://example.com',
        userId: '539e4cba-4893-428a-bafd-1110f023514f',
        headers: {
            kid: '2016-11-17'
        }
    });
}

// Start server before all tests
beforeAll(() => {
    server.listen({ onUnhandledRequest: 'error' });
    console.error = vi.fn();

    document.cookie = `auth0_jwt=${jwtWithExpiry(10)}; expires=${new Date(Date.now() + 3600 * 1000).toUTCString()}; path=/;`;
    document.cookie = `refresh_token=refresh_token; expires=${new Date(Date.now() + 3600 * 1000).toUTCString()}; path=/;`;
});

const originalConsoleError = console.error;

// Close server after all tests
afterAll(() => {
    server.close();
    console.error = originalConsoleError;
});

// Reset handlers after each test for test isolation
afterEach(() => server.resetHandlers());


describe.skip('postChecklistItem', () => {
    it('posts a checklist item and receives the id of the new row back', async () => {
        let sentJson: any;

        server.use(
            http.post(
                'http://localhost:3000/checklist',
                async ({ request }) => {
                    sentJson = await request.json();
                    return HttpResponse.json([{ id: '14b96e1f-2f0a-4dff-968e-bb60a8ca9fde' }]);
                }),
        );

        const checklistItem = {
            id: '14b96e1f-2f0a-4dff-968e-bb60a8ca9fde',
            order: 0,
            title: 'This is a checklist item',
            task_id: '3ea33233-0c90-41fc-9d26-185a7de67b51',
            is_complete: false,
        }

        const response = await postChecklistItem(checklistItem);
        expect(response).toEqual({
            id: '14b96e1f-2f0a-4dff-968e-bb60a8ca9fde',
        });

        expect(sentJson).toMatchObject(
            {
                id: '14b96e1f-2f0a-4dff-968e-bb60a8ca9fde',
                order: 0,
                title: 'This is a checklist item',
                task_id: '3ea33233-0c90-41fc-9d26-185a7de67b51',
                is_complete: false,
            }
        )
    });

    it('should be able to post a ChecklistItem without an id', async () => {
        server.use(
            http.post(
                'http://localhost:3000/checklist',
                async ({ request }) => {
                    return HttpResponse.json([{ id: '14b96e1f-2f0a-4dff-968e-bb60a8ca9fde' }]);
                }),
        );

        const response = await postChecklistItem({
            order: 0,
            title: 'This is a checklist item',
            task_id: '3ea33233-0c90-41fc-9d26-185a7de67b51',
            is_complete: false,
        });

        expect(response).toEqual({
            id: '14b96e1f-2f0a-4dff-968e-bb60a8ca9fde',
        });
    });
})

describe.skip('deleteChecklistItem', () => {
    test('deletes the checklist item successfully', async () => {
        server.use(
            http.delete('http://localhost:3000/checklist', () => {
                return HttpResponse.json({}, { status: 200 });
            }),
        );
        await expect(deleteChecklistItem('789')).resolves.toBeUndefined();
    });
})