import jwt, { Secret, SignOptions } from 'jsonwebtoken';

export const createJWTPayload = (): Record<string, any> => {
    const now = Math.floor(Date.now() / 1000); // Current time in seconds since epoch
    return {
        "https://samboyd.dev/role": "test_authenticated",
        "role": "test_authenticated",
        "type": "accessToken",
        "https://samboyd.dev/type": "accessToken",
        "iss": "https://task-management-184892.us.auth0.com/",
        "sub": "google-oauth2|100049631933995708445",
        "aud": [
            "https://samboyd.dev",
            "https://task-management-184892.us.auth0.com/userinfo"
        ],
        "iat": now,
        "exp": now + 86400, // 1 day in seconds
        "scope": "openid profile email offline_access",
        "azp": "Y75IJDBUoZDf057RZM3C2t8BZUm1pjdX"
    }
}

const DEFAULT_TEST_SECRET: Secret = "this-is-my-super-secret-development-key";
export const createJWT = (payload: Record<string, any>, secret: string = DEFAULT_TEST_SECRET): string => {
    // Ensure consistent options for signing
    const options: SignOptions = {
        algorithm: 'HS256',
        header: {
            alg: 'HS256',
            typ: 'JWT'
        }
    };
    
    return jwt.sign(payload, secret, options);
}
