// --- LoginScreen.tsx ---
import React, { useState } from 'react';
import {
  View, TextInput, Text, StyleSheet, TouchableOpacity, Alert, KeyboardAvoidingView, Platform, ScrollView, TouchableWithoutFeedback, Keyboard, Image
} from 'react-native';
import { signInWithEmailAndPassword } from 'firebase/auth';
import { auth, db } from '../firebaseConfig';
import { useRouter } from 'expo-router';
import { doc, getDoc } from 'firebase/firestore';
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
    width: '100%', height: 50, backgroundColor: '#4a90e2',
    borderRadius: 12, justifyContent: 'center', alignItems: 'center',
    marginBottom: 12
  },
  authButtonText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
  toggleText: { color: '#4a90e2', fontSize: 14, marginTop: 8 },
  error: { color: 'red', marginTop: 10, textAlign: 'center' },
  backButton: {
    position: 'absolute',
    top: 10,
    left: 10,
    zIndex: 10,
  },
});
