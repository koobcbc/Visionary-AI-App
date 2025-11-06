import React, { useEffect, useState } from 'react';
import {
  View, Text, FlatList, StyleSheet, ActivityIndicator,
  TouchableOpacity, Linking, Alert, TextInput, Button, Modal, Dimensions
} from 'react-native';
import { WebView } from 'react-native-webview';
import * as Location from 'expo-location';
import { Ionicons } from '@expo/vector-icons';
import taxonomy from '../../../assets/nucc_taxonomy_250.json';
import { GoogleGenerativeAI } from "@google/generative-ai";
import Constants from 'expo-constants';
import DropDownPicker from 'react-native-dropdown-picker';
import { doc, updateDoc, getDoc } from 'firebase/firestore';
import { auth, db } from '../../../firebaseConfig'; // adjust path as needed


const STATE = 'IL';

type Doctor = {
  name: string;
  specialty: string;
  address: string;
  mapQuery: string;
  latitude?: number;
  longitude?: number;
};
type TaxonomyEntry = {
  Grouping: string;
  Classification: string;
  Specialization: string;
  "Display Name": string;
  Code: string;
};

type SpecializationEntry = {
  name: string;
  displayName: string;
  code: string;
  specialization: string;
};

type NestedSpecialties = {
  [group: string]: {
    [classification: string]: SpecializationEntry[];
  };
};

type Summary = {
  diagnosis: string;
  symptoms: string[];
  causes: string[];
  treatments: string[];
  specialty: string;
};

