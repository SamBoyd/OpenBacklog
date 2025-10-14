/**
 * Analytics service for tracking user interactions with Mixpanel
 * Configured to use self-hosted proxy to bypass ad-blockers
 */

import mixpanel, { Mixpanel } from 'mixpanel-browser';
import * as Sentry from "@sentry/react";
import { getCurrentUserInfo } from '#api/jwt';

interface MixpanelConfig {
    token: string;
    apiHost: string;
    libraryUrl: string;
}

/**
 * Initialize with proxy configuration
 */
export const initializeAnalytics = (): void => {
    const mixpanelToken = process.env.MIXPANEL_TOKEN || '';
    const mixpanelProxyUrl = process.env.MIXPANEL_PROXY_URL || '';

    // Configure Mixpanel to use our proxy
    const config: MixpanelConfig = {
        token: mixpanelToken,
        apiHost: mixpanelProxyUrl,
        libraryUrl: `${mixpanelProxyUrl}/lib.min.js`
    };

    if (mixpanelToken !== '') {
        mixpanel.init(config.token, {
            api_host: config.apiHost,
            loaded: (mixpanel: Mixpanel) => {
                console.log('Mixpanel loaded successfully via proxy');
                // Auto-identify current user if JWT is available
                identifyCurrentUser();
                trackAppLoad();
            },
            track_pageview: true,
            persistence: "localStorage",
        });
    }

    const sentryDSN = process.env.SENTRY_DSN || '';
    const sentryProxyUrl = process.env.SENTRY_PROXY_URL || '';

    if (sentryDSN !== '') {
        Sentry.init({
            dsn: sentryDSN,
            tunnel: sentryProxyUrl,
            // Adds request headers and IP for users, for more info visit:
            // https://docs.sentry.io/platforms/javascript/guides/react/configuration/options/#sendDefaultPii
            sendDefaultPii: true,
            environment: process.env.NODE_ENV || 'development',
            integrations: [
                // Add performance monitoring
                Sentry.browserTracingIntegration(),
            ],
            tracesSampleRate: process.env.NODE_ENV === 'production' ? 0 : 1.0,
        });
    }
};

/**
 * Track an event with optional properties
 * @param eventName - Name of the event to track
 * @param properties - Optional properties to include with the event
 */
export const trackEvent = (eventName: string, properties?: Record<string, any>): void => {
    if (process.env.MIXPANEL_TOKEN == '') {
        return;
    }

    try {
        mixpanel.track(eventName, {
            ...properties,
            timestamp: new Date().toISOString(),
            page_url: window.location.href,
            page_title: document.title
        });
    } catch (error) {
        console.error('Failed to track event:', eventName, error);
    }
};

/**
 * Identify a user with unique ID and properties
 * @param userId - Unique identifier for the user
 * @param properties - Optional user properties
 */
export const identifyUser = (userId: string, properties?: Record<string, any>): void => {
    if (process.env.MIXPANEL_TOKEN == '') {
        return;
    }

    try {
        mixpanel.identify(userId);
        if (properties) {
            mixpanel.people.set(properties);
        }
    } catch (error) {
        console.error('Failed to identify user:', userId, error);
    }
};

/**
 * Identify the current user from JWT token
 * Extracts user ID and email from the stored JWT and identifies the user in Mixpanel
 */
export const identifyCurrentUser = (): void => {
    if (process.env.MIXPANEL_TOKEN == '') {
        return;
    }

    try {
        const userInfo = getCurrentUserInfo();
        if (userInfo) {
            identifyUser(userInfo.userId, { 
                '$email': userInfo.email 
            });
        }
    } catch (error) {
        console.error('Failed to identify current user:', error);
    }
};

/**
 * Set user properties
 * @param properties - User properties to set
 */
export const setUserProperties = (properties: Record<string, any>): void => {
    if (process.env.MIXPANEL_TOKEN == '') {
        return;
    }
    try {
        mixpanel.people.set(properties);
    } catch (error) {
        console.error('Failed to set user properties:', error);
    }
};

export const trackAppLoad = (): void => {
    if (process.env.MIXPANEL_TOKEN == '') {
        return;
    }
    trackEvent('App Load', {
        page_path: window.location.pathname,
        referrer: document.referrer
    });
};

/**
 * Track page view
 * @param pageName - Optional name of the page
 */
export const trackPageView = (pageName?: string): void => {
    if (process.env.MIXPANEL_TOKEN == '') {
        return;
    }

    trackEvent('Page View', {
        page_name: pageName || document.title,
        page_path: window.location.pathname,
        referrer: document.referrer
    });
};

/**
 * Reset user tracking (for logout)
 */
export const resetUser = (): void => {
    if (process.env.MIXPANEL_TOKEN == '') {
        return;
    }

    try {
        mixpanel.reset();
    } catch (error) {
        console.error('Failed to reset user:', error);
    }
};

// Common event tracking functions
export const analytics = {
    initialize: initializeAnalytics,
    track: trackEvent,
    identify: identifyUser,
    identifyCurrentUser,
    setUserProperties,
    trackPageView,
    reset: resetUser,

    // Specific event trackers
    trackSignup: (method: string) => trackEvent('User Signup', { method }),
    trackLogin: (method: string) => trackEvent('User Login', { method }),
    trackLogout: () => trackEvent('User Logout'),
    trackError: (error: string, context?: Record<string, any>) =>
        trackEvent('Error Occurred', { error, ...context }),
    trackFeatureUsage: (feature: string, action: string) =>
        trackEvent('Feature Used', { feature, action }),
    trackTaskCreated: (taskType: string) => trackEvent('Task Created', { type: taskType }),
    trackInitiativeCreated: () => trackEvent('Initiative Created'),
};