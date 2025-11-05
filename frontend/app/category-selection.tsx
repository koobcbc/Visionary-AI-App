import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity,
  TouchableWithoutFeedback, Keyboard, Alert, Image, Platform
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { doc, getDoc } from 'firebase/firestore';
import { db } from '../firebaseConfig';
import { getAuth, signOut } from 'firebase/auth';
import AsyncStorage from '@react-native-async-storage/async-storage';
import BottomNavigation from '../components/BottomNavigation';

const logo = require('../assets/images/transparent-logo.png');
const skinImage = require('../assets/images/skin1.png');
const dentalImage = require('../assets/images/dental1.png');

const auth = getAuth();

export default function CategorySelectionScreen() {
  const [menuVisible, setMenuVisible] = useState(false);
  const [userName, setUserName] = useState('');
  const [profileIncomplete, setProfileIncomplete] = useState(false);
  const userInitial = userName ? userName.charAt(0).toUpperCase() : '?';

  const fetchUserName = async () => {
    const user = auth.currentUser;
    if (!user) {
      router.replace('/');
      return;
    }

    // Try to load from cache first for instant display
    try {
      const cachedName = await AsyncStorage.getItem(`userName_${user.uid}`);
      if (cachedName) {
        setUserName(cachedName);
      }
    } catch (error) {
      console.log('Error loading cached user name:', error);
    }

    // Then fetch fresh data from Firestore
    try {
      const docRef = doc(db, "users", user.uid);
      const docSnap = await getDoc(docRef);
      if (docSnap.exists()) {
        const data = docSnap.data();
        const firstName = data.firstName || '';
        setUserName(firstName);
        setProfileIncomplete(data.profileCreated !== true);
        
        // Cache the user name for next time
        try {
          await AsyncStorage.setItem(`userName_${user.uid}`, firstName);
        } catch (error) {
          console.log('Error caching user name:', error);
        }
      }
    } catch (error) {
      console.log('Error fetching user name:', error);
    }
  };

  useEffect(() => {
    fetchUserName();
  }, []);

  const handleLogout = async () => {
    try {
      const user = auth.currentUser;
      if (user) {
        // Clear cached user name on logout
        await AsyncStorage.removeItem(`userName_${user.uid}`);
      }
      await signOut(auth);
      await new Promise(res => setTimeout(res, 500));
      router.replace('/');
    } catch (error) {
      Alert.alert("Logout Failed", "An error occurred while logging out.");
    }
  };

  const handleCategorySelect = (category: 'skin' | 'dental') => {
    router.push(`/dashboard?category=${category}`);
  };

  return (
    <TouchableWithoutFeedback onPress={() => { setMenuVisible(false); Keyboard.dismiss(); }}>
      <View style={styles.container}>
        <View style={styles.header}>
          <Image source={logo} style={styles.logo} resizeMode="contain" />
          <View style={styles.headerSpacer} />
          <View>
            <TouchableOpacity style={styles.avatar} onPress={() => setMenuVisible(!menuVisible)}>
              <Text style={styles.avatarText}>{userInitial}</Text>
              {profileIncomplete && (
                <View style={styles.incompleteIndicator}>
                  <Ionicons name="warning" size={12} color="#e74c3c" />
                </View>
              )}
            </TouchableOpacity>
            {menuVisible && (
              <View style={styles.menu}>
                {profileIncomplete && (
                  <TouchableOpacity onPress={() => { setMenuVisible(false); router.push('/profile-creation'); }}>
                    <Text style={[styles.menuItem, styles.incompleteMenuItem]}>Complete Profile</Text>
                  </TouchableOpacity>
                )}
                <TouchableOpacity onPress={() => { setMenuVisible(false); router.push('/account'); }}>
                  <Text style={styles.menuItem}>Account</Text>
                </TouchableOpacity>
                <TouchableOpacity onPress={() => { setMenuVisible(false); router.push('/settings'); }}>
                  <Text style={styles.menuItem}>Settings</Text>
                </TouchableOpacity>
                <TouchableOpacity onPress={handleLogout}>
                  <Text style={styles.menuItem}>Logout</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        </View>

        <View style={styles.content}>
          <Text style={styles.title}>Choose Your Consultation Type</Text>
          <Text style={styles.subtitle}>Select the type of medical consultation you need</Text>

          <View style={styles.cardContainer}>
            <TouchableOpacity
              style={styles.categoryCard}
              onPress={() => handleCategorySelect('skin')}
              activeOpacity={0.9}
            >
              <View style={styles.cardImageSection}>
                <Image 
                  source={skinImage} 
                  style={styles.cardImage} 
                  resizeMode="cover"
                />
                <View style={styles.cardGradientOverlay} />
              </View>
              <View style={styles.cardContent}>
                <Text style={styles.categoryCardTitle}>Skin</Text>
              </View>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.categoryCard}
              onPress={() => handleCategorySelect('dental')}
              activeOpacity={0.9}
            >
              <View style={styles.cardImageSection}>
                <Image 
                  source={dentalImage} 
                  style={styles.cardImage} 
                  resizeMode="cover"
                />
                <View style={styles.cardGradientOverlay} />
              </View>
              <View style={styles.cardContent}>
                <Text style={styles.categoryCardTitle}>Dental</Text>
              </View>
            </TouchableOpacity>
          </View>
        </View>

        <BottomNavigation activeTab="chat" />
      </View>
    </TouchableWithoutFeedback>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f0f7ff',
    paddingHorizontal: 20,
    paddingBottom: 80,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 20,
    paddingTop: 20,
    zIndex: 1000,
    position: 'relative',
  },
  logo: {
    width: 140,
    height: 60,
  },
  avatar: {
    backgroundColor: '#4a90e2',
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  avatarText: {
    fontWeight: '700',
    color: '#fff',
    fontSize: Platform.select({
      ios: 18,
      default: 20,
    }),
  },
  incompleteIndicator: {
    position: 'absolute',
    top: -2,
    right: -2,
    backgroundColor: '#fff',
    borderRadius: 8,
    width: 16,
    height: 16,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#e74c3c',
  },
  menu: {
    backgroundColor: '#ffffff',
    borderRadius: 8,
    paddingVertical: 8,
    paddingHorizontal: 10,
    position: 'absolute',
    top: 48,
    left: 0,
    width: 180,
    zIndex: 9999,
    elevation: 16,
    shadowColor: '#000',
    shadowOpacity: 0.12,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 6 },
    borderWidth: 1,
    borderColor: '#e2e6ea',
  },
  menuItem: {
    paddingVertical: 8,
    fontSize: Platform.select({
      ios: 16,
      default: 18,
    }),
    color: '#333',
  },
  incompleteMenuItem: {
    color: '#e74c3c',
    fontWeight: 'bold',
  },
  headerSpacer: {
    flex: 1,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 40,
  },
  title: {
    fontSize: Platform.select({
      ios: 24,
      default: 28,
    }),
    fontWeight: '700',
    color: '#2c3e50',
    marginBottom: 12,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: Platform.select({
      ios: 14,
      default: 16,
    }),
    color: '#7f8c8d',
    marginBottom: 48,
    textAlign: 'center',
    paddingHorizontal: 20,
  },
  cardContainer: {
    width: '100%',
    maxWidth: 400,
    gap: 20,
  },
  categoryCard: {
    width: '100%',
    borderRadius: 20,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOpacity: 0.2,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 6 },
    elevation: 8,
    borderWidth: 2,
    borderColor: '#ffffff',
  },
  cardImageSection: {
    width: '100%',
    height: 220,
    position: 'relative',
    backgroundColor: '#f8f9fa',
    alignItems: 'center',
    justifyContent: 'center',
    borderTopLeftRadius: 18,
    borderTopRightRadius: 18,
    overflow: 'hidden',
  },
  cardImage: {
    width: '100%',
    height: '100%',
  },
  cardGradientOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.15)',
  },
  cardContent: {
    padding: 24,
    paddingBottom: 20,
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
    borderBottomLeftRadius: 18,
    borderBottomRightRadius: 18,
  },
  categoryCardTitle: {
    color: '#fff',
    fontSize: Platform.select({
      ios: 28,
      default: 32,
    }),
    fontWeight: '700',
    letterSpacing: 0.5,
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 6,
  },
});

