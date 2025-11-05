import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Image } from 'react-native';
import { router } from 'expo-router';

const dashboardIcon = require('../assets/images/dashboard-icon.png');
const chatIcon = require('../assets/images/chaticon2.png');

interface BottomNavigationProps {
  activeTab: 'dashboard' | 'chat';
}

export default function BottomNavigation({ activeTab }: BottomNavigationProps) {

  const handleDashboardPress = () => {
    router.push('/user-dashboard');
  };

  const handleChatPress = () => {
    router.push('/category-selection');
  };

  return (
    <View style={styles.container}>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'dashboard' && styles.activeTab]}
        onPress={handleDashboardPress}
        activeOpacity={0.7}
      >
        <Image source={dashboardIcon} style={styles.icon} resizeMode="contain" />
        <Text style={[styles.label, activeTab === 'dashboard' && styles.activeLabel]}>Dashboard</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.tab, activeTab === 'chat' && styles.activeTab]}
        onPress={handleChatPress}
        activeOpacity={0.7}
      >
        <Image source={chatIcon} style={styles.icon} resizeMode="contain" />
        <Text style={[styles.label, activeTab === 'chat' && styles.activeLabel]}>Chat</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    backgroundColor: '#ffffff',
    borderTopWidth: 1,
    borderTopColor: '#e0e8f0',
    paddingBottom: 20,
    paddingTop: 12,
    paddingHorizontal: 20,
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: -4 },
    elevation: 8,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    borderTopWidth: 3,
    borderTopColor: 'transparent',
  },
  activeTab: {
    borderTopColor: '#4a90e2',
  },
  icon: {
    width: 24,
    height: 24,
    marginBottom: 4,
  },
  label: {
    fontSize: 12,
    color: '#7f8c8d',
    fontWeight: '500',
  },
  activeLabel: {
    color: '#4a90e2',
    fontWeight: '600',
  },
});