export default function DoctorsScreen({ summary, chatCategory }: { summary: Summary; chatCategory?: 'skin' | 'dental' | null }) {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [location, setLocation] = useState<Location.LocationObject | null>(null);
  const [zipCode, setZipCode] = useState<string>('');
  const [city, setCity] = useState<string>('');
  const [zipInput, setZipInput] = useState('');
  const [mapRegion, setMapRegion] = useState({
    latitude: 41.8781, // Chicago default
    longitude: -87.6298,
    latitudeDelta: 0.1,
    longitudeDelta: 0.1,
  });
  const [showMap, setShowMap] = useState(false); // Default to list mode
  const [selectedSpecialty, setSelectedSpecialty] = useState(() => {
    // If summary has a specialty, use it; otherwise use chat category default
    if (summary.specialty) {
      return summary.specialty;
    }
    
    // Set default based on chat category
    if (chatCategory === 'skin') {
      return 'Dermatology';
    } else if (chatCategory === 'dental') {
      return 'General Practice';
    }
    
    return '';
  });
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState<string | null>(null);
  const [selectedClass, setSelectedClass] = useState<string | null>(null);
  const [hasChangedDefaults, setHasChangedDefaults] = useState(false);


  // Dropdown states
  const [groupOpen, setGroupOpen] = useState(false);
  const [groupValue, setGroupValue] = useState<string | null>(null);
  const [groupItems, setGroupItems] = useState<{label: string; value: string}[]>([]);

  const [classOpen, setClassOpen] = useState(false);
  const [classValue, setClassValue] = useState<string | null>(null);
  const [classItems, setClassItems] = useState<{label: string; value: string}[]>([]);

  const [specOpen, setSpecOpen] = useState(false);
  const [specValue, setSpecValue] = useState<string | null>(null);
  const [specItems, setSpecItems] = useState<{label: string; value: string}[]>([]);

  const [nestedSpecialties, setNestedSpecialties] = useState<NestedSpecialties>({});

  // zip code
  const [editingZip, setEditingZip] = useState(false);

  useEffect(() => {
    const tree = buildNestedSpecialties(taxonomy);
    setNestedSpecialties(tree);
    setGroupItems(Object.keys(tree).map(k => ({ label: k, value: k })));

    // Determine which specialty to use for matching
    const specialtyToMatch = summary.specialty || selectedSpecialty;
    
    const matched =
      taxonomy.find(
        (entry) =>
          entry["Specialization"] &&
          entry["Specialization"].toLowerCase() === specialtyToMatch.toLowerCase()
      ) ||
      taxonomy.find(
        (entry) =>
          entry["Classification"] &&
          entry["Specialization"] === "" &&
          entry["Classification"].toLowerCase() === specialtyToMatch.toLowerCase()
      );
      
    if (matched) {
      setGroupValue(matched.Grouping);
      setClassValue(matched.Classification);
      setSpecValue(matched.Specialization || matched.Classification); // This is used as dropdown label
      setSelectedSpecialty(matched.Specialization || matched.Classification); // Used for search
    }
  }, [summary.specialty, chatCategory]);

  useEffect(() => {
    const fetchZipFromUser = async () => {
      try {
        const user = auth.currentUser;
        if (user) {
          const userRef = doc(db, "users", user.uid);
          const docSnap = await getDoc(userRef);
  
          if (docSnap.exists()) {
            const data = docSnap.data();
            if (data.zipCode) {
              const zip = data.zipCode;
              setZipCode(zip);
              setZipInput(zip);

              const geoResults = await Location.geocodeAsync(zip);
              if (geoResults.length > 0) {
                const { latitude, longitude } = geoResults[0];
                const reverse = await Location.reverseGeocodeAsync({ latitude, longitude });
                const place = reverse[0];
                if (place?.city || place?.subregion || place?.region) {
                  setCity(place.city || place.subregion || place.region || '');
                }
              }

              fetchDoctors(undefined, undefined, zip, selectedSpecialty);
              return; // skip location request
            }
          }
        }
  
        // If no zipCode in Firestore or user not logged in
        requestLocation();
      } catch (err) {
        console.error("Failed to load user ZIP from Firestore:", err);
        Alert.alert("Firestore Error", "Unable to fetch saved ZIP code.");
        requestLocation();
      }
    };
  
    fetchZipFromUser();
  }, []);

  function buildNestedSpecialties(taxonomy: TaxonomyEntry[]): NestedSpecialties {
    const nested: NestedSpecialties = {};
  
    taxonomy.forEach(({ Grouping, Classification, Specialization, "Display Name": DisplayName, Code }) => {
      if (!Grouping || !Classification) return;
  
      if (!nested[Grouping]) nested[Grouping] = {};
      if (!nested[Grouping][Classification]) nested[Grouping][Classification] = [];
  
      nested[Grouping][Classification].push({
        name: Specialization || Classification,
        displayName: DisplayName,
        code: Code,
        specialization: Specialization,
      });
    });
  
    return nested;
  }

  useEffect(() => {
    if (groupValue) {
      const classes = Object.keys(nestedSpecialties[groupValue] || {});
      setClassItems(classes.map(c => ({ label: c, value: c })));
      if (hasChangedDefaults) {
        setClassValue(null);
        setSpecValue(null);
        setSpecItems([]);
      }
    }
  }, [groupValue]);

  function setGroupValueInDropdown(callback: any) {
    const value = typeof callback === 'function' ? callback(groupValue) : callback;
    setGroupValue(value);
    setHasChangedDefaults(true);
  }

  useEffect(() => {
    if (groupValue && classValue) {
      const specs = nestedSpecialties[groupValue][classValue];
      setSpecItems(
        specs.map((s: SpecializationEntry) => ({
          label: s.name,
          value: s.name, // ensures uniqueness
        }))
      );
    }
  }, [classValue]);

  useEffect(() => {
    if (specValue && !loading) {
      fetchDoctors(undefined, undefined, undefined, specValue);
    }
  }, [specValue]);

  const requestLocation = async () => {
    setLoading(true);
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        setLoading(false);
        return;
      }

      const loc = await Location.getCurrentPositionAsync({});
      setLocation(loc);
      console.log("loc", loc)

      const geo = await Location.reverseGeocodeAsync({
        latitude: loc.coords.latitude,
        longitude: loc.coords.longitude
      });
      
      
      if (geo[0]) {
        const { postalCode, city, subregion, region } = geo[0];
        if (postalCode) {
          setZipInput(postalCode)
          setZipCode(postalCode)
          try {
            const user = auth.currentUser;
            if (user) {
              const userRef = doc(db, "users", user.uid);
              await updateDoc(userRef, { zipCode: postalCode });
              console.log("Zip code saved to Firestore");
            }
          } catch (err) {
            console.error("Failed to update Firestore:", err);
            Alert.alert("Firestore Error", "Failed to save ZIP code.");
          }
        };
        if (city || subregion || region) {
          setCity(city || subregion || region || ''); // fallback if city is undefined
        }
      }

      fetchDoctors(loc.coords.latitude, loc.coords.longitude, undefined, selectedSpecialty);
    } catch (err: any) {
      setError("Unable to fetch location.");
      setLoading(false);
    }
  };

  const formatZipCode = (address: string) => {
    return address.replace(/(\D|^)(\d{5})(\d{4})(\D|$)/, '$1$2-$3$4');
  };

  const fetchDoctors = async (lat?: number, lon?: number, zip?: string, specialty?: string) => {
    setLoading(true);
    try {
      let selected = specialty || selectedSpecialty;
      
      // Use a more reliable CORS proxy
      let url = `https://api.allorigins.win/raw?url=${encodeURIComponent(`https://npiregistry.cms.hhs.gov/api/?version=2.1&taxonomy_description=${selected}&limit=20`)}`;

      if (zip) {
        console.log("zip", zip)
        url = `https://api.allorigins.win/raw?url=${encodeURIComponent(`https://npiregistry.cms.hhs.gov/api/?version=2.1&taxonomy_description=${selected}&limit=20&postal_code=${zip}`)}`;
      } else if (lat && lon) {
        const geo = await Location.reverseGeocodeAsync({ latitude: lat, longitude: lon });
        if (geo[0]?.postalCode) {
          console.log("zip from geo", geo[0].postalCode)
          url = `https://api.allorigins.win/raw?url=${encodeURIComponent(`https://npiregistry.cms.hhs.gov/api/?version=2.1&taxonomy_description=${selected}&limit=20&postal_code=${geo[0].postalCode}`)}`;
        } else {
          throw new Error("Failed to determine postal code.");
        }
      } else {
        url = `https://api.allorigins.win/raw?url=${encodeURIComponent(`https://npiregistry.cms.hhs.gov/api/?version=2.1&taxonomy_description=${selected}&limit=20&state=${STATE}`)}`;
      }

      const res = await fetch(url);
      const json = await res.json();

      if (!json.results) throw new Error('No results found');

      const parsed: Doctor[] = await Promise.all(
        json.results.map(async (doc: any) => {
          const basic = doc.basic || {};
          
          // Find the address with address_purpose as "LOCATION"
          const addresses = doc.addresses || [];
          const locationAddress = addresses.find((addr: any) => addr.address_purpose === 'LOCATION') || addresses[0] || {};
          
          const name = `${basic.first_name || ''} ${basic.last_name || ''}`.trim();
          const specialty = doc.taxonomies?.[0]?.desc || 'N/A';
          const fullAddress = `${locationAddress.address_1 || ''} ${locationAddress.city || ''}, ${locationAddress.state || ''} ${formatZipCode(locationAddress.postal_code) || ''}`;
          const mapQuery = `${locationAddress.address_1 || ''}, ${locationAddress.city || ''}, ${locationAddress.state || ''}`;

          // Geocode address to get coordinates
          let latitude: number | undefined;
          let longitude: number | undefined;
          try {
            if (locationAddress.address_1 && locationAddress.city && locationAddress.state) {
              const geoResults = await Location.geocodeAsync(mapQuery);
              if (geoResults.length > 0) {
                latitude = geoResults[0].latitude;
                longitude = geoResults[0].longitude;
              }
            }
          } catch (err) {
            console.error('Geocoding error for', mapQuery, err);
          }

          return {
            name: name || doc.basic.organization_name || 'Unknown',
            specialty,
            address: fullAddress,
            mapQuery,
            latitude,
            longitude
          };
        })
      );
      
      setDoctors(parsed);
      
      // Update map region to show doctors
      if (parsed.length > 0) {
        const doctorsWithCoords = parsed.filter(d => d.latitude && d.longitude);
        if (doctorsWithCoords.length > 0) {
          const avgLat = doctorsWithCoords.reduce((sum, d) => sum + (d.latitude || 0), 0) / doctorsWithCoords.length;
          const avgLon = doctorsWithCoords.reduce((sum, d) => sum + (d.longitude || 0), 0) / doctorsWithCoords.length;
          setMapRegion({
            latitude: avgLat,
            longitude: avgLon,
            latitudeDelta: 0.1,
            longitudeDelta: 0.1,
          });
        }
      }
      
      // If we have user location, center map on user
      if (location) {
        setMapRegion({
          latitude: location.coords.latitude,
          longitude: location.coords.longitude,
          latitudeDelta: 0.05,
          longitudeDelta: 0.05,
        });
      }
    } catch (err: any) {
      console.error(err)
      setError(err.message || 'Failed to fetch doctors');
    } finally {
      setLoading(false);
    }
  };

  const API_KEY = Constants.expoConfig?.extra?.GEMINI_API_KEY;
  const genAI = new GoogleGenerativeAI(API_KEY);

  async function getGeminiResponse(msg: string) {
    try {
      const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash-001" });
      const chat = model.startChat({
        history: [
          { role: "user", parts: [{ text: "Hi" }] },
          { role: "model", parts: [{ text: "Hello! How can I assist you today?" }] },
        ]
      });
      const result = await chat.sendMessage(msg);
      return result.response.text();
    } catch (error) {
      console.error("Gemini error:", error);
      return "Sorry, something went wrong.";
    }
  }

  const openInMaps = (query: string) => {
    const url = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`;
    Linking.openURL(url).catch(() => Alert.alert('Error', 'Failed to open Maps'));
  };

  const capitalize = (str: string) => {
    if (str) {
      return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
    }
    return '';
  }

  const generateMapHTML = () => {
    const doctorsWithCoords = doctors.filter(d => d.latitude && d.longitude);
    
    // Get Google Maps API key from environment
    const mapsApiKey = Constants.expoConfig?.extra?.GOOGLE_MAPS_API_KEY || '';
    
    if (!mapsApiKey) {
      console.warn('Google Maps API key not found');
    }
    
    // Calculate center point
    let centerLat = location?.coords.latitude || mapRegion.latitude;
    let centerLon = location?.coords.longitude || mapRegion.longitude;
    
    if (doctorsWithCoords.length > 0) {
      // Use average of doctor locations if available
      const avgLat = doctorsWithCoords.reduce((sum, d) => sum + (d.latitude || 0), 0) / doctorsWithCoords.length;
      const avgLon = doctorsWithCoords.reduce((sum, d) => sum + (d.longitude || 0), 0) / doctorsWithCoords.length;
      
      // If user location exists, use it; otherwise use average of doctors
      if (!location) {
        centerLat = avgLat;
        centerLon = avgLon;
      }
    }
    
    // Create markers data for all doctors
    const markersData = doctorsWithCoords.map((doctor, index) => {
      const escapedName = (doctor.name || 'Doctor').replace(/'/g, "\\'").replace(/"/g, "&quot;");
      const escapedSpecialty = (doctor.specialty || '').replace(/'/g, "\\'").replace(/"/g, "&quot;");
      return {
        lat: doctor.latitude,
        lng: doctor.longitude,
        name: escapedName,
        specialty: escapedSpecialty,
        label: (index + 1).toString()
      };
    });
    
    // Use Maps JavaScript API to show multiple markers
    // This is more flexible than Embed API and supports multiple markers
    return `
      <!DOCTYPE html>
      <html>
        <head>
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <style>
            * {
              margin: 0;
              padding: 0;
              box-sizing: border-box;
            }
            html, body {
              height: 100%;
              width: 100%;
              overflow: hidden;
            }
            #map {
              height: 100%;
              width: 100%;
            }
          </style>
        </head>
        <body>
          <div id="map"></div>
          <script>
            function initMap() {
              const center = { lat: ${centerLat}, lng: ${centerLon} };
              const map = new google.maps.Map(document.getElementById('map'), {
                zoom: ${doctorsWithCoords.length > 0 ? 12 : 10},
                center: center,
                mapTypeId: 'roadmap'
              });

              // Add user location marker if available
              ${location ? `
                new google.maps.Marker({
                  position: { lat: ${location.coords.latitude}, lng: ${location.coords.longitude} },
                  map: map,
                  title: 'Your Location',
                  icon: {
                    path: google.maps.SymbolPath.CIRCLE,
                    scale: 8,
                    fillColor: '#4285F4',
                    fillOpacity: 1,
                    strokeColor: '#ffffff',
                    strokeWeight: 2
                  },
                  label: {
                    text: 'You',
                    color: '#4285F4',
                    fontSize: '12px',
                    fontWeight: 'bold'
                  }
                });
              ` : ''}

              // Add markers for all doctors
              const markers = ${JSON.stringify(markersData)};
              
              const bounds = new google.maps.LatLngBounds();
              ${location ? `bounds.extend(new google.maps.LatLng(${location.coords.latitude}, ${location.coords.longitude}));` : ''}
              
              markers.forEach((markerData) => {
                const marker = new google.maps.Marker({
                  position: { lat: markerData.lat, lng: markerData.lng },
                  map: map,
                  title: markerData.name,
                  label: markerData.label
                });

                const infoWindow = new google.maps.InfoWindow({
                  content: '<div style="padding: 8px;"><strong>' + markerData.name + '</strong><br>' + markerData.specialty + '</div>'
                });

                marker.addListener('click', () => {
                  infoWindow.open(map, marker);
                });
                
                bounds.extend(new google.maps.LatLng(markerData.lat, markerData.lng));
              });

              // Fit bounds to show all markers
              if (markers.length > 0 || ${location ? 'true' : 'false'}) {
                map.fitBounds(bounds);
              }
            }
          </script>
          <script async defer
            src="https://maps.googleapis.com/maps/api/js?key=${mapsApiKey}&callback=initMap">
          </script>
        </body>
      </html>
    `;
  };

  console.log(zipCode, city)
  console.log("doctors", doctors)
  return (
    <View style={styles.container}>

      <View style={styles.pillContainer}>
        <View style={{ alignItems: 'center', marginBottom: 6 }}>
          <TouchableOpacity
            style={styles.pill}
            activeOpacity={0.8}
            onPress={() => setEditingZip(true)}
          >
            <View style={styles.pillTopRow}>
              <Ionicons name="location-sharp" size={16} color="#000" style={{ marginRight: 4 }} />
              <Text style={styles.pillZip}>{zipCode || ''}</Text>
              <Ionicons name="chevron-down" size={16} color="#000" style={{ marginLeft: 4 }} />
            </View>
            <Text style={styles.pillCity}>{city || 'City'}</Text>
          </TouchableOpacity>
        </View>
        <Modal visible={editingZip} transparent animationType="fade">
          <View style={styles.modalOverlay}>
            <View style={styles.modalBox}>
              <Text style={styles.modalLabel}>Enter ZIP Code:</Text>
              <TextInput
                style={styles.input}
                value={zipInput}
                onChangeText={setZipInput}
                keyboardType="numeric"
                maxLength={5}
                autoFocus
              />
              <View style={styles.modalButtons}>
                <TouchableOpacity onPress={() => setEditingZip(false)} style={styles.cancelBtn}>
                  <Text style={{ color: '#555' }}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  onPress={async () => {
                    const trimmed = zipInput.trim();
                    if (trimmed.length === 5) {
                      setZipCode(trimmed);
                      fetchDoctors(undefined, undefined, trimmed, selectedSpecialty);
                      setEditingZip(false);

                      try {
                        const user = auth.currentUser;
                        if (user) {
                          const userRef = doc(db, "users", user.uid);
                          await updateDoc(userRef, { zipCode: trimmed });
                          console.log("Zip code saved to Firestore");
                        }
                      } catch (err) {
                        console.error("Failed to update Firestore:", err);
                        Alert.alert("Firestore Error", "Failed to save ZIP code.");
                      }

                    } else {
                      Alert.alert("Invalid ZIP", "Please enter a valid 5-digit ZIP code.");
                    }
                  }}
                  style={styles.saveBtn}
                >
                  <Text style={{ color: '#fff', fontWeight: 'bold' }}>Save</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </Modal>
      </View>

      <View style={styles.specialtyContainer}>
        <Text style={styles.specialtyText}>
          Specialty: {capitalize(specValue || '')}
        </Text>
        <TouchableOpacity onPress={() => setModalVisible(true)}>
          <Ionicons name="pencil" size={20} color="black" style={styles.iconStyle} />
        </TouchableOpacity>
      </View>

      <Modal visible={modalVisible} transparent animationType="fade">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
          <DropDownPicker
            open={groupOpen}
            value={groupValue}
            items={groupItems}
            setOpen={setGroupOpen}
            setValue={setGroupValueInDropdown}
            setItems={setGroupItems}
            placeholder="Select Group"
            zIndex={3000}
            zIndexInverse={1000}
          />

          <DropDownPicker
            open={classOpen}
            value={classValue}
            items={classItems}
            setOpen={setClassOpen}
            setValue={setClassValue}
            setItems={setClassItems}
            placeholder="Select Classification"
            zIndex={2000}
            zIndexInverse={2000}
          />

          <DropDownPicker
            open={specOpen}
            value={specValue}
            items={specItems}
            setOpen={setSpecOpen}
            setValue={setSpecValue}
            setItems={setSpecItems}
            placeholder="Select Specialization"
            zIndex={1000}
            zIndexInverse={3000}
          />
            {/* Confirm Button */}
            <TouchableOpacity
              style={styles.saveBtn}
              onPress={() => {
                if (specValue) {
                  setSelectedSpecialty(specValue);
                  fetchDoctors(undefined, undefined, zipCode, specValue);
                  setModalVisible(false);
                } else {
                  Alert.alert("Select Specialization", "Please choose a valid specialization.");
                }
              }}
            >
              <Text style={{ color: '#fff', fontWeight: 'bold', textAlign: 'center' }}>Confirm</Text>
            </TouchableOpacity>

            {/* Optional Cancel Button */}
            <TouchableOpacity
              style={{ marginTop: 10 }}
              onPress={() => setModalVisible(false)}
            >
              <Text style={{ color: '#666', textAlign: 'center' }}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      {/* Toggle between Map and List */}
      <View style={styles.toggleContainer}>
        <TouchableOpacity
          style={[styles.toggleButton, showMap && styles.toggleButtonActive]}
          onPress={() => setShowMap(true)}
        >
          <Ionicons name="map" size={20} color={showMap ? '#fff' : '#666'} />
          <Text style={[styles.toggleText, showMap && styles.toggleTextActive]}>Map</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.toggleButton, !showMap && styles.toggleButtonActive]}
          onPress={() => setShowMap(false)}
        >
          <Ionicons name="list" size={20} color={!showMap ? '#fff' : '#666'} />
          <Text style={[styles.toggleText, !showMap && styles.toggleTextActive]}>List</Text>
        </TouchableOpacity>
      </View>

      {loading ? (
        <ActivityIndicator size="large" style={{ marginTop: 50 }} />
      ) : error ? (
        <View style={styles.errorContainer}>
          <Text style={{ color: 'red', fontSize: 16 }}>{error}</Text>
        </View>
      ) : showMap ? (
        <View style={styles.mapContainer}>
          <WebView
            style={styles.map}
            source={{
              html: generateMapHTML(),
            }}
            javaScriptEnabled={true}
            domStorageEnabled={true}
            originWhitelist={['*']}
          />
        </View>
      ) : (
        <FlatList
          data={doctors}
          keyExtractor={(item, idx) => `${item.name}-${idx}`}
          renderItem={({ item }) => (
            <TouchableOpacity style={styles.card} onPress={() => openInMaps(item.mapQuery)}>
              <View style={styles.cardContent}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.name}>{item.name}</Text>
                  <Text style={styles.specialty}>{item.specialty}</Text>
                  <Text style={styles.address}>{item.address}</Text>
                </View>
                <Ionicons name="location-outline" size={20} color="#A5CCC9" />
              </View>
            </TouchableOpacity>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff', padding: 10 },
  card: {
    backgroundColor: '#DBEDEC',
    padding: 12,
    marginBottom: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#A5CCC9',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  name: { fontSize: 16, fontWeight: 'bold', color: '#2c3e50' },
  specialty: { fontSize: 14, color: '#2c3e50', marginTop: 4 },
  address: { fontSize: 13, color: '#555', marginTop: 4 },
  errorContainer: {
    flex: 1, alignItems: 'center', justifyContent: 'center'
  },
  specialtyContainer: { flexDirection: 'row', alignItems: 'center', marginBottom: 16 },
  specialtyText: { fontSize: 16, fontWeight: 'bold' },
  editButton: { marginLeft: 10, color: 'blue' },
  specialtyItem: { padding: 10, fontSize: 16 },
  iconStyle: { marginLeft: 8 },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center'
  },
  modalContent: {
    backgroundColor: '#fff',
    width: '80%',
    borderRadius: 10,
    padding: 16,
    maxHeight: 400
  },
  pillContainer: {
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  pill: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 20,
    paddingVertical: 4,
    paddingHorizontal: 12,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fff',
    minWidth: 80,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 2 },
  },
  pillTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 2,
  },
  pillZip: {
    fontSize: 13,
    fontWeight: '600',
    color: '#000',
  },
  
  pillCity: {
    fontSize: 11,
    color: '#333',
    textAlign: 'center',
  },
  zipInput: {
    borderBottomWidth: 1,
    borderColor: '#aaa',
    fontSize: 16,
    minWidth: 80,
    color: '#000',
    paddingVertical: 4,
    paddingHorizontal: 6,
    backgroundColor: '#f5f7fa',
    borderRadius: 4
  },
  modalBox: {
    backgroundColor: '#fff',
    width: '80%',
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
  },
  modalLabel: {
    fontSize: 16,
    marginBottom: 10,
  },
  input: {
    borderBottomWidth: 1,
    borderColor: '#ccc',
    width: '60%',
    textAlign: 'center',
    fontSize: 18,
    marginBottom: 20,
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 20,
  },
  cancelBtn: {
    padding: 10,
  },
  saveBtn: {
    backgroundColor: '#2c3e50',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  cardContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  toggleContainer: {
    flexDirection: 'row',
    marginBottom: 10,
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
    padding: 4,
  },
  toggleButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    gap: 6,
  },
  toggleButtonActive: {
    backgroundColor: '#2c3e50',
  },
  toggleText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  toggleTextActive: {
    color: '#fff',
  },
  mapContainer: {
    flex: 1,
    height: Dimensions.get('window').height * 0.6,
    marginTop: 10,
    borderRadius: 8,
    overflow: 'hidden',
  },
  map: {
    width: '100%',
    height: '100%',
  },
});