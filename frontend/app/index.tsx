import React from 'react';
import {
  View,
  StyleSheet,
  Image,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  TouchableWithoutFeedback,
  Keyboard,
  TouchableOpacity,
  Text
} from 'react-native';
import AuthScreen from '../components/AuthScreen';
import logo from '../assets/images/dermascanAI_logo_cropped.png';
import { useRouter } from 'expo-router';
import { StatusBar as ExpoStatusBar } from 'expo-status-bar';

export const unstable_settings = { initialRouteName: "dashboard" };

export default function HomeScreen() {
  
  const router = useRouter();
  
  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={60}
    >
      <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
        <ScrollView
          contentContainerStyle={styles.container}
          keyboardShouldPersistTaps="handled"
        >
          <ExpoStatusBar style="dark" backgroundColor="#ffffff" />
          <View style={styles.logoContainer}>
            <Image source={logo} style={styles.logo} resizeMode="contain" />
          </View>
          <View style={styles.buttonWrapper}>
            <TouchableOpacity
              style={styles.button}
              onPress={() => router.push('/login')}
            >
              <Text style={styles.buttonText}>Log In</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.button, styles.secondaryButton]}
              onPress={() => router.push('/signup')}
            >
              <Text style={[styles.buttonText, styles.secondaryButtonText]}>
                Sign Up
              </Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </TouchableWithoutFeedback>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingVertical: 40,
    paddingTop: 10,
    backgroundColor: '#ffffff',
  },
  logoContainer: {
    marginBottom: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  logo: {
    width: 250,
    height: 250,
    borderRadius: 10
  },
  formWrapper: {
    width: '100%',
    maxWidth: 400,
    padding: 20,
    backgroundColor: '#ffffff',
  },
  buttonWrapper: {
    width: '100%',
    maxWidth: 400,
    alignItems: 'center',
  },
  button: {
    backgroundColor: '#2c3e50',
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 12,
    marginBottom: 20,
    width: '100%',
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  secondaryButton: {
    backgroundColor: '#ffffff',
    borderColor: '#2c3e50',
    borderWidth: 1,
  },
  secondaryButtonText: {
    color: '#2c3e50',
  },
});