import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';

export default function SummaryScreen({ chatId }: { chatId: string }) {
  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Summary</Text>

      <View style={styles.row}>
        <Text style={styles.heading}>Diagnosis</Text>
        <Text style={styles.content}>Glaucoma</Text>
      </View>

      <View style={styles.row}>
        <Text style={styles.heading}>Symptoms</Text>
        <Text style={styles.content}>
          - Often no symptoms in early stages (open-angle){'\n'}
          - Gradual peripheral vision loss{'\n'}
          - Eye pain, nausea (angle-closure){'\n'}
          - Halos around lights
        </Text>
      </View>

      <View style={styles.row}>
        <Text style={styles.heading}>Causes</Text>
        <Text style={styles.content}>Lorem ipsum dolor sit amet</Text>
      </View>

      <View style={styles.row}>
        <Text style={styles.heading}>Treatment Options</Text>
        <Text style={styles.content}>Lorem ipsum dolor sit amet</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: '#fff' },
  title: { fontSize: 20, fontWeight: '700', marginBottom: 15, alignSelf: 'center' },
  row: { marginBottom: 15 },
  heading: { fontWeight: 'bold', fontSize: 16, marginBottom: 4 },
  content: { fontSize: 15, lineHeight: 22, color: '#333' },
});