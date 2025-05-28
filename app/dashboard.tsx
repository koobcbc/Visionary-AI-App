import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity,
  FlatList, Alert, TouchableWithoutFeedback, Keyboard
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

const auth = getAuth();

export default function Dashboard() {
  const [menuVisible, setMenuVisible] = useState(false);
  const [chats, setChats] = useState<any[]>([]);
  const [userName, setUserName] = useState('');
  const userInitial = userName ? userName.charAt(0).toUpperCase() : '?';
  const unsubscribeRef = useRef(null);

  useEffect(() => {
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

  const handleNewChat = async () => {
    try {
      const user = auth.currentUser;
      if (!user) throw new Error("User not authenticated.");

      const docRef = await addDoc(collection(db, "chats"), {
        title: "New Chat",
        userId: user.uid,
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
          <View>
            <TouchableOpacity style={styles.avatar} onPress={() => setMenuVisible(!menuVisible)}>
              <Text style={styles.avatarText}>{userInitial}</Text>
            </TouchableOpacity>
            {menuVisible && (
              <View style={styles.menu}>
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

        <SwipeListView
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
      </View>
    </TouchableWithoutFeedback>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f9fafe', paddingHorizontal: 20 },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 12 },
  avatar: { backgroundColor: '#9db2f2', width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  avatarText: { fontWeight: '700', color: '#fff', fontSize: 16 },
  menu: { backgroundColor: '#ffffff', borderRadius: 8, paddingVertical: 8, paddingHorizontal: 10, position: 'absolute', top: 48, left: 0, width: 140, zIndex: 10, shadowColor: '#000', shadowOpacity: 0.08, shadowRadius: 6, shadowOffset: { width: 0, height: 4 }, borderWidth: 1, borderColor: '#e2e6ea' },
  menuItem: { paddingVertical: 8, fontSize: 16, color: '#333' },
  headerTitle: { fontSize: 18, fontWeight: '700', color: '#2c3e50' },
  chatCard: { backgroundColor: '#eaf4fb', padding: 16, borderRadius: 10, justifyContent: 'space-between', flexDirection: 'column' },
  chatTitle: { fontSize: 16, fontWeight: '600', color: '#2c3e50', marginBottom: 6 },
  timestamp: { fontSize: 12, color: '#7f8c8d' },
  rowFront: { backgroundColor: '#ffffff', borderRadius: 10, marginBottom: 12, overflow: 'hidden', shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 3, shadowOffset: { width: 0, height: 2 } },
  rowBack: { alignItems: 'center', backgroundColor: '#ff3b30', flex: 1, flexDirection: 'row', justifyContent: 'flex-end', paddingRight: 20, borderRadius: 10, marginBottom: 12 },
  deleteButton: { alignItems: 'center', justifyContent: 'center', width: 75, height: '100%' },
  deleteText: { color: '#fff', fontWeight: 'bold' },
});
