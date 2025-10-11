import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Dimensions, FlatList, Image, Linking, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { fetchContent, VideoItem } from '../api';
import type { RootStackParamList } from '../../App';
import YoutubePlayer from 'react-native-youtube-iframe';

type Props = NativeStackScreenProps<RootStackParamList, 'Latest'>;

const numColumns = 2;
const GUTTER = 12;
const CARD_W = (Dimensions.get('window').width - (GUTTER * (numColumns + 1))) / numColumns;

export default function LatestScreen({ navigation }: Props) {
  const [items, setItems] = useState<VideoItem[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (next = false) => {
    try {
      if (next) setLoadingMore(true); else setLoading(true);
      const res = await fetchContent({ limit: 24, cursor: next ? cursor : null });
      setItems(next ? [...items, ...(res.items || [])] : (res.items || []));
      setCursor(res.nextCursor ?? null);
    } catch (e: any) {
      setError(e?.message || 'Failed to load');
    } finally {
      if (next) setLoadingMore(false); else setLoading(false);
    }
  }, [cursor, items]);

  useEffect(() => { load(false); }, []);

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
      navigation.navigate('Swipe', { slug: '', label: 'Latest', initialVideoId: vid });
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

  const featuredId = useMemo(() => (items.length ? extractId(items[0]) : undefined), [items]);

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
        ListHeaderComponent={featuredId ? (
          <View style={{ marginBottom: 16 }}>
            <Text style={{ fontSize: 16, fontWeight: '600', marginBottom: 8 }}>Featured</Text>
            <YoutubePlayer height={240} play={false} videoId={featuredId} />
          </View>
        ) : null}
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
