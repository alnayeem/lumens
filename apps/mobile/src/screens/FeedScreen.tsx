import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Dimensions, FlatList, Image, Linking, SafeAreaView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { fetchContent, VideoItem } from '../api';
import type { RootStackParamList } from '../../App';

type Props = NativeStackScreenProps<RootStackParamList, 'Feed'>;

const numColumns = 2;
const GUTTER = 12;
const CARD_W = (Dimensions.get('window').width - (GUTTER * (numColumns + 1))) / numColumns;

export default function FeedScreen({ route, navigation }: Props) {
  const { slug } = route.params;
  const [items, setItems] = useState<VideoItem[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (next = false) => {
    try {
      if (next) setLoadingMore(true); else setLoading(true);
      const res = await fetchContent({ topic: slug, language: 'en', limit: 24, cursor: next ? cursor : null });
      setItems(next ? [...items, ...(res.items || [])] : (res.items || []));
      setCursor(res.nextCursor ?? null);
    } catch (e: any) {
      setError(e?.message || 'Failed to load');
    } finally {
      if (next) setLoadingMore(false); else setLoading(false);
    }
  }, [slug, cursor, items]);

  useEffect(() => { load(false); }, [slug]);

  const extractId = (it: VideoItem): string | undefined => {
    if (it.video_id) return it.video_id;
    const fromEmbed = /\/embed\/([A-Za-z0-9_-]{6,})/.exec(it.embed || '');
    if (fromEmbed && fromEmbed[1]) return fromEmbed[1];
    const fromUrl = /[?&]v=([A-Za-z0-9_-]{6,})/.exec(it.url || '');
    if (fromUrl && fromUrl[1]) return fromUrl[1];
    return undefined;
  };

  const openVideo = (it: VideoItem) => {
    const vid = extractId(it);
    if (vid) {
      navigation.navigate('Swipe', { slug, label: route.params.label, initialVideoId: vid });
      return;
    }
    if (it.url) {
      Linking.openURL(it.url).catch(() => {});
    }
  };

  const renderItem = ({ item }: { item: VideoItem }) => {
    const thumb = item.thumbnails?.medium?.url || item.thumbnails?.default?.url;
    return (
      <TouchableOpacity style={styles.card} onPress={() => openVideo(item)} activeOpacity={0.8}>
        {thumb ? (<Image source={{ uri: thumb }} style={styles.thumb} />) : (<View style={[styles.thumb, styles.thumbPlaceholder]} />)}
        <Text style={styles.title} numberOfLines={2}>{item.title}</Text>
        <Text style={styles.meta} numberOfLines={1}>{item.channel_title}</Text>
      </TouchableOpacity>
    );
  };

  if (loading) return <SafeAreaView style={styles.center}><ActivityIndicator /></SafeAreaView>;
  if (error) return <SafeAreaView style={styles.center}><Text>{error}</Text></SafeAreaView>;

  return (
    <SafeAreaView style={styles.container}>
      <FlatList
        contentContainerStyle={{ padding: GUTTER }}
        data={items}
        keyExtractor={(_, idx) => String(idx)}
        renderItem={renderItem}
        numColumns={numColumns}
        columnWrapperStyle={{ gap: GUTTER }}
        ItemSeparatorComponent={() => <View style={{ height: GUTTER }} />}
        onEndReachedThreshold={0.5}
        onEndReached={() => { if (cursor && !loadingMore) load(true); }}
        ListFooterComponent={loadingMore ? <ActivityIndicator style={{ marginVertical: 16 }} /> : null}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  card: { width: CARD_W, },
  thumb: { width: '100%', aspectRatio: 16/9, borderRadius: 8, backgroundColor: '#eee' },
  thumbPlaceholder: { alignItems: 'center', justifyContent: 'center' },
  title: { marginTop: 6, fontSize: 14, fontWeight: '600' },
  meta: { color: '#666', marginTop: 2, fontSize: 12 }
});
