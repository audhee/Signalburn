import { Stack } from 'expo-router';
import './i18n';
import React from 'react';
import { View, Text, ScrollView } from 'react-native';

class ErrorBoundary extends React.Component<{children: React.ReactNode}, {error: string | null}> {
  state = { error: null };
  componentDidCatch(error: Error) {
    this.setState({ error: error.message + '\n' + error.stack });
  }
  render() {
    if (this.state.error) {
      return (
        <ScrollView style={{flex:1, backgroundColor:'#000', padding:20, paddingTop:60}}>
          <Text style={{color:'red', fontSize:16, fontWeight:'bold'}}>CRASH REASON:</Text>
          <Text style={{color:'white', fontSize:12, marginTop:10}}>{this.state.error}</Text>
        </ScrollView>
      );
    }
    return this.props.children;
  }
}

export default function RootLayout() {
  return (
    <ErrorBoundary>
      <Stack initialRouteName="index" screenOptions={{ headerShown: false }}>
        <Stack.Screen name="index" />
        <Stack.Screen name="language" options={{ presentation: 'modal', gestureEnabled: false }} />
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
    </ErrorBoundary>
  );
}
