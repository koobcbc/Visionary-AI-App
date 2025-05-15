import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, TextInput, Button, FlatList, StyleSheet,
  KeyboardAvoidingView, Platform, TouchableWithoutFeedback,
  Keyboard, Image
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { useLocalSearchParams } from 'expo-router';
import Swiper from 'react-native-swiper';
import {
  collection, addDoc, query, orderBy, onSnapshot, serverTimestamp
} from 'firebase/firestore';
import { db, auth } from '../../../firebaseConfig';
import { Timestamp } from 'firebase/firestore';
import { GoogleGenerativeAI } from "@google/generative-ai";
import Constants from 'expo-constants';


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
//   const { chatId } = useLocalSearchParams();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [images, setImages] = useState<string[]>([]);

  const flatListRef = useRef<FlatList>(null);

  // console.log("user", auth.currentUser?.email)
  useEffect(() => {
    if (!chatId) return;

    const q = query(
      collection(db, `chats/${chatId}/messages`),
      orderBy('createdAt', 'asc')
    );

    const unsubscribe = onSnapshot(q, (snapshot) => {
      const msgs = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() } as Message));
      setMessages(msgs);
      flatListRef.current?.scrollToEnd({ animated: true });
    });

    return () => unsubscribe();
  }, [chatId]);

  useEffect(() => {
    if (messages.length > 0) {
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100); // slight delay to ensure layout has updated
    }
  }, [messages]);

  useEffect(() => {
    const showSub = Keyboard.addListener('keyboardDidShow', () => {
      requestAnimationFrame(() => {
        flatListRef.current?.scrollToEnd({ animated: false });
      });
    });
    return () => showSub.remove();
  }, []);

  const fakeBotResponse = (msg: string, isImage = false) =>
    isImage ? "Thanks for the image! We'll review it shortly." :
      msg.toLowerCase().includes("hello") ? "Hi there! How can I help you?" :
        "I'm a demo bot responding to your message.";

  // const app = initializeApp(firebaseConfig);
  // const functions = getFunctions(app);
  // const getGeminiResponse = httpsCallable(functions, "generateFromGemini");

  const API_KEY = Constants.expoConfig?.extra?.GEMINI_API_KEY;
  const genAI = new GoogleGenerativeAI(API_KEY);
  // Function to generate a response from Gemini Pro
  async function getGeminiResponse(msg: string, isImage = false) {
    try {
      const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash-001" });

      const chat = model.startChat({
        history: [
          {
            role: "user",
            parts: [{ text: "Hi" }],
          },
          {
            role: "model",
            parts: [{ text: "Hello! How can I assist you today?" }],
          },
        ],
      });

      const result = await chat.sendMessage(msg);
      const response = result.response;
      const text = response.text();
      console.log("Gemini says:", text);
      return text;
    } catch (error) {
      console.error("Error in Gemini API call:", error);
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
      try {
        const result = await getGeminiResponse(input);
        const response = result;
        console.log("Gemini response:", response);
        await addDoc(collection(db, `chats/${chatId}/messages`), {
          text: response,
          createdAt: serverTimestamp(),
          user: "AI Bot",
          userId: auth.currentUser?.uid,
          sender: "bot"
        });
      } catch (error) {
        console.error("Gemini callable error:", error);
      }
    }, 1200);
  };

  const handleSendImage = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 0.6,
    });

    if (!result.canceled && result.assets?.length > 0) {
      const uri = result.assets[0].uri;
      setImages(prev => [...prev, uri]);

      await addDoc(collection(db, `chats/${chatId}/messages`), {
        text: "[Image]",
        image: uri,
        createdAt: serverTimestamp(),
        user: auth.currentUser?.email || "anonymous",
        userId: auth.currentUser?.uid,
        sender: "user"
      });

      setTimeout(async () => {
        try {
          const result = await getGeminiResponse(`Please analyze this image: ${uri}`);
          const response = result;
          console.log("Gemini response:", response);

          await addDoc(collection(db, `chats/${chatId}/messages`), {
            text: response,
            createdAt: serverTimestamp(),
            user: "AI Bot",
            userId: auth.currentUser?.uid,
            sender: "bot"
          });
        } catch (error) {
          console.error("Gemini callable error:", error);
        }
      }, 1200);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={80}
    >
      <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
        <View style={{ flex: 1 }}>
          <FlatList
            ref={flatListRef}
            data={messages}
            keyExtractor={item => item.id}
            contentContainerStyle={styles.messages}
            renderItem={({ item }) => (
              <View style={[
                styles.messageBubble,
                item.sender === 'bot' ? styles.botBubble : styles.userBubble
              ]}>
                <Text style={styles.sender}>{item.user}</Text>
                {item.image && (
                  <Image source={{ uri: item.image }} style={styles.imagePreview} />
                )}
                <Text>{item.text}</Text>
              </View>
            )}
          />

          {images.length > 0 && (
            <View style={{ height: 200 }}>
              <Swiper showsButtons loop={false}>
                {images.map((imgUri, index) => (
                  <Image
                    key={index}
                    source={{ uri: imgUri }}
                    style={{ width: '100%', height: 180, borderRadius: 12 }}
                  />
                ))}
              </Swiper>
            </View>
          )}

          <View style={styles.inputContainer}>
            <Button title="📷" onPress={handleSendImage} />
            <TextInput
              style={styles.input}
              placeholder="Type a message..."
              value={input}
              onChangeText={setInput}
            />
            <Button title="Send" onPress={handleSend} />
          </View>
        </View>
      </TouchableWithoutFeedback>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f0f0f0' },
  messages: { padding: 10 },
  messageBubble: {
    maxWidth: '75%',
    padding: 10,
    borderRadius: 10,
    marginBottom: 8,
  },
  userBubble: {
    backgroundColor: '#d2ecf9',
    alignSelf: 'flex-end',
    marginLeft: 40,
    borderTopRightRadius: 0,
  },
  botBubble: {
    backgroundColor: '#ffe9c9',
    alignSelf: 'flex-start',
    marginRight: 40,
    borderTopLeftRadius: 0,
  },
  sender: {
    fontWeight: '600',
    marginBottom: 4,
    color: '#333'
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderTopWidth: 1,
    borderColor: '#ccc',
    backgroundColor: '#fff',
    padding: 10
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 20,
    paddingHorizontal: 15,
    height: 40,
    marginHorizontal: 10,
    backgroundColor: '#fff'
  },
  imagePreview: {
    width: 180,
    height: 180,
    borderRadius: 12,
    marginBottom: 6
  }
});