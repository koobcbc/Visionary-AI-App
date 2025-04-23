import React, { useState } from "react";
import { View, TextInput, Button, Text, StyleSheet, Alert } from "react-native";
import { createUserWithEmailAndPassword, signInWithEmailAndPassword } from "firebase/auth";
import { auth } from "../firebaseConfig"; // your config file

export default function LoginScreen() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSignUp = async () => {
    console.log("Sign Up clicked");
    try {
    //   await createUserWithEmailAndPassword(auth, email, password);
      Alert.alert("Success", "Account created!");
    } catch (error) {
      Alert.alert("Error", error.message);
    }
  };

  const handleLogin = async () => {
    console.log("Login clicked");
    try {
      await signInWithEmailAndPassword(auth, email, password);
      Alert.alert("Success", "Logged in!");
    } catch (error) {
      Alert.alert("Error", error.message);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Login / Signup</Text>
      <TextInput
        placeholder="Email"
        style={styles.input}
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
        autoCapitalize="none"
      />
      <TextInput
        placeholder="Password"
        style={styles.input}
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />
      <View style={styles.buttonContainer}>
        <Button title="Login" onPress={handleLogin} />
        <Button title="Sign Up" onPress={handleSignUp} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, flex: 1, justifyContent: "center" },
  title: { fontSize: 24, marginBottom: 20, textAlign: "center" },
  input: { borderWidth: 1, padding: 12, marginVertical: 10, borderRadius: 5 },
  buttonContainer: { flexDirection: "row", justifyContent: "space-between", marginTop: 10 }
});