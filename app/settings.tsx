import React, { useEffect, useState } from 'react';
import { View, Text, Switch, StyleSheet, Alert, TouchableOpacity } from 'react-native';
import * as Location from 'expo-location';
import * as ImagePicker from 'expo-image-picker';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

export default function SettingsScreen() {
  const [locationEnabled, setLocationEnabled] = useState(false);
  const [photoEnabled, setPhotoEnabled] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const loadPreferences = async () => {
      const loc = await AsyncStorage.getItem('enableLocation');
      const photo = await AsyncStorage.getItem('enablePhoto');
      setLocationEnabled(loc === 'true');
      setPhotoEnabled(photo === 'true');
    };
    loadPreferences();
  }, []);

  const toggleLocation = async () => {
    if (!locationEnabled) {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission Denied', 'Location permission is required.');
        return;
      }
    }
    setLocationEnabled(prev => {
      AsyncStorage.setItem('enableLocation', String(!prev));
      return !prev;
    });
  };

  const togglePhoto = async () => {
    if (!photoEnabled) {
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission Denied', 'Photo permission is required.');
        return;
      }
    }
    setPhotoEnabled(prev => {
      AsyncStorage.setItem('enablePhoto', String(!prev));
      return !prev;
    });
  };

  return (
    <View style={styles.container}>
      {/* Back Button */}
      <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
        <Ionicons name="arrow-back" size={24} color="#333" />
      </TouchableOpacity>

      <Text style={styles.title}>App Settings</Text>

      <View style={styles.settingRow}>
        <Text style={styles.label}>Enable Location Sharing</Text>
        <Switch value={locationEnabled} onValueChange={toggleLocation} />
      </View>

      <View style={styles.settingRow}>
        <Text style={styles.label}>Enable Photo Album Sharing</Text>
        <Switch value={photoEnabled} onValueChange={togglePhoto} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: '#fff' },
  backButton: {
    marginBottom: 12,
  },
  title: { fontSize: 22, fontWeight: 'bold', marginBottom: 24 },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginVertical: 16,
  },
  label: { fontSize: 16 },
});