// Import the functions you need from the SDKs you need

import { initializeApp, getApps, getApp } from "firebase/app";
import 'firebase/auth/react-native';
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";
import { getStorage } from "firebase/storage";


// Your web app's Firebase configuration
export const firebaseConfig = {
  apiKey: "AIzaSyBlWHSZTflw67kCU2PyfiIuzUyvyuSOawg",
  authDomain: "adsp-34002-ip07-visionary-ai.firebaseapp.com",
  projectId: "adsp-34002-ip07-visionary-ai",
  storageBucket: "adsp-34002-ip07-visionary-ai.firebasestorage.app",
  messagingSenderId: "139431081773",
  appId: "1:139431081773:web:420dfd09d65abe7e0945a4"
};

const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApp();

// Initialize Firebase
export const storage = getStorage(app);

// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries
export const auth = getAuth(app);
export const db = getFirestore(app);

