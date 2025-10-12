import React, { useState } from 'react';
import { KeyboardAvoidingView, Platform, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../auth/AuthContext';

export default function LoginScreen() {
  const { signIn } = useAuth();
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string | null>(null);
  const onSubmit = async () => {
    try {
      if (!email.includes('@')) throw new Error('Enter a valid email');
      await signIn(email.trim());
    } catch (e: any) {
      setError(e?.message || 'Failed to sign in');
    }
  };
  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.inner}>
        <Text style={styles.title}>Welcome to Lumens</Text>
        <Text style={styles.subtitle}>Sign in to continue</Text>
        <TextInput
          value={email}
          onChangeText={setEmail}
          placeholder="you@example.com"
          keyboardType="email-address"
          autoCapitalize="none"
          autoCorrect={false}
          style={styles.input}
        />
        {error ? <Text style={styles.error}>{error}</Text> : null}
        <TouchableOpacity style={styles.button} onPress={onSubmit} activeOpacity={0.9}>
          <Text style={styles.buttonText}>Continue</Text>
        </TouchableOpacity>
        <View style={{ height: 16 }} />
        <Text style={styles.hint}>This demo stores your email locally only.</Text>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  inner: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24 },
  title: { fontSize: 24, fontWeight: '700' },
  subtitle: { marginTop: 8, fontSize: 14, color: '#666' },
  input: { marginTop: 24, width: '100%', borderWidth: 1, borderColor: '#ddd', borderRadius: 8, paddingHorizontal: 12, height: 44 },
  button: { marginTop: 16, width: '100%', backgroundColor: '#1e88e5', height: 44, borderRadius: 8, alignItems: 'center', justifyContent: 'center' },
  buttonText: { color: '#fff', fontWeight: '600' },
  error: { color: '#d32f2f', marginTop: 8 },
  hint: { color: '#999', fontSize: 12 },
});

