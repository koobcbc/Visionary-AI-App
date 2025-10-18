import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';

type Summary = {
  diagnosis: string;
  symptoms: string[];
  causes: string[];
  treatments: string[];
  specialty: string;
};

export default function SummaryScreen({ summary }: { summary: Summary }) {
  const renderList = (items: string[]) => {
    if (!items || items.length === 0) return <Text style={styles.content}>Not enough information</Text>;
    return (
      <Text style={styles.content}>
        {items.map((item, index) => `- ${item}${index !== items.length - 1 ? '\n' : ''}`)}
      </Text>
    );
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.row}>
        <Text style={styles.heading}>Diagnosis</Text>
        <Text style={styles.content}>
          {summary.diagnosis && summary.diagnosis !== "Not enough information"
            ? summary.diagnosis
            : "Not enough information"}
        </Text>
      </View>

      <View style={styles.row}>
        <Text style={styles.heading}>Symptoms</Text>
        {renderList(summary.symptoms)}
      </View>

      <View style={styles.row}>
        <Text style={styles.heading}>Causes</Text>
        {renderList(summary.causes)}
      </View>

      <View style={styles.row}>
        <Text style={styles.heading}>Treatment Options</Text>
        {renderList(summary.treatments)}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: '#fff' },
  row: { marginBottom: 15 },
  heading: { fontWeight: 'bold', fontSize: 16, marginBottom: 4 },
  content: { fontSize: 15, lineHeight: 22, color: '#333' },
});