import { Stack } from 'expo-router';
import './i18n';

export default function RootLayout() {
  return (
    <Stack initialRouteName="index" screenOptions={{ headerShown: false }}>
      <Stack.Screen
        name="language"
        options={{
          presentation: 'modal',
          gestureEnabled: false, // Prevent swiping away on initial load if we want to force choice, but for modal usually we want gesture. Let's keep default gesture but modal presentation.
        }}
      />
      <Stack.Screen name="index" />
      <Stack.Screen name="setup/profile" />
      <Stack.Screen name="home/index" />
      <Stack.Screen name="emergency/assist" />
      <Stack.Screen name="emergency/ai-guidance" />
      <Stack.Screen name="emergency/location" />
      <Stack.Screen name="emergency/chatbox" />
    </Stack>
  );
}
