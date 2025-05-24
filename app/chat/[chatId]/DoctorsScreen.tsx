import React, { useEffect, useState } from 'react';
import {
  View, Text, FlatList, StyleSheet, ActivityIndicator,
  TouchableOpacity, Linking, Alert, TextInput, Button
} from 'react-native';
import * as Location from 'expo-location';


type Doctor = {
  name: string;
  specialty: string;
  address: string;
  mapQuery: string;
};

const SPECIALTY = 'Ophthalmology';
const STATE = 'IL';

export default function DoctorsScreen() {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [location, setLocation] = useState<Location.LocationObject | null>(null);
  const [zipInput, setZipInput] = useState('');
  const [locationPermissionDenied, setLocationPermissionDenied] = useState(false);

  const requestLocation = async () => {
    setLoading(true);
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        setLocationPermissionDenied(true);
        setLoading(false);
        return;
      }

      const loc = await Location.getCurrentPositionAsync({});
      setLocation(loc);
      fetchDoctors(loc.coords.latitude, loc.coords.longitude);
    } catch (err: any) {
      setError("Unable to fetch location.");
      setLoading(false);
    }
  };

  const formatZipCode = (address: string) => {
    // Match and format 9-digit ZIP code (e.g., 123456789 -> 12345-6789)
    return address.replace(/(\D|^)(\d{5})(\d{4})(\D|$)/, '$1$2-$3$4');
  };

  const fetchDoctors = async (lat?: number, lon?: number, zip?: string) => {
    setLoading(true);
    try {
      let url = `https://npiregistry.cms.hhs.gov/api/?version=2.1&taxonomy_description=${encodeURIComponent(SPECIALTY)}&limit=20`;

      if (zip) {
        url += `&postal_code=${zip}`;
      } else if (lat && lon) {
        // NPI registry doesn't support lat/lon directly, you'd need reverse geocoding to get zip/state
        const geo = await Location.reverseGeocodeAsync({ latitude: lat, longitude: lon });
        if (geo[0]?.postalCode) {
          url += `&postal_code=${geo[0].postalCode}`;
        } else {
          throw new Error("Failed to determine postal code.");
        }
      } else {
        url += `&state=${STATE}`;
      }

      const res = await fetch(url);
      const json = await res.json();

      if (!json.results) throw new Error('No results found');

      const parsed: Doctor[] = json.results.map((doc: any) => {
        const basic = doc.basic || {};
        const address = doc.addresses?.[0] || {};
        const name = `${basic.first_name || ''} ${basic.last_name || ''}`.trim();
        const specialty = doc.taxonomies?.[0]?.desc || 'N/A';
        const fullAddress = `${address.address_1 || ''} ${address.city || ''}, ${address.state || ''} ${formatZipCode(address.postal_code) || ''}`;
        const mapQuery = `${address.address_1 || ''}, ${address.city || ''}, ${address.state || ''}`;

        return {
          name: name || doc.basic.organization_name || 'Unknown',
          specialty,
          address: fullAddress,
          mapQuery
        };
      });

      setDoctors(parsed);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch doctors');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    requestLocation();
  }, []);

  const handleZipSearch = () => {
    if (zipInput.trim()) {
      fetchDoctors(undefined, undefined, zipInput.trim());
    }
  };


  const openInMaps = (query: string) => {
    const url = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`;
    Linking.openURL(url).catch(() => Alert.alert('Error', 'Failed to open Maps'));
  };

  useEffect(() => {
    fetchDoctors();
  }, []);

  if (loading) {
    return <ActivityIndicator size="large" style={{ marginTop: 50 }} />;
  }

  if (error) {
    return (
      <View style={styles.errorContainer}>
        <Text style={{ color: 'red', fontSize: 16 }}>{error}</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.subTitle}>Specialty: {SPECIALTY}</Text>

      {locationPermissionDenied && (
        <View style={{ marginBottom: 20 }}>
          <Text style={{ textAlign: 'center', color: 'red' }}>Location permission denied.</Text>
          <Text style={{ textAlign: 'center' }}>Enter your ZIP code below to search manually:</Text>
          <TextInput
            placeholder="Enter ZIP code"
            value={zipInput}
            onChangeText={setZipInput}
            keyboardType="numeric"
            style={{
              borderWidth: 1, padding: 8, marginTop: 10, borderRadius: 6,
              borderColor: '#ccc', textAlign: 'center'
            }}
          />
          <Button title="Search by ZIP" onPress={handleZipSearch} />
        </View>
      )}

      {loading ? (
        <ActivityIndicator size="large" style={{ marginTop: 50 }} />
      ) : error ? (
        <View style={styles.errorContainer}>
          <Text style={{ color: 'red', fontSize: 16 }}>{error}</Text>
        </View>
      ) : (
        <FlatList
          data={doctors}
          keyExtractor={(item, idx) => `${item.name}-${idx}`}
          renderItem={({ item }) => (
            <TouchableOpacity style={styles.card} onPress={() => openInMaps(item.mapQuery)}>
              <View style={{ flex: 1 }}>
                <Text style={styles.name}>{item.name}</Text>
                <Text style={styles.specialty}>{item.specialty}</Text>
                <Text style={styles.address}>{item.address}</Text>
              </View>
            </TouchableOpacity>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff', padding: 20 },
  title: { fontSize: 20, fontWeight: '700', marginBottom: 10, alignSelf: 'center' },
  subTitle: { fontSize: 16, fontWeight: '500', marginBottom: 16, textAlign: 'center' },
  card: {
    backgroundColor: '#e6f0fa',
    padding: 12,
    marginBottom: 12,
    borderRadius: 8
  },
  name: { fontSize: 16, fontWeight: 'bold' },
  specialty: { fontSize: 14, color: '#333' },
  address: { fontSize: 13, color: '#555' },
  errorContainer: {
    flex: 1, alignItems: 'center', justifyContent: 'center'
  }
});