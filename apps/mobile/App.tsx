import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import CategoriesScreen from './src/screens/CategoriesScreen';
import FeedScreen from './src/screens/FeedScreen';
import LatestScreen from './src/screens/LatestScreen';
import LoginScreen from './src/screens/LoginScreen';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { AuthProvider, useAuth } from './src/auth/AuthContext';
import PlayerScreen from './src/screens/PlayerScreen';
import SwipePlayerScreen from './src/screens/SwipePlayerScreen';
import type { VideoItem } from './src/api';

export type RootStackParamList = {
  Intro: undefined;
  Login: undefined;
  Latest: undefined;
  Categories: undefined;
  Feed: { slug: string; label: string };
  Player: { item: VideoItem };
  Swipe: { slug: string; label: string; initialVideoId?: string | null };
};

const Stack = createNativeStackNavigator<RootStackParamList>();

function RootNavigator() {
  const { user, initializing } = useAuth();
  if (initializing) return null;
  return (
    <Stack.Navigator initialRouteName={'Intro'}>
      <Stack.Screen name="Intro" component={require('./src/screens/IntroScreen').default} options={{ headerShown: false }} />
      {!user ? (
        <Stack.Screen name="Login" component={LoginScreen} options={{ headerShown: false }} />
      ) : (
        <>
          <Stack.Screen name="Latest" component={LatestScreen} options={{ title: 'Latest' }} />
          <Stack.Screen name="Categories" component={CategoriesScreen} />
          <Stack.Screen name="Feed" component={FeedScreen} options={({ route }) => ({ title: route.params.label })} />
          <Stack.Screen name="Player" component={PlayerScreen} options={{ title: 'Preview' }} />
          <Stack.Screen name="Swipe" component={SwipePlayerScreen} options={({ route }) => ({ title: route.params.label })} />
        </>
      )}
    </Stack.Navigator>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <NavigationContainer>
          <RootNavigator />
        </NavigationContainer>
      </AuthProvider>
    </SafeAreaProvider>
  );
}
