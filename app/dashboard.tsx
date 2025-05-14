import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity,
  FlatList, Alert
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { collection, addDoc, getDoc, deleteDoc, serverTimestamp, onSnapshot, query, orderBy, where, doc } from 'firebase/firestore';
import { db } from '../firebaseConfig';
import { getAuth } from 'firebase/auth';
import { SwipeListView } from 'react-native-swipe-list-view';

const auth = getAuth();

// export const metadata = {
//   title: "Dashboard"
// };

export default function Dashboard() {
  const [menuVisible, setMenuVisible] = useState(false);
  const [chats, setChats] = useState<any[]>([]);
  const [userName, setUserName] = useState('');
  const userInitial = userName ? userName.charAt(0).toUpperCase() : '?';

  useEffect(() => {
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
      orderBy("createdAt", "desc")
    );

    const unsubscribe = onSnapshot(q, (snapshot) => {
      const chatData = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));
      setChats(chatData);
    });

    return () => unsubscribe();
  }, []);

  const handleNewChat = async () => {
    try {
      const user = auth.currentUser;
      if (!user) throw new Error("User not authenticated.");

      const docRef = await addDoc(collection(db, "chats"), {
        title: "New Chat",
        userId: user.uid,
        createdAt: serverTimestamp()
      });

      // Step 2: Add bot welcome message
      await addDoc(collection(db, `chats/${docRef.id}/messages`), {
        text: "Hi there! How can I assist you?",
        createdAt: serverTimestamp(),
        user: "AI Bot",
        userId: user.uid,
        sender: "bot"
      });

      router.push(`/chat/${docRef.id}`);
    } catch (error) {
      Alert.alert("Error", "Failed to create chat.");
    }
  };

  const openChat = (chat: any) => {
    router.push(`/chat/${chat.id}`);
  };

  const handleDeleteChat = async (chatId: string) => {
    try {
      await deleteDoc(doc(db, "chats", chatId));
      // Optionally: delete subcollection `messages` manually (Firebase doesn't auto-delete subcollections)
      // You’d need recursive deletion via backend (Cloud Functions or Firebase CLI)
    } catch (error) {
      Alert.alert("Error", "Could not delete chat.");
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View>
          <TouchableOpacity style={styles.avatar} onPress={() => setMenuVisible(!menuVisible)}>
            <Text style={styles.avatarText}>{userInitial}</Text>
          </TouchableOpacity>
          {menuVisible && (
            <View style={styles.menu}>
              <TouchableOpacity onPress={() => router.push('/account')}>
                <Text style={styles.menuItem}>Account</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={() => Alert.alert("Settings clicked")}>
                <Text style={styles.menuItem}>Settings</Text>
              </TouchableOpacity>
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
            <TouchableOpacity
              style={styles.chatCard}
              onPress={() => openChat(item)}
              activeOpacity={0.9}
            >
              <Text style={styles.chatTitle}>{item.title}</Text>
              <Text style={styles.timestamp}>
                {item.createdAt?.toDate().toLocaleString() || "Unknown"}
              </Text>
            </TouchableOpacity>
          </View>
        )}
        renderHiddenItem={({ item }) => (
          <View style={styles.rowBack}>
            <TouchableOpacity
              style={styles.deleteButton}
              onPress={() => handleDeleteChat(item.id)}
            >
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
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f2f2f7', paddingTop: 50, paddingHorizontal: 20 },
  header: { flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 10 },
  avatar: {
    backgroundColor: '#cdd5ec',
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: { fontWeight: 'bold', color: '#3b3b3b', fontSize: 16 },
  menu: {
    backgroundColor: '#fff', borderRadius: 6, padding: 6,
    position: 'absolute', top: 45, left: 0, width: 120,
    borderWidth: 1, borderColor: '#ccc', zIndex: 10,
    shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 5,
    shadowOffset: { width: 0, height: 2 },
  },
  menuItem: { paddingVertical: 6, paddingHorizontal: 10, fontSize: 16 },
  headerTitle: { fontSize: 18, fontWeight: '600', marginTop: 5 },
  chatList: { marginTop: 10 },
  chatCard: {
    backgroundColor: '#d8eff5',
    padding: 14,
    borderWidth: 0.5,
    borderColor: '#bcd3df',
    flexDirection: 'row',
    justifyContent: 'space-between',
    borderRadius: 6,
  },
  chatTitle: { fontWeight: 'bold' },
  timestamp: { color: '#555' },
  rowFront: {
    backgroundColor: '#fff',           
    borderRadius: 6,
    marginBottom: 10,
    overflow: 'hidden',              
  },
  
  rowBack: {
    alignItems: 'center',
    backgroundColor: '#ff3b30',
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'flex-end',
    paddingRight: 20,
    borderRadius: 6,
    marginBottom: 10,
  },
  deleteButton: {
    alignItems: 'center',
    justifyContent: 'center',
    width: 75,
    height: '100%',
  },
  
  deleteText: {
    color: 'white',
    fontWeight: 'bold',
  },
});