import React, { useState } from 'react';
import {
  View,
  TextInput,
  Button,
  Text,
  StyleSheet,
  ScrollView,
  Keyboard,
  Platform,
  KeyboardAvoidingView,
  TouchableWithoutFeedback,
  TouchableOpacity,
  Alert
} from 'react-native';
import { signInWithEmailAndPassword, createUserWithEmailAndPassword } from 'firebase/auth';
import { auth, db } from '../firebaseConfig';
import { useRouter } from 'expo-router';
import { doc, setDoc } from 'firebase/firestore';

export default function AuthScreen() {
  const [email, setEmail] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [error, setError] = useState('');
  const router = useRouter();

  const handleAuth = async () => {
    setError('');

    if (mode === 'signup' && password !== confirmPassword) {
      Alert.alert('Error', 'Passwords do not match.', [{ text: 'OK', style: 'destructive' }]);
      return;
    }

    try {
      if (mode === 'login') {
        await signInWithEmailAndPassword(auth, email, password);
        resetForm();
        router.push('/dashboard');  // redirect on login
      } else {
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        const user = userCredential.user;
        await new Promise(res => setTimeout(res, 1000)); // wait for auth session to stabilize
        console.log("auth", auth)

        // Save user info to Firestore
        await setDoc(doc(db, 'users', user.uid), {
          firstName,
          lastName,
          email,
          phoneNumber,
          createdAt: new Date()
        });

        setMode('login');
        resetForm();
        Alert.alert(
          'Account Created',
          'Your account was successfully created! Please log in.',
          [{ text: 'OK', style: 'default' }]
        );
      }
    } catch (err: any) {
      Alert.alert('Login/Signup Failed', err.message, [{ text: 'OK', style: 'destructive' }]);
    }
  };

  const resetForm = () => {
    setEmail('');
    setPassword('');
    setConfirmPassword('');
    setFirstName('');
    setLastName('');
    setPhoneNumber('');
  };

  const toggleMode = () => {
    setMode(mode === 'login' ? 'signup' : 'login');
    resetForm();
    setError('');
  };

  return (
    <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
      <ScrollView contentContainerStyle={styles.scrollContainer} keyboardShouldPersistTaps="handled">
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={60}
      >
          <View style={[styles.container, mode === 'signup' && styles.signupContainer]}>
            {mode === 'signup' && (
              <>
                <TextInput placeholder="First Name" placeholderTextColor="#666" style={styles.input}
                  onChangeText={setFirstName} value={firstName} />
                <TextInput placeholder="Last Name" placeholderTextColor="#666" style={styles.input}
                  onChangeText={setLastName} value={lastName} />
                <TextInput placeholder="Phone Number" placeholderTextColor="#666" style={styles.input}
                  onChangeText={setPhoneNumber} value={phoneNumber} keyboardType="phone-pad" />
              </>
            )}
            <TextInput placeholder="Email" placeholderTextColor="#666" style={styles.input}
              onChangeText={setEmail} value={email} autoCapitalize="none" keyboardType="email-address" />
            <TextInput placeholder="Password" placeholderTextColor="#666" secureTextEntry style={styles.input}
              onChangeText={setPassword} value={password} />
            {mode === 'signup' && (
              <TextInput placeholder="Confirm Password" placeholderTextColor="#666" secureTextEntry
                style={styles.input} onChangeText={setConfirmPassword} value={confirmPassword} />
            )}
            <TouchableOpacity style={styles.authButton} onPress={handleAuth}>
              <Text style={styles.authButtonText}>{mode === 'login' ? 'SIGN IN' : 'SIGN UP'}</Text>
            </TouchableOpacity>

            <TouchableOpacity onPress={() => setMode(mode === 'login' ? 'signup' : 'login')}>
              <Text style={styles.toggleText}>
                {mode === 'login' ? "Don't have an account? Sign up" : 'Already have an account? Log in'}
              </Text>
            </TouchableOpacity>
            {error ? <Text style={styles.error}>{error}</Text> : null}
          </View>
        </KeyboardAvoidingView>
      </ScrollView>
    </TouchableWithoutFeedback>
  );
}

const styles = StyleSheet.create({
  scrollContainer: { flexGrow: 1, justifyContent: 'center' },
  container: { padding: 20, alignItems: 'center' },
  signupContainer: { padding: 0, alignItems: 'center' },
  input: {
    width: '100%',
    height: 50,
    borderColor: '#ddd',
    borderWidth: 1,
    borderRadius: 12,
    marginBottom: 16,
    paddingHorizontal: 14,
    backgroundColor: '#f9f9f9',
    color: '#000'
  },
  error: { color: 'red', marginTop: 10, textAlign: 'center' },
  authButton: {
    width: '100%',
    height: 50,
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
});