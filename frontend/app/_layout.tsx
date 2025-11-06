// app/_layout.tsx
import { DefaultTheme, ThemeProvider } from '@react-navigation/native';
import { Stack, usePathname } from 'expo-router';
import { useEffect } from 'react';
import * as SplashScreen from 'expo-splash-screen';
import { StatusBar as ExpoStatusBar } from 'expo-status-bar';
import { SafeAreaView, View, Platform, StatusBar as RNStatusBar } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { useFonts } from 'expo-font';
import { setupErrorFilter } from '../utils/logger';
import {
  NotoSans_100Thin,
  NotoSans_200ExtraLight,
  NotoSans_300Light,
  NotoSans_400Regular,
  NotoSans_500Medium,
  NotoSans_600SemiBold,
  NotoSans_700Bold,
  NotoSans_800ExtraBold,
  NotoSans_900Black,
  NotoSans_100Thin_Italic,
  NotoSans_200ExtraLight_Italic,
  NotoSans_300Light_Italic,
  NotoSans_400Regular_Italic,
  NotoSans_500Medium_Italic,
  NotoSans_600SemiBold_Italic,
  NotoSans_700Bold_Italic,
  NotoSans_800ExtraBold_Italic,
  NotoSans_900Black_Italic,
} from '@expo-google-fonts/noto-sans';

SplashScreen.preventAutoHideAsync();

// Setup error filtering on app start
setupErrorFilter();

export default function RootLayout() {
  const pathname = usePathname();
  const [fontsLoaded, fontError] = useFonts({
    NotoSans_100Thin,
    NotoSans_200ExtraLight,
    NotoSans_300Light,
    NotoSans_400Regular,
    NotoSans_500Medium,
    NotoSans_600SemiBold,
    NotoSans_700Bold,
    NotoSans_800ExtraBold,
    NotoSans_900Black,
    NotoSans_100Thin_Italic,
    NotoSans_200ExtraLight_Italic,
    NotoSans_300Light_Italic,
    NotoSans_400Regular_Italic,
    NotoSans_500Medium_Italic,
    NotoSans_600SemiBold_Italic,
    NotoSans_700Bold_Italic,
    NotoSans_800ExtraBold_Italic,
    NotoSans_900Black_Italic,
  });

  useEffect(() => {
    if (fontsLoaded || fontError) {
      SplashScreen.hideAsync();
    }
  }, [fontsLoaded, fontError]);

  return (
    <SafeAreaProvider>
      <ThemeProvider value={DefaultTheme}>
        <View style={{ flex: 1 }}>
          {/* Top SafeArea (light theme) */}
          <SafeAreaView style={{ 
            backgroundColor: pathname?.includes('/chat/') ? '#f9fafe' : '#DBEDEC' 
          }}>
            {Platform.OS === 'android' && (
              <RNStatusBar backgroundColor="#4a90e2" barStyle="light-content" />
            )}
          </SafeAreaView>

          {/* Main App Stack */}
          <View style={{ flex: 1, backgroundColor: '#DBEDEC' }}>
            <Stack screenOptions={{ headerShown: false }}>
              <Stack.Screen name="(tabs)" />
              <Stack.Screen name="+not-found" />
              <Stack.Screen name="login" />
              <Stack.Screen name="signup" />
              <Stack.Screen name="profile-creation" />
              <Stack.Screen name="category-selection" options={{ animation: 'none', gestureEnabled: false }} />
              <Stack.Screen name="user-dashboard" options={{ animation: 'none', gestureEnabled: false }} />
              <Stack.Screen name="dashboard" />
              <Stack.Screen name="chat/[chatId]" options={{ animation: 'slide_from_right' }} />
            </Stack>
          </View>

          {/* Bottom SafeArea */}
          <SafeAreaView style={{ 
            backgroundColor: pathname === '/login' || pathname === '/signup' ? '#DBEDEC' : '#ffffff' 
          }} />
        </View>

        <ExpoStatusBar style="dark" />
      </ThemeProvider>
    </SafeAreaProvider>
  );
}