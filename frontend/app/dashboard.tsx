import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity,
  FlatList, Alert, TouchableWithoutFeedback, Keyboard, Image, ImageBackground
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { router, useLocalSearchParams } from 'expo-router';
import {
  collection, addDoc, getDoc, deleteDoc,
  getDocs, updateDoc, serverTimestamp, onSnapshot,
  query, orderBy, where, doc
} from 'firebase/firestore';
import { db } from '../firebaseConfig';
import { getAuth, signOut } from 'firebase/auth';
import { SwipeListView } from 'react-native-swipe-list-view';
import * as Location from 'expo-location';

const logo = require('../assets/images/transparent-logo.png');
const skinImage = require('../assets/images/skin_no_bg.png');
const dentalImage = require('../assets/images/dental_no_bg.png');

const auth = getAuth();

export default function Dashboard() {
  const params = useLocalSearchParams();
  const category = (params.category as 'skin' | 'dental') || 'skin';
  
  const [menuVisible, setMenuVisible] = useState(false);
  const [chats, setChats] = useState<any[]>([]);
  const [userName, setUserName] = useState('');
  const [profileIncomplete, setProfileIncomplete] = useState(false);
  const userInitial = userName ? userName.charAt(0).toUpperCase() : '?';
  const unsubscribeRef = useRef<any>(null);

  useEffect(() => {
    // Validate category parameter
    if (category !== 'skin' && category !== 'dental') {
      router.replace('/category-selection');
      return;
    }

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
      where("category", "==", category),
      orderBy("last_message_at", "desc")
    );

    const unsubscribe = onSnapshot(q, (snapshot) => {
      const chatData = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
      setChats(chatData);
    });

    unsubscribeRef.current = unsubscribe;
    return () => unsubscribe();
  }, [category]);

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

  const handleNewChat = async () => {
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

      router.push(`/chat/${docRef.id}`);
    } catch (error) {
      Alert.alert("Error", "Failed to create chat.");
    }
  };

  const openChat = (chat: any) => {
    router.push(`/chat/${chat.id}`);
  };

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
          <TouchableOpacity 
            style={styles.backButton} 
            onPress={() => router.push('/category-selection')}
          >
            <Ionicons name="arrow-back" size={24} color="#4a90e2" />
          </TouchableOpacity>
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
          <TouchableOpacity 
            style={styles.newChatCard} 
            onPress={handleNewChat}
            activeOpacity={0.7}
          >
            <Ionicons name="add-circle-outline" size={20} color="#4a90e2" />
            <Text style={styles.newChatText}>+ New Chat</Text>
          </TouchableOpacity>

          {chats.length === 0 ? (
            <View style={styles.emptyStateContainer}>
              <View style={styles.emptyIconContainer}>
                <Ionicons name="chatbubble-ellipses-outline" size={64} color="#2c3e50" style={styles.emptyIcon} />
              </View>
              <Text style={styles.emptyTitle}>No chats yet</Text>
              <Text style={styles.emptySubtitle}>Start a conversation to get personalized guidance.</Text>
              <TouchableOpacity style={styles.emptyCtaButton} onPress={handleNewChat} activeOpacity={0.9}>
                <Ionicons name="add-circle" size={20} color="#fff" />
                <Text style={styles.emptyCtaText}>Start a Chat</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <SwipeListView
              style={{ flex: 1 }}
              contentContainerStyle={{ paddingVertical: 4 }}
              data={chats}
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
          )}
          
          {/* Background Image */}
          <Image
            source={category === 'skin' ? skinImage : dentalImage}
            style={styles.backgroundImage}
            resizeMode="cover"
          />
        </View>
      </View>
    </TouchableWithoutFeedback>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#DBEDEC', paddingHorizontal: 20 },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 20, paddingTop: 20, zIndex: 1000, position: 'relative' },
  backButton: {
    padding: 4,
    marginRight: 8,
  },
  logo: {
    width: 140,
    height: 60,
  },
  headerSpacer: { flex: 1 },
  avatar: { backgroundColor: '#4a90e2', width: 48, height: 48, borderRadius: 24, alignItems: 'center', justifyContent: 'center', position: 'relative' },
  avatarText: { fontWeight: '700', color: '#fff', fontSize: 20 },
  incompleteIndicator: { position: 'absolute', top: -2, right: -2, backgroundColor: '#fff', borderRadius: 8, width: 16, height: 16, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: '#e74c3c' },
  menu: { backgroundColor: '#ffffff', borderRadius: 8, paddingVertical: 8, paddingHorizontal: 10, position: 'absolute', top: 48, right: 0, width: 180, zIndex: 9999, elevation: 16, shadowColor: '#000', shadowOpacity: 0.12, shadowRadius: 8, shadowOffset: { width: 0, height: 6 }, borderWidth: 1, borderColor: '#e2e6ea' },
  menuItem: { paddingVertical: 8, fontSize: 18, color: '#333' },
  incompleteMenuItem: { color: '#e74c3c', fontWeight: 'bold' },
  
  // New Chat Card
  newChatCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#ffffff',
    borderWidth: 2,
    borderStyle: 'dashed',
    borderColor: '#4a90e2',
    borderRadius: 10,
    paddingVertical: 16,
    paddingHorizontal: 20,
    marginBottom: 16,
    gap: 8,
  },
  newChatText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#4a90e2',
  },
  
  // Chat styles
  chatCard: { backgroundColor: '#e8f4fd', padding: 16, borderRadius: 10, justifyContent: 'space-between', flexDirection: 'column', minHeight: 96 },
  chatTitle: { fontSize: 18, fontWeight: '600', color: '#2c3e50', marginBottom: 6 },
  timestamp: { fontSize: 14, color: '#7f8c8d' },
  rowFront: { backgroundColor: '#ffffff', borderRadius: 10, marginBottom: 12, overflow: 'hidden', shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 3, shadowOffset: { width: 0, height: 2 } },
  rowBack: { alignItems: 'center', backgroundColor: '#ff3b30', flex: 1, flexDirection: 'row', justifyContent: 'flex-end', paddingRight: 20, borderRadius: 10, marginBottom: 12 },
  deleteButton: { alignItems: 'center', justifyContent: 'center', width: 75, height: '100%' },
  deleteText: { color: '#fff', fontWeight: 'bold' },

  // Empty state
  emptyStateContainer: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  emptyIconContainer: { width: 96, height: 96, borderRadius: 48, backgroundColor: 'rgba(74, 144, 226, 0.1)', alignItems: 'center', justifyContent: 'center', marginBottom: 16 },
  emptyIcon: { opacity: 0.6 },
  emptyTitle: { fontSize: 18, fontWeight: '700', color: '#2c3e50', marginBottom: 6 },
  emptySubtitle: { fontSize: 14, color: '#7f8c8d', marginBottom: 16, textAlign: 'center', paddingHorizontal: 20 },
  emptyCtaButton: { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: '#4a90e2', paddingVertical: 12, paddingHorizontal: 16, borderRadius: 10 },
  emptyCtaText: { color: '#fff', fontWeight: '600', marginLeft: 8 },

  // List panel wrapper
  listPanel: { 
    flex: 1, 
    backgroundColor: '#ffffff', 
    borderRadius: 12, 
    padding: 12, 
    shadowColor: '#000', 
    shadowOpacity: 0.06, 
    shadowRadius: 6, 
    shadowOffset: { width: 0, height: 3 }, 
    borderWidth: 1, 
    borderColor: '#e0e8f0',
    position: 'relative',
    overflow: 'hidden',
  },
  backgroundImage: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    width: '100%',
    height: 200,
    opacity: 0.5,
    zIndex: -1,
  },
});
