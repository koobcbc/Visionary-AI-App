import React from 'react';
import { View, StyleSheet, Dimensions } from 'react-native';
import Swiper from 'react-native-swiper';
import ChatScreen from './ChatScreen';
import SummaryScreen from './SummaryScreen';
import DoctorsScreen from './DoctorsScreen';
import { useLocalSearchParams } from 'expo-router';

export default function ChatSwiper() {
  const { chatId } = useLocalSearchParams();

  return (
    <View style={styles.wrapper}>
      <ChatScreen chatId={chatId as string} />
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: { flex: 1 },
  dot: { backgroundColor: '#ccc' },
  activeDot: { backgroundColor: '#333' },
  pagination: {
    bottom: 70, // lifts dots from bottom edge
  },
});