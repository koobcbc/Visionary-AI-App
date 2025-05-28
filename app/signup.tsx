// --- SignupScreen.tsx ---
import React, { useState } from 'react';
import {
  View, TextInput, Text, StyleSheet, TouchableOpacity, Alert, KeyboardAvoidingView, Platform, ScrollView, TouchableWithoutFeedback, Keyboard, Image
} from 'react-native';
import { createUserWithEmailAndPassword } from 'firebase/auth';
import { auth, db } from '../firebaseConfig';
import { doc, setDoc } from 'firebase/firestore';
import { useRouter } from 'expo-router';
import logo from '../assets/images/dermascan_logo_transparent.png';
import { Ionicons } from '@expo/vector-icons';

export default function SignupScreen() {
  const [email, setEmail] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();

  const handleSignup = async () => {
    setError('');
    if (password !== confirmPassword) {
      Alert.alert('Error', 'Passwords do not match.', [{ text: 'OK', style: 'destructive' }]);
      return;
    }
    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      const user = userCredential.user;
      await new Promise(res => setTimeout(res, 500));
      await setDoc(doc(db, 'users', user.uid), {
        firstName, lastName, email, phoneNumber, createdAt: new Date()
      });
      Alert.alert('Success', 'Account created! Please log in.', [{ text: 'OK' }]);
      router.push('/login');
    } catch (err: any) {
      Alert.alert('Signup Failed', err.message, [{ text: 'OK', style: 'destructive' }]);
    }
  };

  return (
    <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
      <ScrollView contentContainerStyle={styles.scrollContainer} keyboardShouldPersistTaps="handled">
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.keyboardView}>
          <View style={[styles.container, styles.signupContainer]}>
            {/* Back Button */}
            <TouchableOpacity style={styles.backButton} onPress={() => router.push('/')}>
              <Ionicons name="arrow-back" size={24} color="#2c3e50" />
            </TouchableOpacity>
            <Image source={logo} style={styles.logo} resizeMode="contain" />
            <TextInput placeholder="First Name" placeholderTextColor="#666" style={styles.input} onChangeText={setFirstName} value={firstName} />
            <TextInput placeholder="Last Name" placeholderTextColor="#666" style={styles.input} onChangeText={setLastName} value={lastName} />
            <TextInput placeholder="Phone Number" placeholderTextColor="#666" style={styles.input} onChangeText={setPhoneNumber} value={phoneNumber} keyboardType="phone-pad" />
            <TextInput placeholder="Email" placeholderTextColor="#666" style={styles.input} onChangeText={setEmail} value={email} autoCapitalize="none" keyboardType="email-address" />
            <TextInput placeholder="Password" placeholderTextColor="#666" secureTextEntry style={styles.input} onChangeText={setPassword} value={password} />
            <TextInput placeholder="Confirm Password" placeholderTextColor="#666" secureTextEntry style={styles.input} onChangeText={setConfirmPassword} value={confirmPassword} />
            <TouchableOpacity style={styles.authButton} onPress={handleSignup}>
              <Text style={styles.authButtonText}>SIGN UP</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={() => router.push('/login')}>
              <Text style={styles.toggleText}>Already have an account? Log in</Text>
            </TouchableOpacity>
            {error ? <Text style={styles.error}>{error}</Text> : null}
          </View>
        </KeyboardAvoidingView>
      </ScrollView>
    </TouchableWithoutFeedback>
  );
}

const styles = StyleSheet.create({
  logo: {
    width: 120,
    height: 120,
    marginBottom: 20,
    borderRadius: 10,
  },
  scrollContainer: {
    flexGrow: 1,
    justifyContent: 'center',
  },
  keyboardView: {
    flex: 1,
  },
  container: {
    paddingHorizontal: 16,
    paddingVertical: 30,
    alignItems: 'center',
    width: '100%',
  },
  signupContainer: {
    padding: 20,
  },
  input: {
    width: '100%',
    height: 42,
    borderColor: '#ddd',
    borderWidth: 1,
    borderRadius: 12,
    marginBottom: 14,
    paddingHorizontal: 14,
    backgroundColor: '#f9f9f9',
    color: '#000',
  },
  authButton: {
    width: '100%',
    height: 48,
    backgroundColor: '#2c3e50',
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  authButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
  toggleText: {
    color: '#2c3e50',
    fontSize: 14,
    marginTop: 8,
  },
  error: {
    color: 'red',
    marginTop: 10,
    textAlign: 'center',
  },
  backButton: {
    position: 'absolute',
    top: 10,
    left: 10,
    zIndex: 10,
  },
});