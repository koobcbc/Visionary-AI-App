import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, TextInput, FlatList, StyleSheet,
  KeyboardAvoidingView, Platform, Image, TouchableOpacity, Animated, Dimensions, ActionSheetIOS, Alert, TouchableWithoutFeedback, Keyboard, ScrollView, Modal
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { collection, addDoc, query, orderBy, onSnapshot, serverTimestamp, updateDoc, deleteDoc, doc, Timestamp } from 'firebase/firestore';
import { db, auth, storage } from '../../../firebaseConfig';
import { ref, uploadBytes, getDownloadURL } from 'firebase/storage';
import { Ionicons, MaterialIcons, Feather } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import SummaryScreen from './SummaryScreen';
import DoctorsScreen from './DoctorsScreen';
import Markdown from 'react-native-markdown-display';
const logo = require('../../../assets/images/transparent-logo-v.png');
const headerLogo = require('../../../assets/images/transparent-logo.png');
const doctorIcon = require('../../../assets/images/doctor.png');

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

type Summary = {
  diagnosis: string;
  symptoms: string[];
  causes: string[];
  treatments: string[];
  specialty: string;
}

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
  const [settingsVisible, setSettingsVisible] = useState(false);
  const settingsSlideAnim = useRef(new Animated.Value(300)).current;
  const [chatTitle, setChatTitle] = useState('Chat');
  const [chatCategory, setChatCategory] = useState<'skin' | 'dental' | null>(null);
  const [newTitle, setNewTitle] = useState('');
  const [summary, setSummary] = useState<Summary>({
    diagnosis: "Not enough information",
    symptoms: [],
    causes: [],
    treatments: [],
    specialty: ""
  });
  const [isEditingTitle, setIsEditingTitle] = useState(false);

  useEffect(() => {
    const keyboardDidShowListener = Keyboard.addListener('keyboardDidShow', () => {
      console.log("keyboard showing")
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
      console.log("setting messages", msgs)
    });
    return () => unsubscribe();
  }, [chatId]);

  useEffect(() => {
    if (!chatId) return;
    const chatRef = doc(db, 'chats', chatId);
  
    const unsubscribe = onSnapshot(chatRef, (docSnap) => {
      if (docSnap.exists()) {
        const data = docSnap.data();
        setChatTitle(data.title || 'Chat');
        setChatCategory(data.category || null);
      }
    });
  
    return () => unsubscribe();
  }, [chatId]);

  useEffect(() => {
    if (flatListRef.current) {
      flatListRef.current.scrollToEnd({ animated: true });
    }
  }, [messages])

  // Debounce summary generation to prevent infinite loops
  const summaryTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastMessageCountRef = useRef(0);
  const isGeneratingSummaryRef = useRef(false);
  
  useEffect(() => {
    // Only generate summary if message count actually increased (new messages added)
    // and we're not already generating a summary
    if (messages.length <= lastMessageCountRef.current || isGeneratingSummaryRef.current) {
      lastMessageCountRef.current = messages.length;
      return;
    }
    
    // Clear existing timeout
    if (summaryTimeoutRef.current) {
      clearTimeout(summaryTimeoutRef.current);
    }
    
    // Only generate summary if there are bot messages and enough messages to summarize
    const hasBotMessages = messages.some(m => m.sender === 'bot' && m.text);
    if (!hasBotMessages || messages.length < 2) {
      lastMessageCountRef.current = messages.length;
      return;
    }
    
    // Debounce: wait 5 seconds after last message before generating summary
    // This prevents rapid-fire API calls
    summaryTimeoutRef.current = setTimeout(async () => {
      if (isGeneratingSummaryRef.current) return; // Prevent concurrent calls
      isGeneratingSummaryRef.current = true;
      try {
        await generateSummary(messages);
      } finally {
        isGeneratingSummaryRef.current = false;
        lastMessageCountRef.current = messages.length;
      }
    }, 5000); // Increased to 5 seconds to reduce API calls
    
    return () => {
      if (summaryTimeoutRef.current) {
        clearTimeout(summaryTimeoutRef.current);
      }
    };
  }, [messages])

  // Check if summary has valid data
  const hasValidSummary = () => {
    return summary.diagnosis && 
           summary.diagnosis !== "Not enough information" && 
           summary.diagnosis.trim() !== "";
  };

  const openDrawer = () => {
    Keyboard.dismiss();
    setDrawerVisible(true);
    // Set doctors to be expanded when drawer opens
    setExpandedCard('doctors');
    Animated.timing(slideAnim, { toValue: 0, duration: 300, useNativeDriver: true }).start();
  };

  const closeDrawer = () => {
    Animated.timing(slideAnim, { toValue: 300, duration: 300, useNativeDriver: true }).start(() => {
      setDrawerVisible(false);
      setExpandedCard(null); // Reset expanded card when closing
    });
  };

  const BACKEND_URL = 'https://supervisor-agent-139431081773.us-central1.run.app/api/v1/main';

  async function getGeminiResponse(msg: string, imageUrl?: string) {
    try {
      if (!auth.currentUser) {
        return "Please sign in to continue.";
      }

      // Get Firebase auth token
      const token = await auth.currentUser.getIdToken();
      
      // Determine speciality from chatCategory
      const speciality = chatCategory || 'skin'; // Default to 'skin' if not set
      
      const requestBody = {
        message: msg || '',
        image_url: imageUrl || '',
        user_id: auth.currentUser.uid,
        chat_id: chatId,
        type: imageUrl ? 'image' : 'text',
        speciality: speciality
      };

      console.log('🔵 Backend API Request:', {
        url: BACKEND_URL,
        method: 'POST',
        body: requestBody
      });

      const response = await fetch(BACKEND_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(requestBody)
      });

      console.log('🟢 Backend API Response Status:', response.status, response.statusText);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('🔴 Backend API Error Response:', errorText);
        throw new Error(`Backend API error: ${response.status} - ${errorText}`);
      }

      const responseText = await response.text();
      console.log('🟡 Backend API Raw Response:', responseText);
      
      let data;
      try {
        data = JSON.parse(responseText);
        console.log('🟢 Backend API Parsed JSON:', JSON.stringify(data, null, 2));
      } catch (parseError) {
        console.error('🔴 Backend API Response is not valid JSON:', parseError);
        console.log('🟡 Returning raw response text');
        return responseText || "Sorry, something went wrong.";
      }

      // Check various possible response formats
      if (data.response) {
        console.log('✅ Using data.response');
        return data.response;
      } else if (data.message) {
        console.log('✅ Using data.message');
        return data.message;
      } else if (data.text) {
        console.log('✅ Using data.text');
        return data.text;
      } else if (typeof data === 'string') {
        console.log('✅ Response is a string');
        return data;
      } else {
        console.warn('⚠️ Unknown response format, returning full data:', data);
        return JSON.stringify(data) || "Sorry, something went wrong.";
      }
    } catch (error) {
      console.error("API error:", error);
      return "Sorry, something went wrong.";
    }
  }

  const handleSend = async () => {
    if (!input.trim()) return;
    
    // Save user input locally for optimistic UI update
    const userMessageText = input;
    setInput(''); // Clear input immediately for better UX
    
    // Send to backend - backend will handle saving to Firestore
    // The Firestore listener will pick up the messages when backend saves them
    try {
      await getGeminiResponse(userMessageText);
      // Backend handles saving both user and bot messages to Firestore
      // Frontend just listens via onSnapshot to update UI
    } catch (error) {
      console.error('Error sending message:', error);
      // Optionally show error to user
      Alert.alert('Error', 'Failed to send message. Please try again.');
    }
  };

  const uploadImageAsync = async (uri: string, chatId: string) => {
    try {
      // Fetch the image as a blob for React Native
      const response = await fetch(uri);
      
      // Check if response is ok
      if (!response.ok) {
        throw new Error(`Failed to fetch image: ${response.status}`);
      }
      
      // Convert to blob
      const blob = await response.blob();
      
      const filename = `chats/${chatId}/${Date.now()}.jpg`;
      const storageRef = ref(storage, filename);
      await uploadBytes(storageRef, blob);
      return await getDownloadURL(storageRef);
    } catch (error) {
      console.error('Error uploading image:', error);
      throw error;
    }
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
      // Upload to Firebase Storage to get a publicly accessible URL
      // Backend requires image_url to be http, https, or gs:// (not base64 due to validation)
      const imageUrl = await uploadImageAsync(localUri, chatId);
      setImages(prev => [...prev, imageUrl]);
  
      // Update chat timestamp
      await updateDoc(doc(db, `chats/${chatId}`), {
        last_message_at: serverTimestamp()
      });
  
      // Send Firebase Storage URL to backend API
      // Backend will download from this URL and process the image
      // Backend will handle saving both user message (with image) and bot response to Firestore
      await getGeminiResponse('', imageUrl);
  
    } catch (error) {
      console.error("Image upload or analysis failed:", error);
      Alert.alert('Error', 'Failed to upload image. Please try again.');
    }
  };

  const renderExpandableCard = (title: string, key: 'summary' | 'doctors', Component: React.ComponentType<any>) => {
    const isSummary = key === 'summary';
    const canExpand = isSummary ? hasValidSummary() : true;
    const isNoSummary = isSummary && !canExpand;
    
    return (
      <View style={[
        styles.card, 
        expandedCard === key && { height: screenHeight * 0.65 },
        isNoSummary && styles.cardNoSummary
      ]}> 
        <TouchableOpacity 
          onPress={() => {
            if (canExpand) {
              setExpandedCard(prev => prev === key ? null : key);
            } else {
              Alert.alert(
                "No Summary Available",
                "There's no summary yet. Please continue your conversation to generate a summary."
              );
            }
          }}
          disabled={!canExpand && expandedCard !== key}
          style={isNoSummary ? styles.cardHeaderNoSummary : undefined}
        >
          <View style={isNoSummary ? styles.cardTitleRow : undefined}>
            <Text style={[styles.cardTitle, isNoSummary && styles.cardTitleNoSummary]}>{title}</Text>
            {isNoSummary && (
              <Text style={styles.noSummaryText}>No summary available yet.</Text>
            )}
          </View>
          {
            expandedCard === key ? null : (
              !isNoSummary && (
                <Text style={styles.cardText}>
                  {isSummary 
                    ? 'AI-generated summary of your recent chat.'
                    : 'Find nearby providers for follow-up care.'}
                </Text>
              )
            )
          }
        </TouchableOpacity>
        {expandedCard === key && canExpand ? (
          <View style={styles.expandedCardContent}>
            <Component chatId={chatId} />
          </View>
        ) : (
          null
        )}
      </View>
    );
  };

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

  const openSettingsDrawer = () => {
    setSettingsVisible(true);
    Animated.timing(settingsSlideAnim, {
      toValue: 0,
      duration: 300,
      useNativeDriver: true,
    }).start();
  };
  
  const closeSettingsDrawer = () => {
    Animated.timing(settingsSlideAnim, {
      toValue: 300,
      duration: 300,
      useNativeDriver: true,
    }).start(() => setSettingsVisible(false));
  };

  const renameChatTitle = async () => {
    if (!newTitle.trim()) return;
  
    try {
      const chatRef = doc(db, 'chats', chatId);
      await updateDoc(chatRef, {
        title: newTitle.trim(),
        updatedAt: serverTimestamp(),
      });
  
      // Optional: Close settings drawer or show confirmation
      // setSettingsVisible(false);
      setNewTitle('');
      Alert.alert("Success", "Chat title has been updated.");
    } catch (error) {
      console.error("Failed to rename chat:", error);
    }
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
              router.replace('/dashboard')
            } catch (error) {
              Alert.alert("Error", "Could not delete chat.");
            }
          }
        }
      ],
      { cancelable: true }
    );
  };

  const generateSummary = async (msgs: Message[]) => {
    // Prevent summary generation if we're in the middle of a chat
    // Only generate summary for completed conversations
    const recentMessages = msgs.slice(-5); // Check last 5 messages
    const hasRecentBotMessage = recentMessages.some(m => m.sender === 'bot');
    const hasRecentUserMessage = recentMessages.some(m => m.sender === 'user');
    
    // If there's a recent user message, the conversation is still active - skip summary
    if (hasRecentUserMessage) {
      console.log('⏭️ Skipping summary - conversation still active');
      return;
    }
    
    const relevantTexts = msgs
      .filter(m => m.sender === 'bot' && m.text && !m.text.includes("[Image]") && !m.text.includes("Rate limit"))
      .map(m => m.text)
      .join('\n');
    
    // Don't generate summary if there's not enough content
    if (relevantTexts.length < 50) {
      console.log('⏭️ Skipping summary - not enough content');
      return;
    }
  
    console.log('🔄 Generating summary...');
    const geminiPrompt = `
      You're an assistant that summarizes skin lesion diagnosis conversations.
      
      Analyze the following conversation between a user and an AI model that classifies images of skin lesions. Based on the bot messages below, extract and organize the information into the following JSON format:
      
      {
        "diagnosis": "string",
        "symptoms": "list of string",
        "causes": "list of string",
        "treatments": "list of string",
        "specialty" : "string"
      }
      
      Here is the json of all the specialties taxonomy; Please use this information to select a specialty from this list; If there isn't enough information, leave specialty as blank.
      If any of the fields lack sufficient information, respond with "Not enough information" for that field (but symptoms, causes, and treatments are still going to be in a list).

      Give response just as a pure json.
      
      Conversation:
      ${relevantTexts}
      `;
  
    try {
      const responseText = await getGeminiResponse(geminiPrompt);

      console.log("📋 Summary responseText", responseText);
  
      if (
        !responseText.includes('{') ||
        !responseText.includes('}')
      ) {
        console.warn("⚠️ Summary response not JSON. Skipping.");
        return {
          diagnosis: "Not enough information",
          symptoms: [],
          causes: [],
          treatments: [],
          specialty: ""
        };
      }
      
      const cleanJson = responseText
        .replace(/```json|```/g, '') // Remove Markdown blocks
        .trim();

      const parsed: Summary = JSON.parse(cleanJson);
      setSummary(parsed);
      console.log('✅ Summary generated successfully');
      return parsed;
    } catch (err) {
      console.error("❌ Summary generation error:", err);
      return {
        diagnosis: "Not enough information",
        symptoms: ["Not enough information"],
        causes: ["Not enough information"],
        treatments: ["Not enough information"],
        specialty: ""
      };
    }
  };

  return (
      <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'} keyboardVerticalOffset={50}>
          <View style={{ flex: 1 }}>
            <View style={{ flex: 1 }}>
              {/* Header section */}
              <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
              <View style={styles.header}>
                <TouchableOpacity onPress={() => router.replace('/dashboard')}>
                  <Ionicons name="chevron-back" size={28} color="#000" />
                </TouchableOpacity>
                <View style={styles.headerLogoContainer}>
                  <Image source={headerLogo} style={styles.headerLogo} resizeMode="contain" />
                </View>
                <View style={styles.headerIcons}>
                  <TouchableOpacity onPress={openDrawer} style={styles.doctorIconButton}>
                    <Image source={doctorIcon} style={styles.doctorIcon} resizeMode="contain" />
                  </TouchableOpacity>
                </View>
              </View>
              </TouchableWithoutFeedback>

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
                  <View style={{ width: '100%', flexDirection: item.sender === 'bot' ? 'row' : 'row-reverse', alignItems: 'flex-start', marginBottom: 10 }}>
                    {item.sender === 'bot' && (
                      <Image source={logo} style={styles.botAvatar} />
                    )}
                
                    <View style={[styles.messageBubble, item.sender === 'bot' ? styles.botBubble : styles.userBubble]}>
                      {item.sender === 'bot' && (
                        <Text style={styles.sender}>Viscura</Text>
                      )}
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
                  <TouchableOpacity onPress={closeDrawer} style={{ marginRight: 12 }}>
                    <Ionicons name="chevron-forward" size={28} color="#000" />
                  </TouchableOpacity>
                  <Text style={styles.drawerTitle}>Back to Chat</Text>
                  <TouchableOpacity onPress={openSettingsDrawer} style={{ marginLeft: 'auto' }}>
                    <Ionicons name="settings-outline" size={24} color="#000" />
                  </TouchableOpacity>
                </View>

                <View style={{ flex: 1 }}>
                  {renderExpandableCard('Summary', 'summary', () => <SummaryScreen summary={summary} />)}
                  {renderExpandableCard('Doctors Near Me', 'doctors', () => <DoctorsScreen summary={summary} chatCategory={chatCategory} />)}
                  {/* <TouchableOpacity style={styles.leaveButton} onPress={() => {}}>
                    <Text style={styles.leaveButtonText}>Leave Chat</Text>
                  </TouchableOpacity> */}
                </View>
              </Animated.View>
            )}

            {settingsVisible && (
              <Animated.View style={[styles.settingsDrawer, { transform: [{ translateX: settingsSlideAnim }] }]}>
                <View style={styles.drawerHeader}>
                  <TouchableOpacity onPress={closeSettingsDrawer}>
                    <Ionicons name="chevron-back" size={28} color="#000" />
                  </TouchableOpacity>
                  <Text style={styles.drawerTitle}>Settings</Text>
                </View>

                <View style={{ paddingHorizontal: 8 }}>
                  <Text style={{ marginBottom: 4, fontWeight: '600' }}>Rename Chat</Text>
                  <TextInput
                    placeholder={chatTitle}
                    value={newTitle}
                    onChangeText={setNewTitle}
                    style={styles.renameInput}
                    placeholderTextColor="#999"
                  />
                  <TouchableOpacity style={styles.renameButton} onPress={renameChatTitle}>
                    <Text style={{ color: '#fff', fontWeight: '600' }}>Rename</Text>
                  </TouchableOpacity>

                  <View style={{ marginVertical: 20 }} />

                  <TouchableOpacity style={styles.leaveButton} onPress={() => handleDeleteChat(chatId)}>
                    <Text style={styles.leaveButtonText}>Leave Chat Room</Text>
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
    paddingVertical: 20,
    paddingTop: 20,
    paddingHorizontal: 16,
    backgroundColor: '#f9fafe',
  },
  headerLogoContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerLogo: {
    width: 140,
    height: 60,
  },
  headerIcons: {
    flexDirection: 'row',
    gap: 10,
    alignItems: 'center',
  },
  doctorIconButton: {
    padding: 4,
  },
  doctorIcon: {
    width: 28,
    height: 28,
  },
  container: { flex: 1, backgroundColor: '#f9fafe' },
  messages: { padding: 12, paddingBottom: 40 },
  botAvatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    marginRight: 8,
    marginTop: 6,
  },
  messageBubble: {
    maxWidth: '80%',
    padding: 12,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 5,
    shadowOffset: { width: 0, height: 1 },
  },
  userBubble: {
    backgroundColor: '#d2ecf9',
    alignSelf: 'flex-end',
    borderTopRightRadius: 0,
  },
  botBubble: {
    backgroundColor: '#f2f2f2',
    alignSelf: 'flex-start',
    borderTopLeftRadius: 0,
  },
  sender: {
    fontWeight: '600',
    color: '#888',
    fontSize: 12,
    marginBottom: 4,
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
    backgroundColor: '#f9fafe',
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
    backgroundColor: '#DBEDEC',
    borderRadius: 16,
    padding: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 6,
    elevation: 3,
    borderWidth: 1,
    borderColor: '#A5CCC9',
  },
  cardNoSummary: {
    minHeight: 50,
    paddingVertical: 12,
  },
  cardHeaderNoSummary: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  cardTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: 8,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 8,
  },
  cardTitleNoSummary: {
    marginBottom: 0,
  },
  noSummaryText: {
    fontSize: 14,
    color: '#666',
    fontStyle: 'italic',
    marginBottom: 0,
  },
  cardText: {
    fontSize: 14,
    color: '#2c3e50',
  },
  disabledText: {
    color: '#999',
    fontStyle: 'italic',
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
  settingsDrawer: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    right: 0,
    width: '100%',
    backgroundColor: '#f9fafe',
    borderLeftWidth: 1,
    borderLeftColor: '#ccc',
    padding: 16,
    zIndex: 15,
    elevation: 6,
  },
  renameInput: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 10,
    marginBottom: 12,
    backgroundColor: '#f9f9f9',
  },
  renameButton: {
    backgroundColor: '#2c3e50',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  titleInput: {
    paddingHorizontal: 4,
    paddingVertical: 2,
    borderBottomWidth: 1,
    borderColor: '#aaa',
    fontSize: 18,
    fontWeight: 'bold',
    minWidth: 100,
    maxWidth: 200,
    color: '#000',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.4)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  
  modalBox: {
    backgroundColor: '#fff',
    width: '80%',
    borderRadius: 12,
    padding: 24,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
    elevation: 5,
  },
  
  modalLabel: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
    color: '#333',
  },
  
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '100%',
  },
  
  cancelBtn: {
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 6,
    backgroundColor: '#f1f1f1',
  },
  
  saveBtn: {
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 6,
    backgroundColor: '#2c3e50',
  },
  titleInput: {
    borderBottomWidth: 1,
    borderColor: '#ccc',
    width: '100%',
    textAlign: 'center',
    fontSize: 16,
    paddingVertical: 8,
    marginBottom: 24,
    color: '#ccc',
  },
});