import React, { useEffect, useState } from 'react';
import { loadAndValidateJWT, isJWTExpired, checkJwtAndRenew } from '#api/jwt';

const OnLogoutRedirectURL = '/';

const AUTH_COOKIE_NAME='access_token'

const checkSessionValidity = async (): Promise<boolean> => {
    try {
        const response = await fetch('/api/user/display-pref');
        if (!response.ok) {
            return false;
        }
        const data = await response.json();
        return !data.error;
    } catch (error) {
        console.error('Session validation error:', error);
        return false;
    }
}

export const SessionResetProvider = ({ children }: { children: React.ReactNode }) => {
    const [isValidatingSession, setIsValidatingSession] = useState(true);

    useEffect(() => {
        const validateSession = async () => {
            try {
                // Check 1: Validate JWT and renew if expired
                await checkJwtAndRenew();

                // Check 2: Validate session with API
                const isSessionValid = await checkSessionValidity();

                if (!isSessionValid) {
                    window.location.href = OnLogoutRedirectURL;
                    return;
                }

                setIsValidatingSession(false);
            } catch (error) {
                // JWT validation/renewal failed
                console.error('Session validation failed:', error);
                window.location.href = OnLogoutRedirectURL;
            }
        };

        // Initial validation
        validateSession();

        // Set up periodic validation (every 5 minutes)
        const intervalId = setInterval(validateSession, 5 * 60 * 1000);

        // Clean up interval on unmount
        return () => clearInterval(intervalId);
    }, []);

    // Show loading or children based on validation state
    return isValidatingSession ? null : <>{children}</>;
};

