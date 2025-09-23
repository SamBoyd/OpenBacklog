import { expect, test, vi } from 'vitest';
import { afterAll, beforeAll } from 'vitest';
import { http, HttpResponse } from 'msw';

const jwtBuilder = require('jwt-builder');


import {
    loadAndValidateJWT,
    decodeJWTExpiry,
    getRefreshToken,
    renewJWT,
    checkJwtAndRenew,
    decodeJWTClaims,
    getCurrentUserId,
    getCurrentUserInfo,
    JWTClaims,
} from '#api/jwt';
import { setupServer } from 'msw/node';


// Suppress console.error output during tests
const originalConsoleError = console.error;

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

const createJWTWithClaims = (claims: Partial<JWTClaims>, expiry: number = 3600000): string => {
    const defaultClaims = {
        sub: 'test-user-123',
        iat: Math.floor(Date.now() / 1000),
        email: 'test@example.com',
        email_verified: true,
        role: 'authenticated',
        'https://samboyd.dev/role': 'authenticated',
        'https://samboyd.dev/type': 'accessToken',
        type: 'accessToken',
        scope: 'openid profile email offline_access',
    };
    
    const finalClaims = { ...defaultClaims, ...claims };
    
    // If exp is provided in claims, use it; otherwise use expiry parameter
    const expTime = 'exp' in claims && claims.exp 
        ? claims.exp 
        : Math.floor((Date.now() + expiry) / 1000);
    
    return jwtBuilder({
        algorithm: 'HS256',
        secret: 'super-secret',
        exp: expTime,
        ...finalClaims,
    });
}

const server = setupServer();


// Start server before all tests
beforeAll(() => {
    server.listen({ onUnhandledRequest: 'error' });

    console.error = vi.fn();

    document.cookie = `auth0_jwt=${jwtWithExpiry(10)}; expires=${new Date(Date.now() + 3600 * 1000).toUTCString()}; path=/;`;
    document.cookie = `refresh_token=refresh_token; expires=${new Date(Date.now() + 3600 * 1000).toUTCString()}; path=/;`;
});

// Close server after all tests
afterAll(() => {
    server.close();
    console.error = originalConsoleError;
});


