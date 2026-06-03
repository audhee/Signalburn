import { Stack } from 'expo-router';
import './i18n';

export default function RootLayout() {
  return (
    <Stack initialRouteName="index" screenOptions={{ headerShown: false }}>
      <Stack.Screen name="index" />
      <Stack.Screen
        name="language"
        options={{
          presentation: 'modal',
          gestureEnabled: false,
        }}
      />
      <Stack.Screen name="otp" />
      <Stack.Screen name="setup/profile" />
      <Stack.Screen name="setup/contacts" />
      <Stack.Screen name="home/index" />
      <Stack.Screen name="emergency/assist" />
      <Stack.Screen name="emergency/ai-guidance" />
      <Stack.Screen name="emergency/location" />
      <Stack.Screen name="emergency/chatbox" />
      <Stack.Screen name="emergency/safe" />
      <Stack.Screen name="settings/index" />
      <Stack.Screen name="stats/index" />
    </Stack>
  );
}
