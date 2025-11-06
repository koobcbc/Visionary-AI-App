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

  // Parse diagnosis string - it might be a single string or comma-separated
  const getDiagnosisList = () => {
    if (!summary.diagnosis || summary.diagnosis === "Not enough information") {
      return [];
    }
    // Split by comma and clean up
    return summary.diagnosis
      .split(',')
      .map(d => d.trim())
      .filter(d => d.length > 0);
  };

  const diagnosisList = getDiagnosisList();

  return (
    <ScrollView style={styles.container}>
      <View style={styles.row}>
        <Text style={styles.heading}>Diagnosis</Text>
        {diagnosisList.length > 0 ? (
          <View style={styles.pillsContainer}>
            {diagnosisList.map((diagnosis, index) => (
              <View key={index} style={[styles.pill, { marginRight: 8, marginBottom: 8 }]}>
                <Text style={styles.pillText}>{diagnosis}</Text>
              </View>
            ))}
          </View>
        ) : (
          <Text style={styles.content}>Not enough information</Text>
        )}
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
  heading: { fontWeight: 'bold', fontSize: 16, marginBottom: 4, color: '#2c3e50' },
  content: { fontSize: 15, lineHeight: 22, color: '#2c3e50' },
  pillsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 4,
  },
  pill: {
    backgroundColor: '#DBEDEC',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#A5CCC9',
  },
  pillText: {
    fontSize: 14,
    color: '#2c3e50',
    fontWeight: '500',
  },
});