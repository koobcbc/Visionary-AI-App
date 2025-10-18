// app/chat/[chatId]/_layout.tsx
import { Stack } from 'expo-router';

export default function ChatLayout() {
  return (
    <Stack screenOptions={{ headerShown: false }} />
  );
}