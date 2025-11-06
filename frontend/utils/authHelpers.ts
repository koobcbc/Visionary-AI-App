import { Platform } from 'react-native';
import { 
  GoogleAuthProvider, 
  OAuthProvider,
  signInWithCredential,
  signInWithPopup,
  User
} from 'firebase/auth';
import { auth, db } from '../firebaseConfig';
import { doc, getDoc, setDoc, serverTimestamp } from 'firebase/firestore';
import * as AuthSession from 'expo-auth-session';
import * as AppleAuthentication from 'expo-apple-authentication';
import * as Crypto from 'expo-crypto';
import * as WebBrowser from 'expo-web-browser';

// Configure WebBrowser for OAuth
WebBrowser.maybeCompleteAuthSession();

// Get OAuth client IDs from environment variables
// These should be configured in Firebase Console > Authentication > Sign-in method
const GOOGLE_CLIENT_ID = process.env.EXPO_PUBLIC_GOOGLE_CLIENT_ID || '';

// OAuth configuration for Google
const googleDiscovery = {
  authorizationEndpoint: 'https://accounts.google.com/o/oauth2/v2/auth',
  tokenEndpoint: 'https://oauth2.googleapis.com/token',
  revocationEndpoint: 'https://oauth2.googleapis.com/revoke',
};

interface SocialAuthResult {
  user: User;
  isNewUser: boolean;
}

/**
 * Sign in with Google
 */
export async function signInWithGoogle(): Promise<SocialAuthResult> {
  try {
    if (Platform.OS === 'web') {
      // Web: Use Firebase's signInWithPopup
      const provider = new GoogleAuthProvider();
      try {
        const result = await signInWithPopup(auth, provider);
        const isNewUser = result.user.metadata.creationTime === result.user.metadata.lastSignInTime;
        
        // Save user to Firestore if new user
        if (isNewUser) {
          await saveUserToFirestore(result.user);
        }
        
        return { user: result.user, isNewUser };
      } catch (popupError: any) {
        // Check if user closed the popup (cancellation)
        if (popupError.code === 'auth/popup-closed-by-user' || 
            popupError.code === 'auth/cancelled-popup-request' ||
            popupError.message?.includes('popup') && popupError.message?.includes('closed')) {
          const cancelError: any = new Error('SIGN_IN_CANCELLED');
          cancelError.isCancellation = true;
          throw cancelError;
        }
        throw popupError;
      }
    } else {
      // Native: Use expo-auth-session with OAuth implicit flow (token response)
      // Note: For production, consider using a backend server for code exchange
      if (!GOOGLE_CLIENT_ID) {
        throw new Error('Google Client ID is not configured. Please set EXPO_PUBLIC_GOOGLE_CLIENT_ID in your environment variables.');
      }

      const redirectUri = AuthSession.makeRedirectUri();
      
      // Use token flow to get ID token directly (implicit flow)
      const request = new AuthSession.AuthRequest({
        clientId: GOOGLE_CLIENT_ID,
        scopes: ['openid', 'profile', 'email'],
        responseType: AuthSession.ResponseType.IdToken,
        redirectUri,
        extraParams: {},
      });

      const result = await request.promptAsync(googleDiscovery);

      if (result.type === 'success') {
        const { id_token } = result.params;
        
        if (!id_token) {
          throw new Error('No ID token received from Google');
        }

        // Create Firebase credential
        const credential = GoogleAuthProvider.credential(id_token);
        const userCredential = await signInWithCredential(auth, credential);
        
        const isNewUser = userCredential.user.metadata.creationTime === userCredential.user.metadata.lastSignInTime;
        
        // Save user to Firestore if new user
        if (isNewUser) {
          await saveUserToFirestore(userCredential.user);
        }
        
        return { user: userCredential.user, isNewUser };
      } else if (result.type === 'cancel' || result.type === 'dismiss') {
        // User cancelled - create a special error that won't show alerts
        const cancelError: any = new Error('SIGN_IN_CANCELLED');
        cancelError.isCancellation = true;
        throw cancelError;
      } else {
        throw new Error('Google sign-in failed');
      }
    }
  } catch (error: any) {
    console.error('Google sign-in error:', error);
    throw error;
  }
}

/**
 * Sign in with Apple
 */
export async function signInWithApple(): Promise<SocialAuthResult> {
  try {
    if (Platform.OS !== 'ios') {
      throw new Error('Apple Sign-In is only available on iOS');
    }

    // Generate a random nonce
    const nonce = await Crypto.digestStringAsync(
      Crypto.CryptoDigestAlgorithm.SHA256,
      Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)
    );

    // Perform Apple authentication
    const appleCredential = await AppleAuthentication.signInAsync({
      requestedScopes: [
        AppleAuthentication.AppleAuthenticationScope.FULL_NAME,
        AppleAuthentication.AppleAuthenticationScope.EMAIL,
      ],
      nonce,
    });

    if (!appleCredential.identityToken) {
      throw new Error('Apple Sign-In failed - no identity token returned');
    }

    // Create Firebase credential
    const provider = new OAuthProvider('apple.com');
    const credential = provider.credential({
      idToken: appleCredential.identityToken,
      rawNonce: nonce,
    });

    const userCredential = await signInWithCredential(auth, credential);
    
    const isNewUser = userCredential.user.metadata.creationTime === userCredential.user.metadata.lastSignInTime;
    
    // Save user to Firestore if new user
    if (isNewUser) {
      // Apple provides name only on first sign-in
      const displayName = appleCredential.fullName
        ? `${appleCredential.fullName.givenName || ''} ${appleCredential.fullName.familyName || ''}`.trim()
        : null;
      
      await saveUserToFirestore(userCredential.user, {
        displayName: displayName || undefined,
        email: appleCredential.email || undefined,
      });
    }
    
    return { user: userCredential.user, isNewUser };
  } catch (error: any) {
    // Check for cancellation errors
    if (error.code === 'ERR_REQUEST_CANCELED' || 
        error.code === 'ERR_CANCELED' ||
        error.message?.includes('cancelled') ||
        error.message?.includes('canceled')) {
      const cancelError: any = new Error('SIGN_IN_CANCELLED');
      cancelError.isCancellation = true;
      throw cancelError;
    }
    
    // Suppress "authorization attempt failed for an unknown reason" error
    // This is a common non-critical error in Expo Go that can be safely ignored
    if (error.message?.includes('authorization attempt failed for an unknown reason')) {
      const cancelError: any = new Error('SIGN_IN_CANCELLED');
      cancelError.isCancellation = true;
      throw cancelError;
    }
    
    // Only log other errors
    console.error('Apple sign-in error:', error);
    throw error;
  }
}

/**
 * Save user data to Firestore
 */
async function saveUserToFirestore(
  user: User, 
  additionalData?: { displayName?: string; email?: string }
) {
  try {
    const userRef = doc(db, 'users', user.uid);
    const userSnap = await getDoc(userRef);

    if (!userSnap.exists()) {
      // Extract name from displayName if available
      const displayName = additionalData?.displayName || user.displayName || '';
      const nameParts = displayName.split(' ');
      const firstName = nameParts[0] || '';
      const lastName = nameParts.slice(1).join(' ') || '';

      await setDoc(userRef, {
        firstName,
        lastName,
        email: additionalData?.email || user.email || '',
        createdAt: serverTimestamp(),
        updatedAt: serverTimestamp(),
      });
    }
  } catch (error) {
    console.error('Error saving user to Firestore:', error);
    // Don't throw - user is still authenticated even if Firestore save fails
  }
}

