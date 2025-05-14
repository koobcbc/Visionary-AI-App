import React, { useState } from 'react';
import {
  View,
  TextInput,
  Button,
  Text,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  TouchableWithoutFeedback,
  Keyboard,
  ScrollView
} from 'react-native';
import { signInWithEmailAndPassword, createUserWithEmailAndPassword } from 'firebase/auth';
import { auth } from '../firebaseConfig';

export default function AuthScreencopy() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [error, setError] = useState('');

  const handleAuth = async () => {
    setError('');
    if (mode === 'signup' && password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    try {
      if (mode === 'login') {
        await signInWithEmailAndPassword(auth, email, password);
        console.log("Logged in");
      } else {
        await createUserWithEmailAndPassword(auth, email, password);
        setMode('login');
        setEmail('');
        setPassword('');
        setConfirmPassword('');
        setError("Account created! Please log in.");
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  const toggleMode = () => {
    setMode(mode === 'login' ? 'signup' : 'login');
    setError('');
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      style={{ flex: 1 }}
    >
      <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
        <ScrollView contentContainerStyle={styles.scroll}>
          <View style={styles.container}>
            <TextInput
              placeholder="Email"
              placeholderTextColor="#666"
              style={styles.input}
              onChangeText={setEmail}
              value={email}
              autoCapitalize="none"
              keyboardType="email-address"
            />
            <TextInput
              placeholder="Password"
              placeholderTextColor="#666"
              secureTextEntry
              style={styles.input}
              onChangeText={setPassword}
              value={password}
            />
            {mode === 'signup' && (
              <TextInput
                placeholder="Confirm Password"
                placeholderTextColor="#666"
                secureTextEntry
                style={styles.input}
                onChangeText={setConfirmPassword}
                value={confirmPassword}
              />
            )}
            <Button title={mode === 'login' ? 'Login' : 'Sign Up'} onPress={handleAuth} />
            <Text style={styles.toggle} onPress={toggleMode}>
              {mode === 'login' ? "Don't have an account? Sign up" : "Have an account? Log in"}
            </Text>
            {error ? <Text style={styles.error}>{error}</Text> : null}
          </View>
        </ScrollView>
      </TouchableWithoutFeedback>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  scroll: {
    flexGrow: 1,
    justifyContent: 'center',
  },
  container: {
    padding: 20,
    width: '100%',
    alignItems: 'center'
  },
  input: {
    height: 40,
    width: '90%',
    borderColor: '#ccc',
    borderWidth: 1,
    marginBottom: 10,
    paddingHorizontal: 10,
    borderRadius: 5,
    color: '#000'
  },
  toggle: {
    color: 'blue',
    marginTop: 10,
    textAlign: 'center'
  },
  error: {
    color: 'red',
    marginTop: 10,
    textAlign: 'center'
  }
});