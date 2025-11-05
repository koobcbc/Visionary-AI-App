// --- SignupScreen.tsx ---
import React, { useState } from 'react';
import {
  View, TextInput, Text, StyleSheet, TouchableOpacity, Alert, KeyboardAvoidingView, Platform, ScrollView, TouchableWithoutFeedback, Keyboard, Image
} from 'react-native';
import { createUserWithEmailAndPassword } from 'firebase/auth';
import { auth, db } from '../firebaseConfig';
import { doc, setDoc } from 'firebase/firestore';
import { useRouter } from 'expo-router';
const logo = require('../assets/images/colored-logo.png');
import { Ionicons } from '@expo/vector-icons';

export default function SignupScreen() {
  const [email, setEmail] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState<{[key: string]: string}>({});
  const router = useRouter();

  const validateEmail = (email: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleSignup = async () => {
    const newErrors: {[key: string]: string} = {};
    
    // Validate required fields
    if (!firstName.trim()) {
      newErrors.firstName = 'First name is required.';
    }
    
    if (!lastName.trim()) {
      newErrors.lastName = 'Last name is required.';
    }
    
    if (!email.trim()) {
      newErrors.email = 'Email is required.';
    } else if (!validateEmail(email)) {
      newErrors.email = 'Please enter a valid email address.';
    }
    
    if (!password) {
      newErrors.password = 'Password is required.';
    } else if (password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters long.';
    }
    
    if (!confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password.';
    } else if (password !== confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match.';
    }
    
    // If there are validation errors, display them and stop
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    // Clear any previous errors
    setErrors({});
    
    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      const user = userCredential.user;
      await new Promise(res => setTimeout(res, 500));
      await setDoc(doc(db, 'users', user.uid), {
        firstName, lastName, email, phoneNumber, createdAt: new Date(),
        profileCreated: false
      });
      Alert.alert('Success', 'Account created! Please log in.', [{ text: 'OK' }]);
      router.push('/login');
    } catch (err: any) {
      // Handle Firebase errors
      let errorMessage = 'An error occurred during signup.';
      if (err.code === 'auth/email-already-in-use') {
        errorMessage = 'This email is already registered.';
      } else if (err.code === 'auth/invalid-email') {
        errorMessage = 'Invalid email address.';
      } else if (err.code === 'auth/weak-password') {
        errorMessage = 'Password is too weak.';
      } else {
        errorMessage = err.message || errorMessage;
      }
      setErrors({ submit: errorMessage });
      Alert.alert('Signup Failed', errorMessage, [{ text: 'OK', style: 'destructive' }]);
    }
  };

  return (
    <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
      <ScrollView contentContainerStyle={styles.scrollContainer} keyboardShouldPersistTaps="handled">
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.keyboardView}>
          <View style={[styles.container, styles.signupContainer]}>
            {/* Back Button */}
            <TouchableOpacity style={styles.backButton} onPress={() => router.push('/')}>
              <Ionicons name="arrow-back" size={24} color="#4a90e2" />
            </TouchableOpacity>
            <Image source={logo} style={styles.logo} resizeMode="contain" />
            
            <View style={styles.inputContainer}>
              <TextInput 
                placeholder="First Name *" 
                placeholderTextColor="#666" 
                style={[styles.input, errors.firstName && styles.inputError]} 
                onChangeText={(text) => {
                  setFirstName(text);
                  if (errors.firstName) {
                    setErrors({...errors, firstName: ''});
                  }
                }} 
                value={firstName} 
              />
              {errors.firstName && <Text style={styles.errorText}>{errors.firstName}</Text>}
            </View>

            <View style={styles.inputContainer}>
              <TextInput 
                placeholder="Last Name *" 
                placeholderTextColor="#666" 
                style={[styles.input, errors.lastName && styles.inputError]} 
                onChangeText={(text) => {
                  setLastName(text);
                  if (errors.lastName) {
                    setErrors({...errors, lastName: ''});
                  }
                }} 
                value={lastName} 
              />
              {errors.lastName && <Text style={styles.errorText}>{errors.lastName}</Text>}
            </View>

            <View style={styles.inputContainer}>
              <TextInput 
                placeholder="Phone Number" 
                placeholderTextColor="#666" 
                style={styles.input} 
                onChangeText={setPhoneNumber} 
                value={phoneNumber} 
                keyboardType="phone-pad" 
              />
            </View>

            <View style={styles.inputContainer}>
              <TextInput 
                placeholder="Email *" 
                placeholderTextColor="#666" 
                style={[styles.input, errors.email && styles.inputError]} 
                onChangeText={(text) => {
                  setEmail(text);
                  if (errors.email) {
                    setErrors({...errors, email: ''});
                  }
                }} 
                value={email} 
                autoCapitalize="none" 
                keyboardType="email-address" 
              />
              {errors.email && <Text style={styles.errorText}>{errors.email}</Text>}
            </View>

            <View style={styles.inputContainer}>
              <TextInput 
                placeholder="Password *" 
                placeholderTextColor="#666" 
                secureTextEntry 
                style={[styles.input, errors.password && styles.inputError]} 
                onChangeText={(text) => {
                  setPassword(text);
                  if (errors.password) {
                    setErrors({...errors, password: ''});
                  }
                }} 
                value={password} 
              />
              {errors.password && <Text style={styles.errorText}>{errors.password}</Text>}
            </View>

            <View style={styles.inputContainer}>
              <TextInput 
                placeholder="Confirm Password *" 
                placeholderTextColor="#666" 
                secureTextEntry 
                style={[styles.input, errors.confirmPassword && styles.inputError]} 
                onChangeText={(text) => {
                  setConfirmPassword(text);
                  if (errors.confirmPassword) {
                    setErrors({...errors, confirmPassword: ''});
                  }
                }} 
                value={confirmPassword} 
              />
              {errors.confirmPassword && <Text style={styles.errorText}>{errors.confirmPassword}</Text>}
            </View>

            {errors.submit && <Text style={styles.errorText}>{errors.submit}</Text>}

            <TouchableOpacity style={styles.authButton} onPress={handleSignup}>
              <Text style={styles.authButtonText}>SIGN UP</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={() => router.push('/login')}>
              <Text style={styles.toggleText}>Already have an account? Log in</Text>
            </TouchableOpacity>
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
    backgroundColor: '#DBEDEC',
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
  inputContainer: {
    width: '100%',
    marginBottom: 4,
  },
  input: {
    width: '100%',
    height: 42,
    borderColor: '#ddd',
    borderWidth: 1,
    borderRadius: 12,
    marginBottom: 4,
    paddingHorizontal: 14,
    backgroundColor: '#f9f9f9',
    color: '#000',
  },
  inputError: {
    borderColor: '#e74c3c',
    borderWidth: 1.5,
  },
  authButton: {
    width: '100%',
    height: 48,
    backgroundColor: '#4a90e2',
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
    color: '#4a90e2',
    fontSize: 14,
    marginTop: 8,
  },
  errorText: {
    color: '#e74c3c',
    fontSize: 12,
    marginTop: 2,
    marginBottom: 8,
    marginLeft: 4,
  },
  backButton: {
    position: 'absolute',
    top: 10,
    left: 10,
    zIndex: 10,
  },
});