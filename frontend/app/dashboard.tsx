import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity,
  FlatList, Alert, TouchableWithoutFeedback, Keyboard, Modal
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import {
  collection, addDoc, getDoc, deleteDoc,
  getDocs, updateDoc, serverTimestamp, onSnapshot,
  query, orderBy, where, doc
} from 'firebase/firestore';
import { db } from '../firebaseConfig';
import { getAuth, signOut } from 'firebase/auth';
import { SwipeListView } from 'react-native-swipe-list-view';
import * as Location from 'expo-location';
import AsyncStorage from '@react-native-async-storage/async-storage';

const auth = getAuth();

export default function Dashboard() {
  const [menuVisible, setMenuVisible] = useState(false);
  const [chats, setChats] = useState<any[]>([]);
  const [userName, setUserName] = useState('');
  const [profileIncomplete, setProfileIncomplete] = useState(false);
  const [activeTab, setActiveTab] = useState<'skin' | 'dental'>('skin');
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const userInitial = userName ? userName.charAt(0).toUpperCase() : '?';
  const unsubscribeRef = useRef<any>(null);

  useEffect(() => {
    // Load saved tab preference
    const loadTabPreference = async () => {
      try {
        const savedTab = await AsyncStorage.getItem('activeTab');
        if (savedTab === 'skin' || savedTab === 'dental') {
          setActiveTab(savedTab);
        }
      } catch (error) {
        console.log('Error loading tab preference:', error);
      }
    };
    loadTabPreference();

    (async () => {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission Denied', 'Location permission is required to use this feature.');
        return;
      }

      const location = await Location.getCurrentPositionAsync({});
      console.log("User location:", location.coords);
    })();

    const user = auth.currentUser;
    if (!user) return;

    const fetchUserName = async () => {
      const docRef = doc(db, "users", user.uid);
      const docSnap = await getDoc(docRef);
      if (docSnap.exists()) {
        const data = docSnap.data();
        setUserName(data.firstName || '');
        setProfileIncomplete(data.profileCreated !== true);
      }
    };
    fetchUserName();

    const q = query(
      collection(db, "chats"),
      where("userId", "==", user.uid),
      orderBy("last_message_at", "desc")
    );

    const unsubscribe = onSnapshot(q, (snapshot) => {
      const chatData = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
      setChats(chatData);
    });

    unsubscribeRef.current = unsubscribe;
    return () => unsubscribe();
  }, []);

  const handleLogout = async () => {
    try {
      if (unsubscribeRef.current) unsubscribeRef.current();
      await signOut(auth);
      await new Promise(res => setTimeout(res, 500));
      router.replace('/');
    } catch (error) {
      Alert.alert("Logout Failed", "An error occurred while logging out.");
    }
  };

  const saveTabPreference = async (tab: 'skin' | 'dental') => {
    try {
      await AsyncStorage.setItem('activeTab', tab);
    } catch (error) {
      console.log('Error saving tab preference:', error);
    }
  };

  const handleTabChange = (tab: 'skin' | 'dental') => {
    setActiveTab(tab);
    saveTabPreference(tab);
  };

  const handleNewChat = () => {
    setShowCategoryModal(true);
  };

  const createChat = async (category: 'skin' | 'dental') => {
    try {
      const user = auth.currentUser;
      if (!user) throw new Error("User not authenticated.");

      const docRef = await addDoc(collection(db, "chats"), {
        title: "New Chat",
        userId: user.uid,
        category: category,
        createdAt: serverTimestamp(),
        last_message_at: serverTimestamp(),
      });

      await addDoc(collection(db, `chats/${docRef.id}/messages`), {
        text: "Hi there! How can I assist you?",
        createdAt: serverTimestamp(),
        user: "AI Bot",
        userId: user.uid,
        sender: "bot"
      });

      await updateDoc(doc(db, "chats", docRef.id), {
        last_message_at: serverTimestamp()
      });

      // Switch to the selected category tab
      handleTabChange(category);
      setShowCategoryModal(false);
      router.push(`/chat/${docRef.id}`);
    } catch (error) {
      Alert.alert("Error", "Failed to create chat.");
    }
  };

  const openChat = (chat: any) => {
    router.push(`/chat/${chat.id}`);
  };

  // Filter chats by active category
  const filteredChats = chats.filter(chat => chat.category === activeTab);

  const handleDeleteChat = (chatId: string) => {
    Alert.alert(
      "Delete Chat",
      "Are you sure you want to delete this chat?",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: async () => {
            try {
              await deleteDoc(doc(db, "chats", chatId));
            } catch (error) {
              Alert.alert("Error", "Could not delete chat.");
            }
          }
        }
      ],
      { cancelable: true }
    );
  };

  return (
    <TouchableWithoutFeedback onPress={() => { setMenuVisible(false); Keyboard.dismiss(); }}>
      <View style={styles.container}>
        <View style={styles.header}>
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
                <TouchableOpacity onPress={() => router.push('/account')}><Text style={styles.menuItem}>Account</Text></TouchableOpacity>
                <TouchableOpacity onPress={() => router.push('/settings')}><Text style={styles.menuItem}>Settings</Text></TouchableOpacity>
                <TouchableOpacity onPress={handleLogout}><Text style={styles.menuItem}>Logout</Text></TouchableOpacity>
              </View>
            )}
          </View>
          <Text style={styles.headerTitle}>Chats</Text>
          <TouchableOpacity onPress={handleNewChat}>
            <Ionicons name="add-circle-outline" size={28} color="#333" />
          </TouchableOpacity>
        </View>

        {/* Category Tabs */}
        <View style={styles.tabContainer}>
          <TouchableOpacity
            style={[styles.tab, activeTab === 'skin' && styles.activeTab]}
            onPress={() => handleTabChange('skin')}
          >
            <Ionicons 
              name="medical" 
              size={20} 
              color={activeTab === 'skin' ? '#fff' : '#2c3e50'} 
            />
            <Text style={[styles.tabText, activeTab === 'skin' && styles.activeTabText]}>
              Skin
            </Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.tab, activeTab === 'dental' && styles.activeTab]}
            onPress={() => handleTabChange('dental')}
          >
            <Ionicons 
              name="happy" 
              size={20} 
              color={activeTab === 'dental' ? '#fff' : '#2c3e50'} 
            />
            <Text style={[styles.tabText, activeTab === 'dental' && styles.activeTabText]}>
              Dental
            </Text>
          </TouchableOpacity>
        </View>

        <SwipeListView
          data={filteredChats}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <View style={styles.rowFront}>
              <TouchableOpacity style={styles.chatCard} onPress={() => openChat(item)} activeOpacity={0.9}>
                <Text style={styles.chatTitle}>{item.title}</Text>
                <Text style={styles.timestamp}>{item.last_message_at?.toDate().toLocaleString() || "Unknown"}</Text>
              </TouchableOpacity>
            </View>
          )}
          renderHiddenItem={({ item }) => (
            <View style={styles.rowBack}>
              <TouchableOpacity style={styles.deleteButton} onPress={() => handleDeleteChat(item.id)}>
                <Text style={styles.deleteText}>Delete</Text>
              </TouchableOpacity>
            </View>
          )}
          rightOpenValue={-75}
          disableRightSwipe
          previewRowKey={'0'}
          previewOpenValue={-40}
          previewOpenDelay={300}
        />

        {/* Category Selection Modal */}
        <Modal
          visible={showCategoryModal}
          transparent={true}
          animationType="fade"
          onRequestClose={() => setShowCategoryModal(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>Choose Chat Category</Text>
              <Text style={styles.modalSubtitle}>What type of consultation do you need?</Text>
              
              <TouchableOpacity
                style={styles.categoryOption}
                onPress={() => createChat('skin')}
              >
                <Ionicons name="medical" size={24} color="#2c3e50" />
                <View style={styles.categoryTextContainer}>
                  <Text style={styles.categoryTitle}>Skin Consultation</Text>
                  <Text style={styles.categoryDescription}>Dermatology and skin-related issues</Text>
                </View>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.categoryOption}
                onPress={() => createChat('dental')}
              >
                <Ionicons name="happy" size={24} color="#2c3e50" />
                <View style={styles.categoryTextContainer}>
                  <Text style={styles.categoryTitle}>Dental Consultation</Text>
                  <Text style={styles.categoryDescription}>Dental and oral health issues</Text>
                </View>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.cancelButton}
                onPress={() => setShowCategoryModal(false)}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
            </View>
          </View>
        </Modal>
      </View>
    </TouchableWithoutFeedback>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f9fafe', paddingHorizontal: 20 },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 12 },
  avatar: { backgroundColor: '#9db2f2', width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center', position: 'relative' },
  avatarText: { fontWeight: '700', color: '#fff', fontSize: 16 },
  incompleteIndicator: { position: 'absolute', top: -2, right: -2, backgroundColor: '#fff', borderRadius: 8, width: 16, height: 16, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: '#e74c3c' },
  menu: { backgroundColor: '#ffffff', borderRadius: 8, paddingVertical: 8, paddingHorizontal: 10, position: 'absolute', top: 48, left: 0, width: 140, zIndex: 10, shadowColor: '#000', shadowOpacity: 0.08, shadowRadius: 6, shadowOffset: { width: 0, height: 4 }, borderWidth: 1, borderColor: '#e2e6ea' },
  menuItem: { paddingVertical: 8, fontSize: 16, color: '#333' },
  incompleteMenuItem: { color: '#e74c3c', fontWeight: 'bold' },
  headerTitle: { fontSize: 18, fontWeight: '700', color: '#2c3e50' },
  
  // Tab styles
  tabContainer: { flexDirection: 'row', marginVertical: 16, backgroundColor: '#ffffff', borderRadius: 12, padding: 4 },
  tab: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 12, paddingHorizontal: 16, borderRadius: 8 },
  activeTab: { backgroundColor: '#2c3e50' },
  tabText: { fontSize: 16, fontWeight: '600', color: '#2c3e50', marginLeft: 8 },
  activeTabText: { color: '#fff' },
  
  // Chat styles
  chatCard: { backgroundColor: '#eaf4fb', padding: 16, borderRadius: 10, justifyContent: 'space-between', flexDirection: 'column' },
  chatTitle: { fontSize: 16, fontWeight: '600', color: '#2c3e50', marginBottom: 6 },
  timestamp: { fontSize: 12, color: '#7f8c8d' },
  rowFront: { backgroundColor: '#ffffff', borderRadius: 10, marginBottom: 12, overflow: 'hidden', shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 3, shadowOffset: { width: 0, height: 2 } },
  rowBack: { alignItems: 'center', backgroundColor: '#ff3b30', flex: 1, flexDirection: 'row', justifyContent: 'flex-end', paddingRight: 20, borderRadius: 10, marginBottom: 12 },
  deleteButton: { alignItems: 'center', justifyContent: 'center', width: 75, height: '100%' },
  deleteText: { color: '#fff', fontWeight: 'bold' },
  
  // Modal styles
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0, 0, 0, 0.5)', justifyContent: 'center', alignItems: 'center' },
  modalContent: { backgroundColor: '#ffffff', borderRadius: 16, padding: 24, marginHorizontal: 20, width: '90%', maxWidth: 400 },
  modalTitle: { fontSize: 20, fontWeight: 'bold', color: '#2c3e50', textAlign: 'center', marginBottom: 8 },
  modalSubtitle: { fontSize: 16, color: '#7f8c8d', textAlign: 'center', marginBottom: 24 },
  categoryOption: { flexDirection: 'row', alignItems: 'center', paddingVertical: 16, paddingHorizontal: 16, backgroundColor: '#f8f9fa', borderRadius: 12, marginBottom: 12 },
  categoryTextContainer: { marginLeft: 16, flex: 1 },
  categoryTitle: { fontSize: 16, fontWeight: '600', color: '#2c3e50', marginBottom: 4 },
  categoryDescription: { fontSize: 14, color: '#7f8c8d' },
  cancelButton: { marginTop: 16, paddingVertical: 12, alignItems: 'center' },
  cancelButtonText: { fontSize: 16, color: '#7f8c8d' },
});
