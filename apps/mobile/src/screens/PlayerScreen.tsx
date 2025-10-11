import React, { useLayoutEffect, useMemo, useState, useCallback } from 'react';
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import YoutubePlayer from 'react-native-youtube-iframe';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList } from '../../App';
import { Linking } from 'react-native';

type Props = NativeStackScreenProps<RootStackParamList, 'Player'>;

export default function PlayerScreen({ route, navigation }: Props) {
  const { item } = route.params;
  const embed = item.embed;
  const url = item.url;
  const videoId = useMemo(() => {
    if (item.video_id) return item.video_id;
    // Try to extract from embed or url
    const fromEmbed = /\/embed\/([A-Za-z0-9_-]{6,})/.exec(embed || '');
    if (fromEmbed && fromEmbed[1]) return fromEmbed[1];
    const fromUrl = /[?&]v=([A-Za-z0-9_-]{6,})/.exec(url || '');
    if (fromUrl && fromUrl[1]) return fromUrl[1];
    return undefined;
  }, [item.video_id, embed, url]);

  const [playing, setPlaying] = useState(false);
  const onChangeState = useCallback((state: string) => {
    if (state === 'ended') setPlaying(false);
  }, []);

  useLayoutEffect(() => {
    navigation.setOptions({
      headerRight: () => (
        <TouchableOpacity onPress={() => { if (url) Linking.openURL(url).catch(() => {}); }}>
          <Text style={styles.headerLink}>Open in YouTube</Text>
        </TouchableOpacity>
      )
    });
  }, [navigation, url]);

  if (!videoId) {
    return (
      <SafeAreaView style={styles.center}>
        <Text>No preview available.</Text>
        {url ? (
          <TouchableOpacity onPress={() => Linking.openURL(url || '').catch(() => {})}>
            <Text style={styles.headerLink}>Open in YouTube</Text>
          </TouchableOpacity>
        ) : null}
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <YoutubePlayer
        height={240}
        play={playing}
        videoId={videoId}
        onChangeState={onChangeState}
      />
      {!url ? null : (
        <View style={{ alignItems: 'center', paddingVertical: 8 }}>
          <TouchableOpacity onPress={() => Linking.openURL(url || '').catch(() => {})}>
            <Text style={styles.headerLink}>Open in YouTube</Text>
          </TouchableOpacity>
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  headerLink: { color: '#1e88e5', paddingHorizontal: 8, fontSize: 14 },
});
