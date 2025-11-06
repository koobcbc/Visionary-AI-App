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
const logo = require('../assets/images/colored-logo.png');
import { useRouter } from 'expo-router';
import { StatusBar as ExpoStatusBar } from 'expo-status-bar';
import WaveBackground from '../components/WaveBackground';

export const unstable_settings = { initialRouteName: "dashboard" };

export default function HomeScreen() {
  
  const router = useRouter();
  
  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={60}
    >
      <View style={styles.wrapper}>
        <WaveBackground 
          topColor="#DBEDEC"
          bottomColor="#FFFFFF"
          wavePosition={0.35}
        />
        <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
          <View style={styles.contentWrapper}>
            <ExpoStatusBar style="dark" backgroundColor="#FFFFFF" />
            {/* Logo in top section (above wave) */}
            <View style={styles.topSection}>
              <View style={styles.logoContainer}>
                <Image source={logo} style={styles.logo} resizeMode="contain" />
              </View>
            </View>
            
            {/* Buttons in white section (below wave) */}
            <ScrollView
              contentContainerStyle={styles.whiteSection}
              keyboardShouldPersistTaps="handled"
              style={styles.scrollView}
            >
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
          </View>
        </TouchableWithoutFeedback>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    flex: 1,
  },
  contentWrapper: {
    flex: 1,
    zIndex: 1,
  },
  topSection: {
    height: '35%', // Matches wavePosition 0.35
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 60,
  },
  scrollView: {
    flex: 1,
  },
  whiteSection: {
    flexGrow: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingVertical: 30,
    paddingTop: 60,
  },
  logoContainer: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  logo: {
    width: 220,
    height: 220,
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
    backgroundColor: '#B8D8D6',
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 12,
    marginBottom: 20,
    width: '100%',
    alignItems: 'center',
  },
  buttonText: {
    color: '#2c3e50',
    fontSize: 16,
    fontWeight: 'bold',
  },
  secondaryButton: {
    backgroundColor: '#ffffff',
    borderColor: '#DBEDEC',
    borderWidth: 2,
  },
  secondaryButtonText: {
    color: '#2c3e50',
  },
});