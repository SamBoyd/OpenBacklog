import { describe, it, expect, beforeAll, afterEach, afterAll } from 'vitest';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { getUserTransactions, getPaymentMethods } from './accounting';

const server = setupServer();

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe.skip('accounting API', () => {
    describe.skip('getUserTransactions', () => {
        it('should fetch user transactions successfully', async () => {
            const mockTransactions = [
                {
                    id: '550e8400-e29b-41d4-a716-446655440001',
                    user_id: '550e8400-e29b-41d4-a716-446655440002',
                    amount_cents: 5000,
                    source: 'STRIPE',
                    external_id: 'cs_test_123456789',
                    created_at: '2024-01-15T10:30:00Z'
                },
                {
                    id: '550e8400-e29b-41d4-a716-446655440003',
                    user_id: '550e8400-e29b-41d4-a716-446655440002',
                    amount_cents: -1250,
                    source: 'USAGE',
                    external_id: null,
                    created_at: '2024-01-14T15:45:00Z'
                }
            ];

            server.use(
                http.get('/api/accounting/transactions', () => {
                    return HttpResponse.json({
                        transactions: mockTransactions
                    });
                })
            );

            const result = await getUserTransactions();

            expect(result).toEqual(mockTransactions);
        });

        it('should handle API errors', async () => {
            server.use(
                http.get('/api/accounting/transactions', () => {
                    return HttpResponse.json(
                        { error: 'Internal server error' },
                        { status: 500 }
                    );
                })
            );

            await expect(getUserTransactions()).rejects.toThrow('Failed to fetch transactions');
        });

        it('should handle invalid response format', async () => {
            server.use(
                http.get('/api/accounting/transactions', () => {
                    return HttpResponse.json({
                        invalid: 'response'
                    });
                })
            );

            await expect(getUserTransactions()).rejects.toThrow('Invalid response format');
        });
    });

    describe.skip('getPaymentMethods', () => {
        it('should fetch payment methods successfully', async () => {
            const mockPaymentMethods = {
                payment_methods: [
                    {
                        id: 'pm_1234567890',
                        type: 'card',
                        card_brand: 'visa',
                        card_last4: '4242',
                        card_exp_month: 12,
                        card_exp_year: 2025,
                        is_default: true
                    },
                    {
                        id: 'pm_0987654321',
                        type: 'card',
                        card_brand: 'mastercard',
                        card_last4: '8888',
                        card_exp_month: 6,
                        card_exp_year: 2026,
                        is_default: false
                    }
                ],
                default_payment_method_id: 'pm_1234567890'
            };

            server.use(
                http.get('/api/billing/payment-methods', () => {
                    return HttpResponse.json(mockPaymentMethods);
                })
            );

            const result = await getPaymentMethods();

            expect(result.paymentMethods).toHaveLength(2);
            expect(result.paymentMethods[0].id).toBe('pm_1234567890');
            expect(result.paymentMethods[0].isDefault).toBe(true);
            expect(result.defaultPaymentMethodId).toBe('pm_1234567890');
        });

        it('should handle empty payment methods', async () => {
            const mockEmptyResponse = {
                payment_methods: [],
                default_payment_method_id: null
            };

            server.use(
                http.get('/api/billing/payment-methods', () => {
                    return HttpResponse.json(mockEmptyResponse);
                })
            );

            const result = await getPaymentMethods();

            expect(result.paymentMethods).toHaveLength(0);
            expect(result.defaultPaymentMethodId).toBeNull();
        });

        it('should handle API errors', async () => {
            server.use(
                http.get('/api/billing/payment-methods', () => {
                    return HttpResponse.json(
                        { error: 'User not onboarded' },
                        { status: 400 }
                    );
                })
            );

            await expect(getPaymentMethods()).rejects.toThrow('Failed to fetch payment methods');
        });

        it('should handle invalid response format', async () => {
            server.use(
                http.get('/api/billing/payment-methods', () => {
                    return HttpResponse.json({
                        invalid: 'response'
                    });
                })
            );

            await expect(getPaymentMethods()).rejects.toThrow('Invalid response format');
        });
    });
}); 