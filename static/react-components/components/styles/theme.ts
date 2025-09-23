import { Theme } from '#hooks/useUserPreferences';

export const getThemeStyles = (theme?: Theme) => {
    const isDark = theme === Theme.DARK;

    return {
        // Common container styles
        container: {
            backgroundColor: isDark
                ? 'var(--bg-dark, #0a0a0a)'   // Deeper black background
                : 'var(--bg-light, #ffffff)',
            color: isDark
                ? 'var(--text-light, #f8f8f8)' // Brighter white text
                : 'var(--text-dark, #1f2937)'
        },

        // Text colors
        text: {
            primary: { color: isDark ? 'var(--text-primary-dark, #f8f8f8)' : 'var(--text-primary-light, #111827)' },
            secondary: { color: isDark ? 'var(--text-secondary-dark, #a1a1aa)' : 'var(--text-secondary-light, #4b5563)' },
            muted: { color: isDark ? 'var(--text-muted-dark, #71717a)' : 'var(--text-muted-light, #6b7280)' },
        },

        // Background colors
        bg: {
            primary: { backgroundColor: isDark ? 'var(--bg-dark, #0a0a0a)' : 'var(--bg-light, #ffffff)' },
            secondary: { backgroundColor: isDark ? 'var(--bg-secondary-dark, #18181b)' : 'var(--bg-secondary-light, #f3f4f6)' },
            highlight: { backgroundColor: isDark ? 'var(--bg-highlight-dark, #27272a)' : 'var(--bg-highlight-light, #e5e7eb)' }
        },

        // Border colors
        border: {
            primary: {
                borderWidth: '1px',
                borderStyle: 'solid',
                borderRadius: '6px',
                borderColor: isDark ? 'var(--text-primary-dark, #f8f8f8)' : 'var(--text-primary-light, #111827)',
            },
            secondary: {
                borderWidth: '1px',
                borderStyle: 'solid',
                borderRadius: '6px',
                borderColor: isDark ? 'var(--border-secondary-dark, #27272a)' : 'var(--border-secondary-light, #e5e7eb)'
            },
            none: {
                borderWidth: '0px',
                borderStyle: 'none',
                borderRadius: '6px',
                borderColor: isDark ? 'var(--bg-dark, #0a0a0a)' : 'var(--bg-light, #ffffff)',
            },
        },

        // Button styles
        button: {
            primary: {
                backgroundColor: isDark
                    ? 'var(--bg-dark, #0a0a0a)'   // Deeper black background
                    : 'var(--bg-light, #ffffff)',
                color: isDark ? 'var(--text-primary-dark, #f8f8f8)' : 'var(--text-primary-light, #111827)',
                borderRadius: '8px',
                borderColor: isDark ? 'var(--text-primary-dark, #f8f8f8)' : 'var(--text-primary-light, #111827)',
                borderWidth: '1px',
                borderStyle: 'solid',
            },
            secondary: {
                backgroundColor: isDark
                    ? 'var(--bg-dark, #0a0a0a)'   // Deeper black background
                    : 'var(--bg-light, #ffffff)',
                color: isDark ? 'var(--text-muted-dark, #71717a)' : 'var(--text-muted-light, #6b7280)',
                borderColor: isDark ? 'var(--text-muted-dark, #71717a)' : 'var(--text-muted-light, #6b7280)',
                borderWidth: '1px',
                borderStyle: 'solid',
            },
            danger: {
                backgroundColor: isDark ? 'var(--btn-danger-dark, #ef4444)' : 'var(--btn-danger-light, #dc2626)',
                color: 'var(--btn-text, #ffffff)'
            },
            success: {
                backgroundColor: isDark ? 'var(--btn-success-dark, #10b981)' : 'var(--btn-success-light, #059669)',
                color: 'var(--btn-text, #ffffff)'
            },
        },

        // Card styles
        card: {
            container: {
                backgroundColor: isDark ? 'var(--bg-dark, #0a0a0a)' : 'var(--bg-light, #ffffff)',
                borderColor: isDark ? 'var(--card-border-dark, #27272a)' : 'var(--card-border-light, #e5e7eb)',
            },
            header: {
                borderBottomColor: isDark ? 'var(--card-header-border-dark, #27272a)' : 'var(--card-header-border-light, #e5e7eb)'
            },
            body: {},
            footer: {
                borderTopColor: isDark ? 'var(--card-footer-border-dark, #27272a)' : 'var(--card-footer-border-light, #e5e7eb)'
            },
        },

        // Form controls
        input: {
            backgroundColor: isDark
                ? 'var(--input-bg-dark, #18181b)'
                : 'var(--input-bg-light, #ffffff)',
            borderColor: isDark
                ? 'var(--input-border-dark, #27272a)'
                : 'var(--input-border-light, #d1d5db)',
            color: isDark
                ? 'var(--input-text-dark, #f8f8f8)'
                : 'var(--input-text-light, #1f2937)',
        },

        // Icons
        icon: { color: isDark ? 'var(--icon-color-dark, #a1a1aa)' : 'var(--icon-color-light, #6b7280)' },

        // Status indicators
        status: {
            success: { color: isDark ? 'var(--status-success-dark, #10b981)' : 'var(--status-success-light, #059669)' },
            error: { color: isDark ? 'var(--status-error-dark, #ef4444)' : 'var(--status-error-light, #dc2626)' },
            warning: { color: isDark ? 'var(--status-warning-dark, #f59e0b)' : 'var(--status-warning-light, #d97706)' },
            info: { color: isDark ? 'var(--status-info-dark, #3b82f6)' : 'var(--status-info-light, #2563eb)' },
        }
    };
};