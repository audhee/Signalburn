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
*           Voice Service - Google Gemini 1.5 Flash
*           LLM Service - Google Gemini 2.0 Pro 
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

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd Arohan
    npm install
    ```

2.  **Environment Setup (Networking):**
    *   Create a `.env` file in the root `Arohan` directory.
    *   Add your local IP (or Ngrok URL) to connect the app to the backend:
        ```env
        EXPO_PUBLIC_API_URL=http://<YOUR_LOCAL_IP>:8000
        ```

### Running the App Locally

You will need to open **4 separate terminal windows** to launch the full environment:

**1. Start the Databases (Redis & PostgreSQL)**
The backend now requires both Redis (for OTPs) and PostgreSQL (for persistent user data). If using Docker Desktop, open two separate terminals or run them sequentially:
```bash
docker run -d -p 6379:6379 --name local-redis redis
docker run -d --name local-postgres -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=arohan_db -p 5433:5432 postgres
```

> **Note on Migrations**: If this is your first time starting PostgreSQL, you must push the schema via Alembic. Open a new terminal:
> ```bash
> cd backend
> venv\Scripts\alembic.exe upgrade head
> ```

**2. Start the Backend API**
Use the provided batch script to automatically activate the environment and bind the server globally.
```bash
cd backend
start_backend.bat
```

**3. Start the Ngrok Tunnel**
Because mobile devices require a secure remote tunnel to the backend, run Ngrok on port 8000:
```bash
ngrok http 8000
```
> **Important:** Copy the `https://...ngrok-free.app` URL it generates. Open the `.env` file located in the root of the project, and paste it so it looks like this:
> `EXPO_PUBLIC_API_URL=https://1234-abcd.ngrok-free.app`

**4. Start the Frontend (Expo)**
Once your `.env` is updated, launch the mobile app:
```bash
cd Arohan
npx expo start
```

*   **Testing Tip:** You can bypass the Twilio SMS setup entirely during development by entering the phone number `9999999999`. The system will automatically log you in with the OTP `123456`.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.
