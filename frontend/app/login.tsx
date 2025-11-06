// --- LoginScreen.tsx ---
import React, { useState } from 'react';
import {
  View, TextInput, Text, StyleSheet, TouchableOpacity, Alert, KeyboardAvoidingView, Platform, ScrollView, TouchableWithoutFeedback, Keyboard, Image
} from 'react-native';
import { signInWithEmailAndPassword } from 'firebase/auth';
import { auth } from '../firebaseConfig';
import { useRouter } from 'expo-router';
import { signInWithGoogle, signInWithApple } from '../utils/authHelpers';
const logo = require('../assets/images/colored-logo.png');
import { Ionicons } from '@expo/vector-icons';

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();

  const handleLogin = async () => {
    setError('');
    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      const user = userCredential.user;
      
      // Navigate to user dashboard for all authenticated users
      router.push('/user-dashboard');
    } catch (err: any) {
      Alert.alert('Login Failed', err.message, [{ text: 'OK', style: 'destructive' }]);
    }
  };

  const handleGoogleSignIn = async () => {
    try {
      setError('');
      const result = await signInWithGoogle();
      // Navigate to user dashboard
      router.push('/user-dashboard');
    } catch (error: any) {
      // Handle cancellation silently - no error shown
      if (error.isCancellation || error.message === 'SIGN_IN_CANCELLED') {
        return; // User cancelled, silently return
      }
      
      const errorMessage = error.message || 'Google sign-in failed. Please try again.';
      
      // For configuration errors, only show alert (not persistent error)
      if (errorMessage.includes('not configured') || errorMessage.includes('Client ID')) {
        Alert.alert(
          'Configuration Required',
          'Google Sign-In is not configured yet. Please set up EXPO_PUBLIC_GOOGLE_CLIENT_ID in your environment variables.\n\n1. Create a .env file in the frontend directory\n2. Add: EXPO_PUBLIC_GOOGLE_CLIENT_ID=your-client-id\n3. Restart your development server',
          [{ text: 'OK' }]
        );
      } else {
        // For other errors, show both alert and persistent message
        setError(errorMessage);
        Alert.alert('Sign-In Failed', errorMessage);
      }
    }
  };

  const handleAppleSignIn = async () => {
    try {
      if (Platform.OS !== 'ios') {
        Alert.alert('Not Available', 'Apple Sign-In is only available on iOS.');
        return;
      }
      setError('');
      const result = await signInWithApple();
      // Navigate to user dashboard
      router.push('/user-dashboard');
    } catch (error: any) {
      // Handle cancellation silently - no error shown
      if (error.isCancellation || error.message === 'SIGN_IN_CANCELLED') {
        return; // User cancelled, silently return
      }
      
      const errorMessage = error.message || 'Apple sign-in failed. Please try again.';
      setError(errorMessage);
      Alert.alert('Sign-In Failed', errorMessage);
    }
  };


  return (
    <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
      <ScrollView contentContainerStyle={styles.scrollContainer} keyboardShouldPersistTaps="handled">
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.keyboardView}>
          <View style={styles.container}>
            {/* Back Button */}
            <TouchableOpacity style={styles.backButton} onPress={() => router.push('/')}>
              <Ionicons name="arrow-back" size={24} color="#4a90e2" />
            </TouchableOpacity>
            <Image source={logo} style={styles.logo} resizeMode="contain" />
            <TextInput placeholder="Email" style={styles.input} placeholderTextColor="#666" value={email} onChangeText={setEmail} autoCapitalize="none" keyboardType="email-address" />
            <TextInput placeholder="Password" style={styles.input} placeholderTextColor="#666" secureTextEntry value={password} onChangeText={setPassword} />
            <TouchableOpacity style={styles.authButton} onPress={handleLogin}>
              <Text style={styles.authButtonText}>SIGN IN</Text>
            </TouchableOpacity>
            
            <View style={styles.dividerContainer}>
              <View style={styles.dividerLine} />
              <Text style={styles.dividerText}>OR</Text>
              <View style={styles.dividerLine} />
            </View>

            <View style={styles.socialButtonsContainer}>
              <TouchableOpacity style={styles.socialButton} onPress={handleGoogleSignIn}>
                <Ionicons name="logo-google" size={24} color="#4285F4" />
              </TouchableOpacity>
              {Platform.OS === 'ios' && (
                <TouchableOpacity style={styles.socialButton} onPress={handleAppleSignIn}>
                  <Ionicons name="logo-apple" size={24} color="#000000" />
                </TouchableOpacity>
              )}
            </View>

            <TouchableOpacity onPress={() => router.push('/signup')}>
              <Text style={styles.toggleText}>Don't have an account? Sign up</Text>
            </TouchableOpacity>
            {error ? <Text style={styles.error}>{error}</Text> : null}
          </View>
        </KeyboardAvoidingView>
      </ScrollView>
    </TouchableWithoutFeedback>
  );
}

const styles = StyleSheet.create({
  scrollContainer: { flexGrow: 1, justifyContent: 'center', backgroundColor: '#DBEDEC' },
  logo: {
    width: 120,
    height: 120,
    marginBottom: 20,
    borderRadius: 10,
  },
  keyboardView: { flex: 1 },
  container: { padding: 20, alignItems: 'center' },
  input: {
    width: '100%', height: 50, borderColor: '#ddd', borderWidth: 1,
    borderRadius: 12, marginBottom: 16, paddingHorizontal: 14,
    backgroundColor: '#f9f9f9', color: '#000'
  },
  authButton: {
    width: '100%', height: 50, backgroundColor: '#A5CCC9',
    borderRadius: 12, justifyContent: 'center', alignItems: 'center',
    marginBottom: 12
  },
  authButtonText: { color: '#111', fontWeight: 'bold', fontSize: 16 },
  toggleText: { color: '#2c3e50', fontSize: 14, marginTop: 8 },
  error: { color: 'red', marginTop: 10, textAlign: 'center' },
  backButton: {
    position: 'absolute',
    top: 10,
    left: 10,
    zIndex: 10,
  },
  dividerContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    width: '100%',
    marginVertical: 20,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#ddd',
  },
  dividerText: {
    marginHorizontal: 12,
    color: '#666',
    fontSize: 14,
  },
  socialButtonsContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 16,
    marginBottom: 16,
  },
  socialButton: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#e0e8f0',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
});
