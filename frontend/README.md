# DiagnosisAI

A React Native mobile application that provides AI-powered medical assistance and diagnosis support through intelligent chat interfaces and doctor recommendations.

## Features

- **AI-Powered Chat**: Interactive chat interface with Gemini AI for medical consultations
- **Doctor Recommendations**: Find nearby healthcare providers based on location and specialty
- **User Authentication**: Secure signup and login with Firebase Authentication
- **Medical Profile**: Comprehensive health history collection and management
- **Speech-to-Text**: Voice input capabilities for hands-free interaction
- **Real-time Chat**: Live messaging with AI medical assistant
- **Cross-platform**: Runs on both iOS and Android

## Tech Stack

- **Frontend**: React Native with Expo
- **Backend**: Firebase (Authentication, Firestore, Storage)
- **AI**: Google Gemini API
- **Navigation**: Expo Router
- **State Management**: React Hooks
- **Styling**: React Native StyleSheet

## Prerequisites

- Node.js (v16 or higher)
- npm or yarn
- Expo CLI
- iOS Simulator (for iOS development)
- Android Studio (for Android development)

## Installation

1. Clone the repository
   ```bash
   git clone <repository-url>
   cd DiagnosisAI/frontend
   ```

2. Install dependencies
   ```bash
   npm install
   ```

3. Set up environment variables
   ```bash
   cp .env.example .env
   ```
   
   Fill in your Firebase and Gemini API keys in the `.env` file:
   ```
   EXPO_PUBLIC_FIREBASE_API_KEY=your_firebase_api_key
   EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
   EXPO_PUBLIC_FIREBASE_PROJECT_ID=your_project_id
   EXPO_PUBLIC_FIREBASE_STORAGE_BUCKET=your_project.firebasestorage.app
   EXPO_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
   EXPO_PUBLIC_FIREBASE_APP_ID=your_app_id
   GEMINI_API_KEY=your_gemini_api_key
   ```

4. Start the development server
   ```bash
   npx expo start
   ```

## Project Structure

```
frontend/
├── app/                    # Main application screens
│   ├── (tabs)/            # Tab navigation screens
│   ├── chat/              # Chat-related screens
│   └── ...
├── components/            # Reusable UI components
├── assets/               # Images, fonts, and static files
├── utils/                # Utility functions
├── types/                # TypeScript type definitions
└── firebaseConfig.ts     # Firebase configuration
```

## Development

### Running the App

- **iOS Simulator**: Press `i` in the terminal or scan QR code with Expo Go
- **Android Emulator**: Press `a` in the terminal
- **Physical Device**: Install Expo Go and scan the QR code

### Key Features Implementation

- **Authentication**: Firebase Auth with email/password
- **Database**: Firestore for user data and chat history
- **AI Integration**: Google Gemini for medical assistance
- **Profile Management**: Multi-step medical history collection
- **Real-time Updates**: Live chat and data synchronization

## Environment Variables

The application requires the following environment variables:

- `EXPO_PUBLIC_FIREBASE_*`: Firebase configuration
- `GEMINI_API_KEY`: Google Gemini API key for AI features

See `.env.example` for the complete list of required variables.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue in the GitHub repository.
