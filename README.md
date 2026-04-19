# Arohan - Emergency Response App for the Elderly

Arohan is a mobile application designed to provide immediate assistance to elderly individuals during medical emergencies. Built with **React Native**, **Expo**, and **FastAPI**, it focuses on speed, accessibility, and reliability, ensuring that help is just a tap away.

## 🚀 Key Features

*   **🚨 One-Tap SOS**: A prominent SOS button for instant emergency activation.
*   **🚑 Emergency Assist**: Quick access to call an ambulance and notify pre-configured emergency contacts.
*   **🗣️ AI Voice Guidance**: Real-time, voice-guided instructions for emergency procedures (e.g., CPR). Powered by a custom **FastAPI backend** using **Google Gemini 1.5 Flash API** for intelligent, low-latency conversational assistance.
*   **🔐 OTP Authentication**: Secure and reliable login via SMS OTPs powered by **Twilio**, ensuring only verified users have access.
*   **📍 Location Sharing**: Automatically shares the user's current location with responders and family members using `expo-location`.
*   **🌍 Multi-Language Support**: Fully localized interface supporting English, Hindi, Kannada, Telugu, Tamil, and Malayalam via `i18next`.
*   **⌚ Wearable Integration**: Includes a mock setup flow for pairing with health monitoring wearables.
*   **📱 Responsive Design**: Optimized UI for various screen sizes, ensuring readability and ease of use for elderly users.

## 🛠️ Tech Stack

### Frontend (Mobile App)
*   **Framework**: [React Native](https://reactnative.dev/) with [Expo](https://expo.dev/)
*   **Navigation**: [Expo Router](https://docs.expo.dev/router/introduction/)
*   **State Management**: [Zustand](https://github.com/pmndrs/zustand)
*   **Maps**: [react-native-maps](https://github.com/react-native-maps/react-native-maps)
*   **Internationalization**: [i18next](https://www.i18next.com/) & [react-i18next](https://react.i18next.com/)
*   **Audio/Haptics**: `expo-av`, `expo-speech`, `expo-haptics`
*   **Language**: TypeScript

### Backend (API Services)
*   **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
*   **AI Engine**: [Google Gemini 1.5 Flash](https://deepmind.google/technologies/gemini/flash/) (Speech-to-Text & Generative AI)
*   **Authentication Service**: [Twilio SMS OTP](https://www.twilio.com/en-us/trusted-activation/verify)

## 📂 Project Structure

The project follows the Expo Router file-based routing convention:

```
Arohan/
├── app/                 # Main application screens and routing (Frontend)
├── backend/             # FastAPI server, Twilio OTP & Gemini Voice services
├── components/          # Reusable UI components
├── constants/           # App constants (Colors, Theme, Responsive Utils)
├── store/               # Zustand state stores
├── assets/              # Images, fonts, and other static assets
└── ...
```

## 🏁 Getting Started

### Prerequisites

*   [Node.js](https://nodejs.org/) (v20+ recommended)
*   [Python 3.9+](https://www.python.org/)
*   [Expo Go](https://expo.dev/client) app on your physical device or an Android/iOS emulator.

### Installation & Running Locally

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd Arohan
    ```

2.  **Start the Backend Engine (FastAPI):**
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install -r requirements.txt
    
    # Ensure you set up the environment variables (Twilio & Gemini API Keys)
    # create a .env file and add your credentials.
    
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```

3.  **Start the Frontend (Expo):**
    Open a new terminal window:
    ```bash
    cd Arohan
    npm install
    npx expo start
    ```

4.  **Run on device/emulator:**
    *   **Physical Device**: Scan the QR code with the Expo Go app. *Note: Ensure your device and local development server are on the same WiFi network for backend connectivity.*
    *   **Emulator**: Press `a` for Android or `i` for iOS in the terminal.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.
