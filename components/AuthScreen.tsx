import React, { useState } from 'react';
import { View, TextInput, Button, Text, StyleSheet } from 'react-native';
import { signInWithEmailAndPassword, createUserWithEmailAndPassword } from 'firebase/auth';
import { auth } from '../firebaseConfig';

export default function AuthScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [error, setError] = useState('');

  const handleAuth = async () => {
    try {
      if (mode === 'login') {
        await signInWithEmailAndPassword(auth, email, password);
      } else {
        await createUserWithEmailAndPassword(auth, email, password);
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>{mode === 'login' ? 'Login' : 'Sign Up'}</Text>
      <TextInput placeholder="Email" style={styles.input} onChangeText={setEmail} />
      <TextInput placeholder="Password" secureTextEntry style={styles.input} onChangeText={setPassword} />
      <Button title={mode === 'login' ? 'Login' : 'Sign Up'} onPress={handleAuth} />
      <Text style={styles.toggle} onPress={() => setMode(mode === 'login' ? 'signup' : 'login')}>
        {mode === 'login' ? "Don't have an account? Sign up" : "Have an account? Log in"}
      </Text>
      {error ? <Text style={styles.error}>{error}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 20, marginTop: 80 },
  title: { fontSize: 24, fontWeight: 'bold', marginBottom: 20 },
  input: { height: 40, borderColor: '#ccc', borderWidth: 1, marginBottom: 10, paddingHorizontal: 10 },
  toggle: { color: 'blue', marginTop: 10 },
  error: { color: 'red', marginTop: 10 }
});