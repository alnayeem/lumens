import React, { useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList } from '../../App';
import { useAuth } from '../auth/AuthContext';

type Props = NativeStackScreenProps<RootStackParamList, 'Intro'>;

export default function IntroScreen({ navigation }: Props) {
  const { user } = useAuth();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const seen = await AsyncStorage.getItem('introSeen');
        if (seen) {
          navigation.reset({ index: 0, routes: [{ name: user ? 'Latest' : 'Login' }] });
          return;
        }
      } finally {
        setChecking(false);
      }
    })();
  }, [user]);

  const onContinue = async () => {
    await AsyncStorage.setItem('introSeen', '1');
    navigation.reset({ index: 0, routes: [{ name: user ? 'Latest' : 'Login' }] });
  };

  if (checking) {
    return (
      <SafeAreaView style={styles.center}>
        <ActivityIndicator />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.inner}>
        <Text style={styles.title}>Welcome to Lumens</Text>
        <Text style={styles.subtitle}>Curated Islamic videos, swipe to explore.</Text>
        <TouchableOpacity style={styles.button} onPress={onContinue} activeOpacity={0.9}>
          <Text style={styles.buttonText}>Get Started</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  inner: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24 },
  title: { fontSize: 28, fontWeight: '700' },
  subtitle: { marginTop: 8, fontSize: 16, color: '#666', textAlign: 'center' },
  button: { marginTop: 24, backgroundColor: '#1e88e5', height: 48, borderRadius: 8, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 20 },
  buttonText: { color: '#fff', fontWeight: '600', fontSize: 16 },
});

