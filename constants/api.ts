/**
 * API Configuration
 *
 * LOCAL DEV & PRODUCTION DYNAMICS:
 *   - The backend URL is now configured entirely via your `.env` file instead of hardcoded strings.
 *   - Ensure `EXPO_PUBLIC_API_URL` is set inside `C:\projects\Arohan\Arohan\.env`.
 *   - If running Ngrok, simply change the variable there and restart the app.
 */
export const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000";
