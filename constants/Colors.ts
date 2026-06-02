const tintColorLight = '#007AFF';
const tintColorDark = '#fff';

export default {
  light: {
    text: '#111827',
    background: '#F9FAFB', // Light gray background for modern feel
    tint: tintColorLight,
    primary: '#FF3B30', // Emergency Red
    secondary: '#007AFF', // Action Blue
    muted: '#6B7280',
    border: '#E5E7EB',
    card: '#FFFFFF',
    success: '#34C759',
    warning: '#FF9500',
    error: '#FF3B30',
    tabIconDefault: '#ccc',
    tabIconSelected: tintColorLight,
  },
  dark: {
    text: '#fff',
    background: '#000',
    tint: tintColorDark,
    primary: '#FF3B30',
    secondary: '#0A84FF',
    muted: '#9CA3AF',
    border: '#374151',
    card: '#1C1C1E',
    success: '#30D158',
    warning: '#FF9F0A',
    error: '#FF453A',
    tabIconDefault: '#ccc',
    tabIconSelected: tintColorDark,
  },
};
