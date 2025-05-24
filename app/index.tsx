import React from 'react';
import {
  View,
  StyleSheet,
  Image,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  TouchableWithoutFeedback,
  Keyboard
} from 'react-native';
import AuthScreen from '../components/AuthScreen';
import logo from '../assets/images/logo_cropped_white.jpeg';
import { StatusBar as ExpoStatusBar } from 'expo-status-bar';

export const unstable_settings = { initialRouteName: "dashboard" };

export default function HomeScreen() {
  
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
          <View style={styles.formWrapper}>
            <AuthScreen />
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
    marginBottom: 10,
    borderRadius: 10
  },
  formWrapper: {
    width: '100%',
    maxWidth: 400,
    padding: 20,
    backgroundColor: '#ffffff',
  }
});