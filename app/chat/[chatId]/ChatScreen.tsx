import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, TextInput, FlatList, StyleSheet,
  KeyboardAvoidingView, Platform, Image, TouchableOpacity, Animated, Dimensions, ActionSheetIOS, Alert, TouchableWithoutFeedback, Keyboard, ScrollView
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { collection, addDoc, query, orderBy, onSnapshot, serverTimestamp, updateDoc, doc, Timestamp } from 'firebase/firestore';
import { db, auth, storage } from '../../../firebaseConfig';
import { GoogleGenerativeAI } from "@google/generative-ai";
import Constants from 'expo-constants';
import { ref, uploadBytes, getDownloadURL } from 'firebase/storage';
import { Ionicons, MaterialIcons, Feather } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import SummaryScreen from './SummaryScreen';
import DoctorsScreen from './DoctorsScreen';
import Markdown from 'react-native-markdown-display';

const { height: screenHeight } = Dimensions.get('window');

type Message = {
  id: string;
  text: string;
  user: string;
  userId: string;
  createdAt?: Timestamp;
  sender: 'user' | 'bot';
  image?: string;
};

export default function ChatScreen({ chatId }: { chatId: string }) {
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [expandedCard, setExpandedCard] = useState<'summary' | 'doctors' | null>(null);
  const slideAnim = useRef(new Animated.Value(300)).current;
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [images, setImages] = useState<string[]>([]);
  const flatListRef = useRef<FlatList>(null);
  const router = useRouter();
  const [showScrollToBottom, setShowScrollToBottom] = useState(false);
  const scrollOffset = useRef(0);
  const contentHeight = useRef(0);
  const listHeight = useRef(0);


  useEffect(() => {
    const keyboardDidShowListener = Keyboard.addListener('keyboardDidShow', () => {
      flatListRef.current?.scrollToEnd({ animated: false });
    });
  
    return () => {
      keyboardDidShowListener.remove();
    };
  }, []);
  
  useEffect(() => {
    if (!chatId) return;
    const q = query(collection(db, `chats/${chatId}/messages`), orderBy('createdAt', 'asc'));
    const unsubscribe = onSnapshot(q, (snapshot) => {
      const msgs = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() } as Message));
      setMessages(msgs);
    });
    return () => unsubscribe();
  }, [chatId]);

  useEffect(() => {
    if (flatListRef.current) {
      flatListRef.current.scrollToEnd({ animated: true });
    }
  }, [messages])

  const openDrawer = () => {
    setDrawerVisible(true);
    Animated.timing(slideAnim, { toValue: 0, duration: 300, useNativeDriver: true }).start();
  };

  const closeDrawer = () => {
    Animated.timing(slideAnim, { toValue: 300, duration: 300, useNativeDriver: true }).start(() => setDrawerVisible(false));
  };

  const API_KEY = Constants.expoConfig?.extra?.GEMINI_API_KEY;
  const genAI = new GoogleGenerativeAI(API_KEY);

  async function getGeminiResponse(msg: string) {
    try {
      const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash-001" });
      const chat = model.startChat({
        history: [
          { role: "user", parts: [{ text: "Hi" }] },
          { role: "model", parts: [{ text: "Hello! How can I assist you today?" }] },
        ]
      });
      const result = await chat.sendMessage(msg);
      return result.response.text();
    } catch (error) {
      console.error("Gemini error:", error);
      return "Sorry, something went wrong.";
    }
  }

  const handleSend = async () => {
    if (!input.trim()) return;
    await addDoc(collection(db, `chats/${chatId}/messages`), {
      text: input,
      createdAt: serverTimestamp(),
      user: auth.currentUser?.email || "anonymous",
      userId: auth.currentUser?.uid,
      sender: "user"
    });
    setInput('');
    setTimeout(async () => {
      const response = await getGeminiResponse(input);
      await addDoc(collection(db, `chats/${chatId}/messages`), {
        text: response,
        createdAt: serverTimestamp(),
        user: "AI Bot",
        userId: auth.currentUser?.uid,
        sender: "bot"
      });
    }, 1200);
  };

  const uploadImageAsync = async (uri: string, chatId: string) => {
    const response = await fetch(uri);
    const blob = await response.blob();
    const filename = `chats/${chatId}/${Date.now()}.jpg`;
    const storageRef = ref(storage, filename);
    await uploadBytes(storageRef, blob);
    return await getDownloadURL(storageRef);
  };

  const handleSendImage = () => {
    const options = ['Take Photo', 'Choose from Library', 'Cancel'];
    const cancelButtonIndex = 2;
  
    if (Platform.OS === 'ios') {
      ActionSheetIOS.showActionSheetWithOptions(
        {
          options,
          cancelButtonIndex,
        },
        async (buttonIndex) => {
          if (buttonIndex === 0) {
            await launchCamera();
          } else if (buttonIndex === 1) {
            await launchImageLibrary();
          }
        }
      );
    } else {
      Alert.alert(
        'Send Image',
        'Choose an option',
        [
          { text: 'Take Photo', onPress: launchCamera },
          { text: 'Choose from Library', onPress: launchImageLibrary },
          { text: 'Cancel', style: 'cancel' },
        ],
        { cancelable: true }
      );
    }
  };

  const launchCamera = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert("Permission Denied", "Camera permission is required to take photos.");
      return;
    }

    const result = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 0.6,
    });

    if (!result.canceled && result.assets?.length > 0) {
      await handleImageUpload(result.assets[0].uri);
    }
  };
  
  const launchImageLibrary = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 0.6,
    });
  
    if (!result.canceled && result.assets?.length > 0) {
      await handleImageUpload(result.assets[0].uri);
    }
  };

  const handleImageUpload = async (localUri: string) => {
    try {
      const imageUrl = await uploadImageAsync(localUri, chatId);
      setImages(prev => [...prev, imageUrl]);
  
      await addDoc(collection(db, `chats/${chatId}/messages`), {
        text: "[Image]",
        image: imageUrl,
        createdAt: serverTimestamp(),
        user: auth.currentUser?.email || "anonymous",
        userId: auth.currentUser?.uid,
        sender: "user"
      });
  
      await updateDoc(doc(db, `chats/${chatId}`), {
        last_message_at: serverTimestamp()
      });
  
      setTimeout(async () => {
        const response = await getGeminiResponse(`Please analyze this image: ${imageUrl}`);
        await addDoc(collection(db, `chats/${chatId}/messages`), {
          text: response,
          createdAt: serverTimestamp(),
          user: "AI Bot",
          userId: auth.currentUser?.uid,
          sender: "bot"
        });
  
        await updateDoc(doc(db, `chats/${chatId}`), {
          last_message_at: serverTimestamp()
        });
      }, 1200);
    } catch (uploadError) {
      console.error("Image upload failed:", uploadError);
    }
  };

  const renderExpandableCard = (title: string, key: 'summary' | 'doctors', Component: React.ComponentType<any>) => (
    <TouchableOpacity onPress={() => setExpandedCard(prev => prev === key ? null : key)}>
      <View style={[styles.card, expandedCard === key && { height: screenHeight * 0.65 }]}> 
        <Text style={styles.cardTitle}>{title}</Text>
        {expandedCard === key ? (
          <View style={styles.expandedCardContent}>
            <Component chatId={chatId} />
          </View>
        ) : (
          <Text style={styles.cardText}>{key === 'summary' ? 'AI-generated summary of your recent chat.' : 'Find nearby providers for follow-up care.'}</Text>
        )}
      </View>
    </TouchableOpacity>
  );

  const markdownStyles = {
    body: {
      fontSize: 15,
      color: '#2c3e50',
    },
    link: {
      color: '#1e90ff',
    },
    code_inline: {
      backgroundColor: '#eee',
      padding: 4,
      borderRadius: 4,
      fontFamily: 'Courier',
    },
    code_block: {
      backgroundColor: '#eee',
      padding: 10,
      borderRadius: 8,
      fontFamily: 'Courier',
    },
    heading1: {
      fontSize: 22,
      fontWeight: 'bold',
    },
    // add more if needed
  };

  console.log("flatListRef", flatListRef)
  return (
      <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'} keyboardVerticalOffset={50}>
          <View style={{ flex: 1 }}>
            <View style={{ flex: 1 }}>
              {/* Header section */}
              <View style={styles.header}>
                <TouchableOpacity onPress={() => router.replace('/dashboard')}>
                  <Ionicons name="chevron-back" size={28} color="#000" />
                </TouchableOpacity>
                <Text style={styles.chatTitle}>Chat</Text>
                <View style={styles.headerIcons}>
                  <TouchableOpacity onPress={openDrawer}>
                    <MaterialIcons name="more-vert" size={24} color="#000" />
                  </TouchableOpacity>
                </View>
              </View>

              {/* Message list */}
              <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
              <FlatList
                ref={flatListRef}
                data={messages}
                keyExtractor={item => item.id}
                contentContainerStyle={styles.messages}
                keyboardShouldPersistTaps="handled"
                onScroll={(event) => {
                  // Scroll tracking logic
                  const { layoutMeasurement, contentOffset, contentSize } = event.nativeEvent;

                  scrollOffset.current = contentOffset.y;
                  contentHeight.current = contentSize.height;
                  listHeight.current = layoutMeasurement.height;

                  const paddingToBottom = 30;
                  const isNearBottom = layoutMeasurement.height + contentOffset.y +300 >= contentSize.height - paddingToBottom;

                  setShowScrollToBottom(!isNearBottom);
                }}
                scrollEventThrottle={100}
                renderItem={({ item }) => (
                  <View style={{ width: '100%' }}>
                    <View style={[styles.messageBubble, item.sender === 'bot' ? styles.botBubble : styles.userBubble]}>
                      {item.sender === 'bot' ? <Text style={styles.sender}>{item.user}</Text> : null}
                      {item.image && <Image source={{ uri: item.image }} style={styles.imagePreview} />}
                      <Markdown style={markdownStyles}>{item.text}</Markdown>
                    </View>
                  </View>
                )}
                onContentSizeChange={() => {
                  flatListRef.current?.scrollToEnd({ animated: false });
                }}
                onLayout={(event) => {
                  listHeight.current = event.nativeEvent.layout.height;
                }}
              />
              </TouchableWithoutFeedback>

              {/* Scroll to bottom button */}
              {showScrollToBottom && (
                <TouchableOpacity
                onPress={() => {
                  if (flatListRef.current && contentHeight.current && listHeight.current) {
                    flatListRef.current.scrollToOffset({
                      offset: Math.max(contentHeight.current - listHeight.current, 0),
                      animated: true,
                    });
                  }
                }}
                  style={styles.scrollToBottomButton}
                >
                  <Ionicons name="chevron-down" size={28} color="#fff" />
                </TouchableOpacity>
              )}

              {/* Input field section */}
              <View style={styles.inputContainer}>
                <TouchableOpacity onPress={handleSendImage} style={styles.iconButton}>
                  <Feather name="camera" size={22} color="#333" />
                </TouchableOpacity>
                <TextInput style={styles.input} placeholder="Type a message..." value={input} onChangeText={setInput} />
                <TouchableOpacity onPress={handleSend} style={styles.sendButton}>
                  <Text style={styles.sendText}>Send</Text>
                </TouchableOpacity>
              </View>
            </View>

            {/* Drawer panel */}
            {drawerVisible && (
              <Animated.View style={[styles.drawer, { transform: [{ translateX: slideAnim }] }]}>
                <View style={styles.drawerHeader}>
                  <TouchableOpacity onPress={closeDrawer}>
                    <Ionicons name="chevron-forward" size={28} color="#000" />
                  </TouchableOpacity>
                  <Text style={styles.drawerTitle}>Back to Chat</Text>
                </View>

                <View style={{ flex: 1 }}>
                  {renderExpandableCard('Summary', 'summary', SummaryScreen)}
                  {renderExpandableCard('Doctors Near Me', 'doctors', DoctorsScreen)}
                  <TouchableOpacity style={styles.leaveButton} onPress={() => {}}>
                    <Text style={styles.leaveButtonText}>Leave Chat</Text>
                  </TouchableOpacity>
                </View>
              </Animated.View>
            )}
          </View>
      </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: '#f9fafe',
  },
  chatTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#000',
  },
  headerIcons: {
    flexDirection: 'row',
    gap: 10,
  },
  container: { flex: 1, backgroundColor: '#f9fafe' },
  messages: { padding: 12, paddingBottom: 40 },
  messageBubble: {
    maxWidth: '80%',
    padding: 12,
    borderRadius: 12,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 5,
    shadowOffset: { width: 0, height: 2 },
  },
  userBubble: {
    backgroundColor: '#d2ecf9',
    alignSelf: 'flex-end',
    marginLeft: 50,
    borderTopRightRadius: 0,
    paddingTop: 6,
    paddingBottom: 6
  },
  botBubble: {
    backgroundColor: '#ffe9c9',
    alignSelf: 'flex-start',
    marginRight: 50,
    borderTopLeftRadius: 0,
  },
  sender: {
    fontWeight: '600',
    marginBottom: 4,
    color: '#333'
  },
  messageText: {
    fontSize: 15,
    color: '#2c3e50'
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderTopWidth: 1,
    borderColor: '#ddd',
    backgroundColor: '#fff',
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 25,
    paddingHorizontal: 15,
    height: 40,
    marginHorizontal: 10,
    backgroundColor: '#fff',
    color: '#000'
  },
  imagePreview: {
    width: 200,
    height: 200,
    borderRadius: 12,
    marginTop: 6,
    marginBottom: 4
  },
  iconButton: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButton: {
    backgroundColor: '#2c3e50',
    borderRadius: 20,
    paddingVertical: 8,
    paddingHorizontal: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  
  sendText: {
    color: '#fff',
    fontWeight: '600',
  },
  drawer: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    right: 0,
    width: '100%',
    backgroundColor: '#fff',
    borderLeftWidth: 1,
    borderLeftColor: '#ccc',
    padding: 16,
    zIndex: 10,
    elevation: 5,
  },
  
  drawerHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  
  drawerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginLeft: 10,
  },
  
  drawerContent: {
    flex: 1,
  },
  
  drawerItem: {
    fontSize: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderColor: '#eee',
  },
  card: {
    backgroundColor: '#f1f1f1',
    borderRadius: 16,
    padding: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 6,
    elevation: 3,
  },
  
  cardTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  
  cardText: {
    fontSize: 14,
    color: '#555',
  },
  
  leaveButton: {
    backgroundColor: '#ef5350',
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 20,
  },
  
  leaveButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  expandedCardContent: {
    flex: 1,
    marginTop: 12,
    padding: 8,
    backgroundColor: '#fff',
    borderRadius: 12,
  },
  scrollToBottomButton: {
    position: 'absolute',
    right: 20,
    bottom: 90,
    backgroundColor: '#2c3e50',
    borderRadius: 30,
    width: 48,
    height: 48,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 5,
    zIndex: 10,
  },
});