describe.skip('loadAndValidateJWT', () => {
    beforeEach(() => {
        // Properly clear the cookie by setting an expired date
        document.cookie = "refresh_token=skhs8eoenmdccx-MKJxywtFUrdcDh-EnzheJ951Myi-Uf; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
        document.cookie = "auth0_jwt=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    });

    test('should load and validate a valid JWT', () => {
        document.cookie = "auth0_jwt=header.payload.signature";
        const token = loadAndValidateJWT();
        expect(token).toBe("header.payload.signature");
    });

    test('should throw error if JWT cookie is missing', () => {
        // No cookie set
        expect(() => loadAndValidateJWT()).toThrowError('JWT cookie not found');
    });

    test('should throw error if JWT format is invalid', () => {
        document.cookie = "auth0_jwt=invalidtoken";
        expect(() => loadAndValidateJWT()).toThrowError('Invalid JWT format');
    });
});


describe.skip('JWT refresh', () => {
    beforeEach(() => {
        // Properly clear the cookie by setting an expired date
        document.cookie = `auth0_jwt=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
        document.cookie = `refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
    });

    test('should decode the expiry date from a JWT', () => {
        const DEV_JWT = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJodHRwczovL3NhbWJveWQuZGV2L3JvbGUiOiJhdXRoZW50aWNhdGVkIiwic3VkIjoiYWZiOWU5ZWUtZjU0Zi00ZmVmLTgxMmQtNWE0YmQ0MmQzODA0IiwiZXhwIjoxNzM4NDgwNzQ0fQ.aAiGKkOz3poqDl-BHm4lvK4_M0ekLgcCunj01921sdY';

        const expectedExpiry = new Date(1738480744000);

        const expiry = decodeJWTExpiry(DEV_JWT);

        expect(expiry).toEqual(expectedExpiry);
    });

    test('should return true if JWT is expired', () => {
        const DEV_JWT = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJodHRwczovL3NhbWJveWQuZGV2L3JvbGUiOiJhdXRoZW50aWNhdGVkIiwic3VkIjoiYWZiOWU5ZWUtZjU0Zi00ZmVmLTgxMmQtNWE0YmQ0MmQzODA0IiwiZXhwIjoxNzM4NDgwNzQ0fQ.aAiGKkOz3poqDl-BHm4lvK4_M0ekLgcCunj01921sdY';

        const isExpired = new Date() > decodeJWTExpiry(DEV_JWT);

        expect(isExpired).toBe(true);
    });

    test('should be able to retrieve refresh token from cookies', () => {
        document.cookie = "refresh_token=refresh_token";
        const refreshToken = getRefreshToken();
        expect(refreshToken).toBe("refresh_token");
    });

    test('should throw error if refresh token cookie is missing', () => {
        // No cookie set
        document.cookie = 'refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';

        expect(() => getRefreshToken()).toThrowError('Refresh token cookie not found');
    });

    test('can request a new JWT with a refresh token', async () => {
        server.use(
            http.post('https://samboyd.ngrok.app/auth/renew-jwt', async ({ request }) => {
                return HttpResponse.json({
                    "auth0_jwt": jwtWithExpiry(1000),
                    "refresh_token": "skhs8eoenmdccx-MKJxywtFUrdcDh-EnzheJ951Myi-Uf",
                    "token_type": "Bearer"
                });
            })
        );

        // This will throw an error if the fetch call fails
        await renewJWT()
    });

    test('should check if JWT is expired and renew it if it is', async () => {
        server.use(
            http.post('https://samboyd.ngrok.app/auth/renew-jwt', async ({ request }) => {
                return HttpResponse.json({
                    "auth0_jwt": jwtWithExpiry(-1000),
                    "refresh_token": "skhs8eoenmdccx-MKJxywtFUrdcDh-EnzheJ951Myi-Uf",
                    "token_type": "Bearer"
                });
            })
        );

        // Set cookies without expired dates so they exist during the test even if the JWT payload indicates expiry.
        document.cookie = `auth0_jwt=${jwtWithExpiry(-100)}; path=/;`;
        document.cookie = `refresh_token=skhs8eoenmdccx-MKJxywtFUrdcDh-EnzheJ951Myi-Uf; path=/;`;

        await checkJwtAndRenew();
    });

    test('should check if JWT is going to expire in the next 1 hour and renew it if it is', async () => {
        server.use(
            http.post('https://samboyd.ngrok.app/auth/renew-jwt', async ({ request }) => {
                return HttpResponse.json({
                    "auth0_jwt": jwtWithExpiry(1000),
                    "refresh_token": "skhs8eoenmdccx-MKJxywtFUrdcDh-EnzheJ951Myi-Uf",
                    "token_type": "Bearer"
                });
            })
        );

        // Set cookies without expired dates.
        document.cookie = `auth0_jwt=${jwtWithExpiry(1000)}; path=/;`;
        document.cookie = `refresh_token=skhs8eoenmdccx-MKJxywtFUrdcDh-EnzheJ951Myi-Uf; path=/;`;

        await checkJwtAndRenew();
    });
});

describe('JWT Claims Functions', () => {
    beforeEach(() => {
        // Clear cookies
        document.cookie = "access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
        console.error = vi.fn();
    });

    describe('decodeJWTClaims', () => {
        test('should decode valid JWT claims', () => {
            const testClaims = {
                sub: 'test-user-123',
                email: 'test@example.com',
                role: 'authenticated'
            };
            const jwt = createJWTWithClaims(testClaims);
            
            const claims = decodeJWTClaims(jwt);
            
            expect(claims.sub).toBe('test-user-123');
            expect(claims.email).toBe('test@example.com');
            expect(claims.role).toBe('authenticated');
        });

        test('should throw error for invalid JWT format', () => {
            expect(() => decodeJWTClaims('invalid.token')).toThrowError('Invalid JWT format');
            expect(() => decodeJWTClaims('invalid')).toThrowError('Invalid JWT format');
        });

        test('should throw error for invalid JWT payload', () => {
            const invalidJwt = 'header.invalid-base64.signature';
            expect(() => decodeJWTClaims(invalidJwt)).toThrowError('Failed to decode JWT claims');
        });
    });

    describe('getCurrentUserId', () => {
        test('should return user ID from valid JWT', () => {
            const jwt = createJWTWithClaims({ sub: 'user-456' });
            document.cookie = `access_token=${jwt}; path=/;`;
            
            const userId = getCurrentUserId();
            
            expect(userId).toBe('user-456');
        });

        test('should return null when JWT is missing', () => {
            // No JWT cookie set
            const userId = getCurrentUserId();
            
            expect(userId).toBeNull();
        });

        test('should return null when JWT is expired', () => {
            // Create an expired JWT manually
            const expiredPayload = {
                sub: 'user-456',
                exp: Math.floor((Date.now() - 1000) / 1000) // expired 1 second ago
            };
            const encodedPayload = btoa(JSON.stringify(expiredPayload));
            const expiredJwt = `header.${encodedPayload}.signature`;
            document.cookie = `access_token=${expiredJwt}; path=/;`;
            
            const userId = getCurrentUserId();
            
            expect(userId).toBeNull();
        });

        test('should return null when JWT is invalid', () => {
            document.cookie = `access_token=invalid.token; path=/;`;
            
            const userId = getCurrentUserId();
            
            expect(userId).toBeNull();
        });
    });

    describe('getCurrentUserInfo', () => {
        test('should return user info from valid JWT', () => {
            const jwt = createJWTWithClaims({ 
                sub: 'user-789', 
                email: 'user@example.com' 
            });
            document.cookie = `access_token=${jwt}; path=/;`;
            
            const userInfo = getCurrentUserInfo();
            
            expect(userInfo).toEqual({
                userId: 'user-789',
                email: 'user@example.com'
            });
        });

        test('should return null when JWT is missing', () => {
            // No JWT cookie set
            const userInfo = getCurrentUserInfo();
            
            expect(userInfo).toBeNull();
        });

        test('should return null when JWT is expired', () => {
            // Create an expired JWT manually
            const expiredPayload = {
                sub: 'user-789',
                email: 'user@example.com',
                exp: Math.floor((Date.now() - 1000) / 1000) // expired 1 second ago
            };
            const encodedPayload = btoa(JSON.stringify(expiredPayload));
            const expiredJwt = `header.${encodedPayload}.signature`;
            document.cookie = `access_token=${expiredJwt}; path=/;`;
            
            const userInfo = getCurrentUserInfo();
            
            expect(userInfo).toBeNull();
        });

        test('should return null when JWT is invalid', () => {
            document.cookie = `access_token=invalid.token; path=/;`;
            
            const userInfo = getCurrentUserInfo();
            
            expect(userInfo).toBeNull();
        });
    });
});
