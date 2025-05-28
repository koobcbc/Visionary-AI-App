import React, { useEffect, useState } from 'react';
import { View, TextInput, Text, Button, StyleSheet, Alert } from 'react-native';
import { doc, getDoc, setDoc } from 'firebase/firestore';
import { db, auth } from '../firebaseConfig';
import { create } from 'react-test-renderer';
import Header from '../components/Header';

export default function AccountScreen() {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');

  const user = auth.currentUser;

  useEffect(() => {
    if (!user) return;
    const fetchData = async () => {
      const userDoc = await getDoc(doc(db, "users", user.uid));
      if (userDoc.exists()) {
        const data = userDoc.data();
        setFirstName(data.firstName || '');
        setLastName(data.lastName || '');
        setPhone(data.phoneNumber || '');
        setEmail(user.email || '');
      }
    };
    fetchData();
  }, [user]);

  const handleUpdate = async () => {
    if (!user) return;
  
    try {
      const userDocRef = doc(db, "users", user.uid);
      const existingDoc = await getDoc(userDocRef);
  
      const existingCreatedAt = existingDoc.exists() ? existingDoc.data().createdAt : new Date();
  
      await setDoc(userDocRef, {
        createdAt: existingCreatedAt,
        modifiedAt: new Date(),
        firstName,
        lastName,
        // Do NOT include phoneNumber or email here — they are locked fields.
      });
  
      Alert.alert("Success", "Profile updated.");
    } catch (err) {
      Alert.alert("Error", "Could not update profile.");
    }
  };

  // Add this helper function above your component
  const formatPhoneNumber = (value: string) => {
    const cleaned = ('' + value).replace(/\D/g, '');
    const match = cleaned.match(/^(\d{0,3})(\d{0,3})(\d{0,4})$/);
    if (!match) return value;
    const [, area, prefix, line] = match;
    if (line) return `(${area}) ${prefix}-${line}`;
    if (prefix) return `(${area}) ${prefix}`;
    if (area) return `(${area}`;
    return '';
  };

  return (
    <View style={styles.container}>
      <Header title="Account" />
      <View style={styles.inputContainer}>
        <Text style={styles.label}>First Name</Text>
        <TextInput style={styles.input} value={firstName} onChangeText={setFirstName} />
        <Text style={styles.label}>Last Name</Text>
        <TextInput style={styles.input} value={lastName} onChangeText={setLastName} />
        <Text style={styles.label}>Phone</Text>
        <TextInput
          style={[styles.input, styles.readOnlyInput]}
          value={phone}
          editable={false}
          selectTextOnFocus={false}
        />

        <Text style={styles.label}>Email</Text>
        <TextInput
          style={[styles.input, styles.readOnlyInput]}
          value={email}
          editable={false}
          selectTextOnFocus={false}
        />
        <Text style={styles.note}>Contact support to update phone or email.</Text>
        <Button title="Update Profile" onPress={handleUpdate} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f2f2f7' },
  inputContainer: { paddingHorizontal: 20 },
  label: { marginTop: 10, marginBottom: 4, fontWeight: 'bold' },
  input: {
    borderWidth: 1, borderColor: '#ccc',
    padding: 10, borderRadius: 6,
    marginBottom: 10
  },
  readOnlyInput: {
    backgroundColor: '#eee',
    color: '#888'
  },
  note: {
    fontSize: 12,
    color: '#999',
    marginBottom: 10,
    marginTop: -6
  }
});