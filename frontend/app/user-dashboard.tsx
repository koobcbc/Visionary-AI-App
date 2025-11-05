import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity,
  TouchableWithoutFeedback, Keyboard, Alert, Image, ScrollView, Modal, Platform
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { doc, getDoc, collection, query, where, getDocs, orderBy, limit } from 'firebase/firestore';
import { db } from '../firebaseConfig';
import { getAuth, signOut } from 'firebase/auth';
import AsyncStorage from '@react-native-async-storage/async-storage';
import BottomNavigation from '../components/BottomNavigation';

const logo = require('../assets/images/transparent-logo.png');
const humanImage = require('../assets/images/man-transparent_skinny.png');

const auth = getAuth();

interface Diagnosis {
  name: string;
  confidence: number;
}

interface DiagnosisCard {
  category: string;
  diagnoses: Diagnosis[];
  icon: string;
}

export default function UserDashboardScreen() {
  const [menuVisible, setMenuVisible] = useState(false);
  const [userName, setUserName] = useState('');
  const [profileIncomplete, setProfileIncomplete] = useState(false);
  const [diagnosisCards, setDiagnosisCards] = useState<DiagnosisCard[]>([]);
  const [expandedCard, setExpandedCard] = useState<string | null>(null);
  const userInitial = userName ? userName.charAt(0).toUpperCase() : '?';

  const fetchUserName = async () => {
    const user = auth.currentUser;
    if (!user) {
      router.replace('/');
      return;
    }

    // Try to load from cache first for instant display
    try {
      const cachedName = await AsyncStorage.getItem(`userName_${user.uid}`);
      if (cachedName) {
        setUserName(cachedName);
      }
    } catch (error) {
      console.log('Error loading cached user name:', error);
    }

    // Then fetch fresh data from Firestore
    try {
      const docRef = doc(db, "users", user.uid);
      const docSnap = await getDoc(docRef);
      if (docSnap.exists()) {
        const data = docSnap.data();
        const firstName = data.firstName || '';
        setUserName(firstName);
        setProfileIncomplete(data.profileCreated !== true);
        
        // Cache the user name for next time
        try {
          await AsyncStorage.setItem(`userName_${user.uid}`, firstName);
        } catch (error) {
          console.log('Error caching user name:', error);
        }
      }
    } catch (error) {
      console.log('Error fetching user name:', error);
    }
  };

  const fetchDiagnosisData = async () => {
    // For now, use placeholder data
    // TODO: Replace with actual diagnosis data from user's chat history
    const cards: DiagnosisCard[] = [
      {
        category: 'Dental',
        diagnoses: [
          { name: 'Cavity', confidence: 85 },
          { name: 'Gingivitis', confidence: 72 },
          { name: 'Tooth Decay', confidence: 68 },
          { name: 'Enamel Erosion', confidence: 55 },
        ],
        icon: 'medical-outline',
      },
      {
        category: 'Skin',
        diagnoses: [
          { name: 'Acne', confidence: 78 },
          { name: 'Eczema', confidence: 65 },
          { name: 'Rash', confidence: 58 },
          { name: 'Dry Skin', confidence: 52 },
        ],
        icon: 'body-outline',
      },
    ];
    setDiagnosisCards(cards);
  };

  useEffect(() => {
    fetchUserName();
    fetchDiagnosisData();
  }, []);

  const handleLogout = async () => {
    try {
      const user = auth.currentUser;
      if (user) {
        await AsyncStorage.removeItem(`userName_${user.uid}`);
      }
      await signOut(auth);
      await new Promise(res => setTimeout(res, 500));
      router.replace('/');
    } catch (error) {
      Alert.alert("Logout Failed", "An error occurred while logging out.");
    }
  };

  return (
    <TouchableWithoutFeedback onPress={() => { setMenuVisible(false); Keyboard.dismiss(); }}>
      <View style={styles.container}>
        <View style={styles.header}>
          <Image source={logo} style={styles.logo} resizeMode="contain" />
          <View style={styles.headerSpacer} />
          <View>
            <TouchableOpacity style={styles.avatar} onPress={() => setMenuVisible(!menuVisible)}>
              <Text style={styles.avatarText}>{userInitial}</Text>
              {profileIncomplete && (
                <View style={styles.incompleteIndicator}>
                  <Ionicons name="warning" size={12} color="#e74c3c" />
                </View>
              )}
            </TouchableOpacity>
            {menuVisible && (
              <View style={styles.menu}>
                {profileIncomplete && (
                  <TouchableOpacity onPress={() => { setMenuVisible(false); router.push('/profile-creation'); }}>
                    <Text style={[styles.menuItem, styles.incompleteMenuItem]}>Complete Profile</Text>
                  </TouchableOpacity>
                )}
                <TouchableOpacity onPress={() => { setMenuVisible(false); router.push('/account'); }}>
                  <Text style={styles.menuItem}>Account</Text>
                </TouchableOpacity>
                <TouchableOpacity onPress={() => { setMenuVisible(false); router.push('/settings'); }}>
                  <Text style={styles.menuItem}>Settings</Text>
                </TouchableOpacity>
                <TouchableOpacity onPress={handleLogout}>
                  <Text style={styles.menuItem}>Logout</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        </View>

        <View style={styles.listPanel}>
          <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
            <View style={styles.mainSection}>
              <View style={styles.avatarSection}>
                <View style={styles.titleContainer}>
                  <Text style={styles.title}>Health Diagnosis</Text>
                </View>
                <View style={styles.imageContainer}>
                  <Image source={humanImage} style={styles.humanImage} resizeMode="contain" />
                </View>
              </View>
              <View style={styles.cardsColumn}>
                {diagnosisCards.map((card, index) => {
                  const isTopCard = index === 0; // Dental card
                  const isExpanded = expandedCard === card.category;
                  const maxVisiblePills = 3; // Show max 3 pills before expanding
                  const visibleDiagnoses = isExpanded ? card.diagnoses : card.diagnoses.slice(0, maxVisiblePills);
                  const hasMoreDiagnoses = card.diagnoses.length > maxVisiblePills;
                  
                  return (
                    <View key={card.category} style={styles.cardWithLine}>
                      {/* Connecting Line */}
                      <View style={[
                        styles.connectingLine,
                        isTopCard ? styles.lineTop : styles.lineMiddle
                      ]}>
                        <View style={styles.lineGradient} />
                      </View>
                      
                      {/* Diagnosis Card */}
                      <TouchableOpacity
                        style={styles.diagnosisCard}
                        onPress={() => {
                          if (hasMoreDiagnoses && !isExpanded) {
                            setExpandedCard(card.category);
                          } else if (isExpanded) {
                            setExpandedCard(null);
                          }
                        }}
                        activeOpacity={0.7}
                      >
                        <View style={styles.cardHeader}>
                          <Ionicons name={card.icon as any} size={20} color="#2c3e50" />
                          <Text style={styles.cardCategoryLabel}>{card.category}</Text>
                          {hasMoreDiagnoses && (
                            <Ionicons 
                              name={isExpanded ? "chevron-up" : "chevron-down"} 
                              size={16} 
                              color="#4a90e2" 
                              style={styles.expandIcon}
                            />
                          )}
                        </View>
                        
                        <View style={styles.pillsContainer}>
                          {visibleDiagnoses.map((diagnosis, diagIndex) => (
                            <View key={diagIndex} style={styles.diagnosisPill}>
                              <Text style={styles.pillText}>{diagnosis.name}</Text>
                              <Text style={styles.pillPercentage}>{diagnosis.confidence}%</Text>
                            </View>
                          ))}
                          {hasMoreDiagnoses && !isExpanded && (
                            <TouchableOpacity
                              style={styles.expandPill}
                              onPress={() => setExpandedCard(card.category)}
                            >
                              <Text style={styles.expandPillText}>+{card.diagnoses.length - maxVisiblePills} more</Text>
                            </TouchableOpacity>
                          )}
                        </View>
                      </TouchableOpacity>
                    </View>
                  );
                })}
              </View>
            </View>

            {/* Expanded Card Modal */}
            {expandedCard && (
              <Modal
                visible={!!expandedCard}
                transparent={true}
                animationType="fade"
                onRequestClose={() => setExpandedCard(null)}
              >
                <View style={styles.modalOverlay}>
                  <TouchableOpacity
                    style={StyleSheet.absoluteFill}
                    activeOpacity={1}
                    onPress={() => setExpandedCard(null)}
                  />
                  <View style={styles.modalContent}>
                    {diagnosisCards
                      .filter(card => card.category === expandedCard)
                      .map((card) => (
                        <View key={card.category}>
                          <View style={styles.modalHeader}>
                            <View style={styles.modalHeaderLeft}>
                              <Ionicons name={card.icon as any} size={24} color="#2c3e50" />
                              <Text style={styles.modalTitle}>{card.category} Diagnoses</Text>
                            </View>
                            <TouchableOpacity
                              onPress={() => setExpandedCard(null)}
                              style={styles.closeButton}
                            >
                              <Ionicons name="close" size={24} color="#2c3e50" />
                            </TouchableOpacity>
                          </View>
                          <ScrollView style={styles.modalScrollView} showsVerticalScrollIndicator={false}>
                            <View style={styles.modalPillsContainer}>
                              {card.diagnoses.map((diagnosis, index) => (
                                <View key={index} style={styles.modalPill}>
                                  <Text style={styles.modalPillText}>{diagnosis.name}</Text>
                                  <Text style={styles.modalPillPercentage}>{diagnosis.confidence}%</Text>
                                </View>
                              ))}
                            </View>
                          </ScrollView>
                        </View>
                      ))}
                  </View>
                </View>
              </Modal>
            )}
          </ScrollView>
        </View>

        <BottomNavigation activeTab="dashboard" />
      </View>
    </TouchableWithoutFeedback>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f0f7ff',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 10,
    paddingTop: 20,
    paddingHorizontal: 20,
    zIndex: 1000,
    position: 'relative',
  },
  logo: {
    width: 140,
    height: 60,
  },
  headerSpacer: {
    flex: 1,
  },
  avatar: {
    backgroundColor: '#4a90e2',
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  avatarText: {
    fontWeight: '700',
    color: '#fff',
    fontSize: Platform.select({
      ios: 18,
      default: 20,
    }),
  },
  incompleteIndicator: {
    position: 'absolute',
    top: -2,
    right: -2,
    backgroundColor: '#fff',
    borderRadius: 8,
    width: 16,
    height: 16,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#e74c3c',
  },
  menu: {
    backgroundColor: '#ffffff',
    borderRadius: 8,
    paddingVertical: 8,
    paddingHorizontal: 10,
    position: 'absolute',
    top: 48,
    right: 0,
    width: 180,
    zIndex: 9999,
    elevation: 16,
    shadowColor: '#000',
    shadowOpacity: 0.12,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 6 },
    borderWidth: 1,
    borderColor: '#e2e6ea',
  },
  menuItem: {
    paddingVertical: 8,
    fontSize: Platform.select({
      ios: 16,
      default: 18,
    }),
    color: '#333',
    fontFamily: 'NotoSans_400Regular',
  },
  incompleteMenuItem: {
    color: '#e74c3c',
    fontWeight: 'bold',
  },
  listPanel: {
    flex: 1,
    backgroundColor: '#ffffff',
    borderRadius: 0,
    padding: 12,
    paddingHorizontal: 0,
    shadowColor: '#000',
    shadowOpacity: 0.06,
    shadowRadius: 1,
    shadowOffset: { width: 0, height: 3 },
    borderWidth: 1,
    borderColor: '#e0e8f0',
    marginHorizontal: 0,
    marginBottom: 80,
  },
  content: {
    flex: 1,
  },
  mainSection: {
    flexDirection: 'row',
    marginBottom: 24,
    alignItems: 'flex-start',
    gap: 16,
  },
  avatarSection: {
    width: '50%',
    maxWidth: 300,
    alignItems: 'center',
    justifyContent: 'center',
  },
  titleContainer: {
    marginBottom: 21,
    marginTop: 10,
    width: '100%',
    alignItems: 'center',
  },
  imageContainer: {
    width: '100%',
    alignItems: 'flex-start',
  },
  humanImage: {
    width: '90%',
    height: 400,    
  },
  title: {
    fontSize: Platform.select({
      ios: 21,
      default: 25,
    }),
    fontWeight: '700',
    color: '#2c3e50',
    fontFamily: 'NotoSans_700Bold',
  },
  cardsColumn: {
    flex: 1,
    paddingTop: '13%',
    gap: 20,
    position: 'relative',
  },
  cardWithLine: {
    flexDirection: 'row',
    alignItems: 'center',
    position: 'relative',
    marginLeft: 0,
    marginRight: 0,
  },
  connectingLine: {
    width: 110,
    height: 2,
    position: 'absolute',
    left: -110,
    zIndex: 1,
  },
  lineTop: {
    top: '25%',
  },
  lineMiddle: {
    top: '50%',
  },
  lineGradient: {
    width: '100%',
    height: '100%',
    backgroundColor: '#FFD700',
    opacity: 0.6,
    borderTopRightRadius: 2,
    borderBottomRightRadius: 2,
  },
  diagnosisCard: {
    width: '90%',
    minHeight: 100,
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: '#e0e8f0',
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
    marginRight: 20,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    gap: 8,
  },
  cardCategoryLabel: {
    fontSize: Platform.select({
      ios: 16,
      default: 18,
    }),
    fontWeight: '700',
    color: '#2c3e50',
    fontFamily: 'NotoSans_700Bold',
    flex: 1,
  },
  expandIcon: {
    marginLeft: 'auto',
  },
  pillsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  diagnosisPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#e8f4fd',
    borderRadius: 16,
    paddingVertical: 6,
    paddingHorizontal: 12,
    gap: 6,
    borderWidth: 1,
    borderColor: '#cce0f5',
  },
  pillText: {
    fontSize: Platform.select({
      ios: 12,
      default: 13,
    }),
    fontWeight: '600',
    color: '#2c3e50',
    fontFamily: 'NotoSans_600SemiBold',
  },
  pillPercentage: {
    fontSize: Platform.select({
      ios: 11,
      default: 12,
    }),
    fontWeight: '700',
    color: '#4a90e2',
    fontFamily: 'NotoSans_700Bold',
  },
  expandPill: {
    backgroundColor: '#f0f7ff',
    borderRadius: 16,
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderWidth: 1,
    borderColor: '#4a90e2',
    borderStyle: 'dashed',
  },
  expandPillText: {
    fontSize: Platform.select({
      ios: 11,
      default: 12,
    }),
    fontWeight: '600',
    color: '#4a90e2',
    fontFamily: 'NotoSans_600SemiBold',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#ffffff',
    borderRadius: 20,
    width: '95%',
    maxHeight: '80%',
    padding: 20,
    shadowColor: '#000',
    shadowOpacity: 0.25,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 5 },
    elevation: 10,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  modalTitle: {
    fontSize: Platform.select({
      ios: 20,
      default: 24,
    }),
    fontWeight: '700',
    color: '#2c3e50',
    fontFamily: 'NotoSans_700Bold',
  },
  closeButton: {
    padding: 4,
  },
  modalScrollView: {
    maxHeight: '100%',
  },
  modalPillsContainer: {
    flexDirection: 'row',
    justifyContent: 'flex-start',
    flexWrap: 'wrap',
    gap: 12,
  },
  modalPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#e8f4fd',
    borderRadius: 20,
    paddingVertical: 10,
    paddingHorizontal: 16,
    gap: 8,
    borderWidth: 1,
    borderColor: '#cce0f5',
    minWidth: 130,
  },
  modalPillText: {
    fontSize: Platform.select({
      ios: 14,
      default: 15,
    }),
    fontWeight: '600',
    color: '#2c3e50',
    fontFamily: 'NotoSans_600SemiBold',
  },
  modalPillPercentage: {
    fontSize: Platform.select({
      ios: 14,
      default: 16,
    }),
    fontWeight: '700',
    color: '#4a90e2',
    fontFamily: 'NotoSans_700Bold',
  },
});

