const AUTH_COOKIE_NAME='access_token'
const REFRESH_COOKIE_NAME='refresh_token'

/**
 * Interface for JWT claims structure based on backend implementation
 */
export interface JWTClaims {
    sub: string;                    // user_id
    iat: number;                    // issued at timestamp
    exp: number;                    // expiry timestamp
    email: string;                  // user email
    email_verified: boolean;        // email verification status
    role: string;                   // PostgREST role
    'https://samboyd.dev/role': string;       // Auth0 compatibility role
    'https://samboyd.dev/type': string;       // Auth0 compatibility type
    type: string;                   // token type
    scope: string;                  // token scope
}

export function loadAndValidateJWT(): string {
    // Ensure we're in a browser environment
    if (typeof document === 'undefined') {
        throw new Error('No document available');
    }
    const match = document.cookie.match(new RegExp(`(^| )${AUTH_COOKIE_NAME}=([^;]+)`));
    if (!!!match) {
        throw new Error('JWT cookie not found');
    }
    const token = match[2];
    // Simple validation: JWT must have 3 parts separated by dots
    if (token.split('.').length !== 3) {
        throw new Error('Invalid JWT format');
    }

    return token;
}

export function decodeJWTExpiry(jwt: string): Date {
    const payload = JSON.parse(atob(jwt.split('.')[1]));
    return new Date(payload.exp * 1000);
}

export function isJWTExpired(jwt: string): boolean {
    return decodeJWTExpiry(jwt) < new Date();
}

export function getRefreshToken(): string {
    // Ensure we're in a browser environment
    if (typeof document === 'undefined') {
        throw new Error('No document available');
    }
    const match = document.cookie.match(new RegExp(`(^| )${REFRESH_COOKIE_NAME}=([^;]+)`));
    if (!!!match) {
        throw new Error('Refresh token cookie not found');
    }
    return match[2];
}

export function renewJWT() {
    // Ensure we're in a browser environment
    if (typeof document === 'undefined') {
        throw new Error('No document available');
    }
    // const refreshToken = getRefreshToken();
    // TODO - This needs to use a different domain in production *********
    return fetch('https://samboyd.ngrok.app/auth/renew-jwt', {
        method: 'POST',
    }).then(response => {
        if (!response.ok) {
            throw new Error('Failed to renew JWT');
        }
    }).catch(error => {
        console.error('Failed to renew JWT', error);
        throw error;
    });
}

export function checkJwtAndRenew(): Promise<void> {
    try {
        const jwt = loadAndValidateJWT();
        if (isJWTExpired(jwt)) {
            return renewJWT();
        }
        return Promise.resolve();
    } catch (error) {
        console.error('Failed to check JWT', error);
        return Promise.reject(error);
    }
}

/**
 * Decodes JWT payload and returns the claims
 * @param jwt - The JWT token to decode
 * @returns {JWTClaims} The decoded JWT claims
 * @throws {Error} If JWT format is invalid or payload cannot be decoded
 */
export function decodeJWTClaims(jwt: string): JWTClaims {
    try {
        // JWT must have 3 parts separated by dots
        if (jwt.split('.').length !== 3) {
            throw new Error('Invalid JWT format');
        }
        
        const payload = JSON.parse(atob(jwt.split('.')[1]));
        return payload as JWTClaims;
    } catch (error) {
        throw new Error(`Failed to decode JWT claims: ${(error as Error).message}`);
    }
}

/**
 * Extracts the current user ID from the stored JWT
 * @returns {string | null} The user ID from JWT sub claim, or null if JWT is unavailable/invalid
 */
export function getCurrentUserId(): string | null {
    try {
        const jwt = loadAndValidateJWT();
        if (isJWTExpired(jwt)) {
            return null;
        }
        
        const claims = decodeJWTClaims(jwt);
        return claims.sub;
    } catch (error) {
        console.warn('Failed to get current user ID:', error);
        return null;
    }
}

/**
 * Extracts current user information (ID and email) from the stored JWT
 * @returns {object | null} Object with userId and email, or null if JWT is unavailable/invalid
 */
export function getCurrentUserInfo(): { userId: string; email: string } | null {
    try {
        const jwt = loadAndValidateJWT();
        if (isJWTExpired(jwt)) {
            return null;
        }
        
        const claims = decodeJWTClaims(jwt);
        return {
            userId: claims.sub,
            email: claims.email
        };
    } catch (error) {
        console.warn('Failed to get current user info:', error);
        return null;
    }
}
