import Colors from './Colors';
import { rf } from './responsive';

const theme = Colors.light; // TODO: specific theme logic hook

export const COLORS = {
    emergency: theme.primary,     // Red - ambulance, SOS
    primary: theme.secondary,       // Blue - actions
    success: theme.success,       // Green - safe
    warning: theme.warning,       // Orange - family
    background: theme.background,
    card: theme.card,
    text: theme.text,
    muted: theme.muted,
    border: theme.border,
    error: theme.error,
};

export const SPACING = {
    xs: rf(4),
    s: rf(8),
    m: rf(16),
    l: rf(24),
    xl: rf(32),
    xxl: rf(48),
};

export const RADIUS = {
    s: rf(8),
    m: rf(12),
    l: rf(16),
    xl: rf(24),
    full: 9999,
};

export const SHADOWS = {
    light: {
        shadowColor: "#000",
        shadowOffset: {
            width: 0,
            height: 2,
        },
        shadowOpacity: 0.1,
        shadowRadius: 3.84,
        elevation: 2,
    },
    medium: {
        shadowColor: "#000",
        shadowOffset: {
            width: 0,
            height: 4,
        },
        shadowOpacity: 0.15,
        shadowRadius: 6,
        elevation: 5,
    }
};
