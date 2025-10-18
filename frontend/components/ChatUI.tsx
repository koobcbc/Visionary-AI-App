// components/ChatUI.tsx
import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  KeyboardAvoidingView,
  Platform
} from 'react-native';

type Message = {
  id: string;
  text: string;
  sender: 'user' | 'bot';
};

const ChatUI: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', text: "Hello! How can I help you?", sender: "bot" },
  ]);
  const [inputText, setInputText] = useState<string>('');

  const sendMessage = () => {
    if (inputText.trim() === '') return;

    const newMessage: Message = {
      id: (messages.length + 1).toString(),
      text: inputText,
      sender: 'user',
    };

    setMessages([...messages, newMessage]);
    setInputText('');
  };

  const renderItem = ({ item }: { item: Message }) => (
    <View
      style={[
        styles.messageBubble,
        item.sender === 'user' ? styles.userBubble : styles.botBubble,
      ]}
    >
      <Text style={styles.messageText}>{item.text}</Text>
    </View>
  );

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <FlatList
        data={messages}
        renderItem={renderItem}
        keyExtractor={(item) => item.id}
        style={styles.chatArea}
        contentContainerStyle={{ paddingVertical: 10 }}
      />
      <View style={styles.inputContainer}>
        <TextInput
          placeholder="Type a message..."
          value={inputText}
          onChangeText={setInputText}
          style={styles.input}
        />
        <TouchableOpacity onPress={sendMessage} style={styles.sendButton}>
          <Text style={styles.sendButtonText}>Send</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
};

export default ChatUI;

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  chatArea: {
    flex: 1,
    paddingHorizontal: 10,
  },
  messageBubble: {
    padding: 10,
    borderRadius: 10,
    marginVertical: 5,
    maxWidth: '80%',
  },
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: '#DCF8C6',
  },
  botBubble: {
    alignSelf: 'flex-start',
    backgroundColor: '#E2E2E2',
  },
  messageText: {
    fontSize: 16,
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 10,
    borderTopWidth: 1,
    borderColor: '#ccc',
    alignItems: 'center',
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 20,
    paddingHorizontal: 15,
    paddingVertical: 8,
    marginRight: 10,
  },
  sendButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 10,
    paddingHorizontal: 15,
    borderRadius: 20,
  },
  sendButtonText: {
    color: 'white',
    fontWeight: 'bold',
  },
});