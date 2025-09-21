from services.ingest.lib.youtube import detect_youtube_ref


def test_detect_handle():
    assert detect_youtube_ref("@One4kids-Zaky") == ("handle", "@One4kids-Zaky")


def test_detect_channel_url():
    kind, val = detect_youtube_ref("https://www.youtube.com/channel/UC178EmfQAV3OT-UpuO6WUMg")
    assert kind == "channel_id"
    assert val.startswith("UC")


def test_detect_playlist_query_param():
    kind, val = detect_youtube_ref("https://www.youtube.com/playlist?list=PLHG5uxhiqH9ULotm1fcrbTV19t5DzieOq")
    assert kind == "playlist_id"
    assert val.startswith("PL")


def test_detect_video_short_url():
    kind, val = detect_youtube_ref("https://youtu.be/dQw4w9WgXcQ")
    assert kind == "video_id"
    assert val == "dQw4w9WgXcQ"


def test_detect_user_url():
    kind, val = detect_youtube_ref("https://www.youtube.com/user/NoorKids")
    assert kind == "user"
    assert val == "NoorKids"


def test_detect_fallback_query():
    assert detect_youtube_ref("Some Custom Channel Name")[0] == "query"

