import { Dimensions, PixelRatio, Platform } from 'react-native';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

// Define a maximum width for scaling calculations to prevent huge elements on desktop
const MAX_SCALE_WIDTH = 500;

// Use the smaller of actual width or max scale width for scaling logic (like fonts)
const SCALED_WIDTH = Math.min(SCREEN_WIDTH, MAX_SCALE_WIDTH);

/**
 * Width-Percentage
 * Converts width percentage to independent pixel (dp).
 * @param widthPercent - The percentage of screen width (e.g., '50%' or 50).
 * @returns {number} Calculated dp value.
 * @note On large screens, this still returns % of FULL width. Use maxWidth in styles for layout constraints.
 */
export const wp = (widthPercent: number | string): number => {
    const elemWidth = typeof widthPercent === "number" ? widthPercent : parseFloat(widthPercent as string);
    return PixelRatio.roundToNearestPixel((SCREEN_WIDTH * elemWidth) / 100);
};

/**
 * Height-Percentage
 * Converts height percentage to independent pixel (dp).
 * @param heightPercent - The percentage of screen height (e.g., '50%' or 50).
 * @returns {number} Calculated dp value.
 */
export const hp = (heightPercent: number | string): number => {
    const elemHeight = typeof heightPercent === "number" ? heightPercent : parseFloat(heightPercent as string);
    return PixelRatio.roundToNearestPixel((SCREEN_HEIGHT * elemHeight) / 100);
};

/**
 * Responsive Font
 * Calculates responsive font size based on screen width, but capped at MAX_SCALE_WIDTH.
 * Standard screen width assumed is ~375 (iPhone X/11/12/13 mini width).
 * @param size - The font size for standard screen.
 * @returns {number} Scaled font size.
 */
export const rf = (size: number): number => {
    const scale = SCALED_WIDTH / 375;
    const newSize = size * scale;
    if (Platform.OS === 'ios') {
        return Math.round(PixelRatio.roundToNearestPixel(newSize));
    } else {
        // Android sometimes scales too huge; keep it slightly tamed
        return Math.round(PixelRatio.roundToNearestPixel(newSize)) - 1;
    }
};
