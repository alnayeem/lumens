import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import CategoriesScreen from './src/screens/CategoriesScreen';
import FeedScreen from './src/screens/FeedScreen';
import PlayerScreen from './src/screens/PlayerScreen';
import SwipePlayerScreen from './src/screens/SwipePlayerScreen';
import type { VideoItem } from './src/api';

export type RootStackParamList = {
  Categories: undefined;
  Feed: { slug: string; label: string };
  Player: { item: VideoItem };
  Swipe: { slug: string; label: string; initialVideoId?: string | null };
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator>
        <Stack.Screen name="Categories" component={CategoriesScreen} />
        <Stack.Screen name="Feed" component={FeedScreen} options={({ route }) => ({ title: route.params.label })} />
        <Stack.Screen name="Player" component={PlayerScreen} options={{ title: 'Preview' }} />
        <Stack.Screen name="Swipe" component={SwipePlayerScreen} options={({ route }) => ({ title: route.params.label })} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
