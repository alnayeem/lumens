import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ActivityIndicator, Dimensions, FlatList, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import YoutubePlayer from 'react-native-youtube-iframe';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList } from '../../App';
import { fetchContent, VideoItem } from '../api';

type Props = NativeStackScreenProps<RootStackParamList, 'Swipe'>;

const { width: SCREEN_W } = Dimensions.get('window');

export default function SwipePlayerScreen({ route }: Props) {
  const { slug, initialVideoId } = route.params;
  const [items, setItems] = useState<VideoItem[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [index, setIndex] = useState(0);
  const listRef = useRef<FlatList>(null);

  const extractId = (it: VideoItem): string | undefined => {
    if (it.video_id) return it.video_id;
    const e = /\/embed\/([A-Za-z0-9_-]{6,})/.exec(it.embed || '');
    if (e && e[1]) return e[1];
    const u = /[?&]v=([A-Za-z0-9_-]{6,})/.exec(it.url || '');
    if (u && u[1]) return u[1];
    return undefined;
  };

  const load = useCallback(async (next = false) => {
    if (next && !cursor) return;
    if (next) setLoading(false); else setLoading(true);
    const res = await fetchContent({ topic: slug, language: 'en', limit: 24, cursor: next ? cursor : null });
    if (next) {
      setItems((prev) => [...prev, ...(res.items || [])]);
    } else {
      setItems(res.items || []);
    }
    setCursor(res.nextCursor ?? null);
    if (!next && initialVideoId) {
      const idx = (res.items || []).findIndex((x) => extractId(x) === initialVideoId);
      if (idx >= 0) {
        setIndex(idx);
        requestAnimationFrame(() => listRef.current?.scrollToIndex({ index: idx, animated: false }));
      }
    }
    if (!next) setLoading(false);
  }, [slug, cursor, initialVideoId]);

  useEffect(() => { load(false); }, [slug]);

  const onViewableItemsChanged = useRef(({ viewableItems }: any) => {
    if (viewableItems && viewableItems.length > 0) {
      const vi = viewableItems[0];
      if (typeof vi.index === 'number') setIndex(vi.index);
    }
  }).current;
  const viewabilityConfig = useMemo(() => ({ itemVisiblePercentThreshold: 60 }), []);

  const onStateChange = useCallback((state: string, i: number) => {
    if (state === 'ended') {
      const nextIndex = i + 1;
      if (nextIndex < items.length) {
        setIndex(nextIndex);
        requestAnimationFrame(() => listRef.current?.scrollToIndex({ index: nextIndex, animated: true }));
      }
    }
  }, [items.length]);

  const renderItem = ({ item, index: i }: { item: VideoItem; index: number }) => {
    const vid = extractId(item);
    const playing = i === index;
    return (
      <View style={styles.slide}>
        {vid ? (
          <YoutubePlayer
            height={240}
            play={playing}
            videoId={vid}
            onChangeState={(s) => onStateChange(s, i)}
          />
        ) : (
          <View style={[styles.slide, styles.center]}><ActivityIndicator /></View>
        )}
      </View>
    );
  };

  if (loading && items.length === 0) {
    return (
      <SafeAreaView style={styles.center}>
        <ActivityIndicator />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <FlatList
        ref={listRef}
        data={items}
        keyExtractor={(_, i) => String(i)}
        renderItem={renderItem}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onEndReachedThreshold={0.6}
        onEndReached={() => { if (cursor) load(true); }}
        onViewableItemsChanged={onViewableItemsChanged}
        viewabilityConfig={viewabilityConfig}
        getItemLayout={(_, i) => ({ length: SCREEN_W, offset: SCREEN_W * i, index: i })}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  slide: { width: SCREEN_W, paddingVertical: 16, alignItems: 'center' },
});
