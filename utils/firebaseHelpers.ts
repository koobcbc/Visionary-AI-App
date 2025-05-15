import { db } from '../firebaseConfig';
import { collection, addDoc, getDocs } from 'firebase/firestore';

export const sendMessageToChat = async (chatId: string, message: string) => {
  const chatRef = collection(db, 'chats', chatId, 'messages');
  await addDoc(chatRef, {
    text: message,
    createdAt: new Date().toISOString(),
  });
};

export const fetchMessages = async (chatId: string) => {
  const chatRef = collection(db, 'chats', chatId, 'messages');
  const snapshot = await getDocs(chatRef);
  return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
};