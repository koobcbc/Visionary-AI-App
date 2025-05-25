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
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.keyboardView}>
          <View style={styles.container}>
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
            <Button title={mode === 'login' ? 'Login' : 'Sign Up'} onPress={handleAuth} />
            <Text style={styles.toggle} onPress={toggleMode}>
              {mode === 'login' ? "Don't have an account? Sign up" : "Already have an account? Log in"}
            </Text>
            {error ? <Text style={styles.error}>{error}</Text> : null}
          </View>
        </KeyboardAvoidingView>
      </ScrollView>
    </TouchableWithoutFeedback>
  );
}

const styles = StyleSheet.create({
  scrollContainer: { flexGrow: 1, justifyContent: 'center' },
  keyboardView: { flex: 1 },
  container: { padding: 20, alignItems: 'center' },
  input: {
    height: 40, width: '90%', borderColor: '#ccc',
    borderWidth: 1, marginBottom: 10,
    paddingHorizontal: 10, borderRadius: 5, color: '#000'
  },
  toggle: { color: 'blue', marginTop: 10, textAlign: 'center' },
  error: { color: 'red', marginTop: 10, textAlign: 'center' }
});