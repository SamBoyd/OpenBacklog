import { expect, test, vi, beforeEach, afterEach } from 'vitest';

// Mock mixpanel before any imports
vi.mock('mixpanel-browser', () => ({
    default: {
        identify: vi.fn(),
        people: {
            set: vi.fn()
        }
    }
}));

// Mock the jwt module
vi.mock('#api/jwt', () => ({
    getCurrentUserInfo: vi.fn()
}));

import { identifyCurrentUser } from './analytics';
import * as jwtModule from '#api/jwt';

// Mock console methods
const originalConsoleError = console.error;

describe('Analytics Service', () => {
    beforeEach(async () => {
        console.error = vi.fn();
        // Reset specific mocks
        const { default: mixpanel } = await import('mixpanel-browser');
        vi.mocked(mixpanel.identify).mockClear();
        vi.mocked(mixpanel.people.set).mockClear();
        vi.mocked(jwtModule.getCurrentUserInfo).mockClear();
    });

    afterEach(() => {
        console.error = originalConsoleError;
    });

    describe('identifyCurrentUser', () => {
        test('should identify user with different email formats', async () => {
            const mockUserInfo = {
                userId: 'user-456',
                email: 'user+test@domain.co.uk'
            };

            vi.mocked(jwtModule.getCurrentUserInfo).mockReturnValue(mockUserInfo);

            identifyCurrentUser();

            const { default: mixpanel } = await import('mixpanel-browser');
            expect(mixpanel.identify).toHaveBeenCalledWith('user-456');
            expect(mixpanel.people.set).toHaveBeenCalledWith({
                '$email': 'user+test@domain.co.uk'
            });
        });

        test('should identify user with ID and email when JWT info is available', async () => {
            const mockUserInfo = {
                userId: 'test-user-123',
                email: 'test@example.com'
            };

            vi.mocked(jwtModule.getCurrentUserInfo).mockReturnValue(mockUserInfo);

            identifyCurrentUser();

            // Get the mocked mixpanel instance
            const { default: mixpanel } = await import('mixpanel-browser');
            expect(mixpanel.identify).toHaveBeenCalledWith('test-user-123');
            expect(mixpanel.people.set).toHaveBeenCalledWith({
                '$email': 'test@example.com'
            });
        });

        test('should not identify user when JWT info is unavailable', async () => {
            vi.mocked(jwtModule.getCurrentUserInfo).mockReturnValue(null);

            identifyCurrentUser();

            const { default: mixpanel } = await import('mixpanel-browser');
            expect(mixpanel.identify).not.toHaveBeenCalled();
            expect(mixpanel.people.set).not.toHaveBeenCalled();
        });

        test('should handle errors gracefully when getCurrentUserInfo throws', async () => {
            vi.mocked(jwtModule.getCurrentUserInfo).mockImplementation(() => {
                throw new Error('JWT error');
            });

            identifyCurrentUser();

            const { default: mixpanel } = await import('mixpanel-browser');
            expect(mixpanel.identify).not.toHaveBeenCalled();
            expect(mixpanel.people.set).not.toHaveBeenCalled();
            expect(console.error).toHaveBeenCalledWith('Failed to identify current user:', expect.any(Error));
        });

        test('should handle errors gracefully when mixpanel methods throw', async () => {
            const mockUserInfo = {
                userId: 'test-user-123',
                email: 'test@example.com'
            };

            vi.mocked(jwtModule.getCurrentUserInfo).mockReturnValue(mockUserInfo);
            
            const { default: mixpanel } = await import('mixpanel-browser');
            vi.mocked(mixpanel.identify).mockImplementation(() => {
                throw new Error('Mixpanel error');
            });

            identifyCurrentUser();

            expect(mixpanel.identify).toHaveBeenCalledWith('test-user-123');
            expect(console.error).toHaveBeenCalledWith('Failed to identify user:', 'test-user-123', expect.any(Error));
        });
    });
});