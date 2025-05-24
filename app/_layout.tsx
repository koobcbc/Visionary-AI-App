// app/_layout.tsx
import { DefaultTheme, ThemeProvider } from '@react-navigation/native';
import { Stack } from 'expo-router';
import { useEffect } from 'react';
import * as SplashScreen from 'expo-splash-screen';
import { StatusBar as ExpoStatusBar } from 'expo-status-bar';
import { SafeAreaView, View, Platform, StatusBar as RNStatusBar } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  useEffect(() => {
    SplashScreen.hideAsync();
  }, []);

  return (
    <SafeAreaProvider>
      <ThemeProvider value={DefaultTheme}>
        <View style={{ flex: 1 }}>
          {/* Top SafeArea (light theme) */}
          <SafeAreaView style={{ backgroundColor: '#ffffff' }}>
            {Platform.OS === 'android' && (
              <RNStatusBar backgroundColor="#2c3e50" barStyle="light-content" />
            )}
          </SafeAreaView>

          {/* Main App Stack */}
          <View style={{ flex: 1, backgroundColor: '#ffffff' }}>
            <Stack screenOptions={{ headerShown: false }}>
              <Stack.Screen name="(tabs)" />
              <Stack.Screen name="+not-found" />
              <Stack.Screen name="chat/[chatId]" options={{ animation: 'slide_from_right' }} />
            </Stack>
          </View>

          {/* Bottom SafeArea (light theme) */}
          <SafeAreaView style={{ backgroundColor: '#ffffff' }} />
        </View>

        <ExpoStatusBar style="dark" />
      </ThemeProvider>
    </SafeAreaProvider>
  );
}