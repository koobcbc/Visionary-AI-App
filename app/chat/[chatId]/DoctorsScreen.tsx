import React, { useEffect, useState } from 'react';
import {
  View, Text, FlatList, StyleSheet, ActivityIndicator,
  TouchableOpacity, Linking, Alert
} from 'react-native';

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

  const fetchDoctors = async () => {
    try {
      const res = await fetch(
        `https://npiregistry.cms.hhs.gov/api/?version=2.1&state=${STATE}&taxonomy_description=${encodeURIComponent(
          SPECIALTY
        )}&limit=20`
      );
      const json = await res.json();

      if (!json.results) throw new Error('No results found');

      const parsed: Doctor[] = json.results.map((doc: any) => {
        const basic = doc.basic || {};
        const address = doc.addresses?.[0] || {};
        const name = `${basic.first_name || ''} ${basic.last_name || ''}`.trim();
        const specialty = doc.taxonomies?.[0]?.desc || 'N/A';
        const fullAddress = `${address.address_1 || ''} ${address.city || ''}, ${address.state || ''} ${address.postal_code || ''}`;
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
      console.error(err);
      setError(err.message || 'Failed to fetch doctors');
    } finally {
      setLoading(false);
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
      <Text style={styles.title}>Doctors Nearby</Text>
      <Text style={styles.subTitle}>Specialty: {SPECIALTY}</Text>
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