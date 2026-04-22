"""
YouTube Data API v3 模块
获取视频详情、频道信息，补充 Viewstats 缺失的数据
"""
import os
import json
from datetime import datetime
from googleapiclient.discovery import build


CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "cache", "youtube_cache.json")


def get_youtube_client(api_key=None):
    key = api_key or os.environ.get("YOUTUBE_API_KEY", "")
    if not key:
        raise ValueError("YOUTUBE_API_KEY not set")
    return build("youtube", "v3", developerKey=key)


def load_cache():
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"videos": {}, "channels": {}}


def save_cache(cache):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def enrich_videos(videos, api_key=None):
    if not videos:
        return videos

    youtube = get_youtube_client(api_key)
    cache = load_cache()

    video_ids_to_fetch = []
    for v in videos:
        vid = v.get("video_id", "")
        if vid and vid not in cache.get("videos", {}):
            video_ids_to_fetch.append(vid)

    for i in range(0, len(video_ids_to_fetch), 50):
        batch = video_ids_to_fetch[i : i + 50]
        try:
            resp = youtube.videos().list(
                part="snippet,statistics,contentDetails",
                id=",".join(batch),
            ).execute()

            for item in resp.get("items", []):
                vid = item["id"]
                snippet = item.get("snippet", {})
                stats = item.get("statistics", {})
                content = item.get("contentDetails", {})

                cache.setdefault("videos", {})[vid] = {
                    "title": snippet.get("title", ""),
                    "description": snippet.get("description", ""),
                    "channel_id": snippet.get("channelId", ""),
                    "channel_name": snippet.get("channelTitle", ""),
                    "tags": snippet.get("tags", []),
                    "category_id": snippet.get("categoryId", ""),
                    "published_at": snippet.get("publishedAt", ""),
                    "views": int(stats.get("viewCount", 0)),
                    "likes": int(stats.get("likeCount", 0)),
                    "comments": int(stats.get("commentCount", 0)),
                    "duration": content.get("duration", ""),
                    "thumbnail_high": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                    "thumbnail_max": snippet.get("thumbnails", {}).get("maxres", {}).get("url", ""),
                    "fetched_at": datetime.utcnow().isoformat(),
                }
        except Exception as e:
            print(f"[YouTube API] Video fetch error: {e}")

    channel_ids_to_fetch = set()
    for v in videos:
        vid = v.get("video_id", "")
        cached = cache.get("videos", {}).get(vid, {})
        ch_id = cached.get("channel_id", "") or v.get("channel_id", "")
        if ch_id and ch_id not in cache.get("channels", {}):
            channel_ids_to_fetch.add(ch_id)

    channel_ids_list = list(channel_ids_to_fetch)
    for i in range(0, len(channel_ids_list), 50):
        batch = channel_ids_list[i : i + 50]
        try:
            resp = youtube.channels().list(
                part="snippet,statistics",
                id=",".join(batch),
            ).execute()

            for item in resp.get("items", []):
                ch_id = item["id"]
                snippet = item.get("snippet", {})
                stats = item.get("statistics", {})

                cache.setdefault("channels", {})[ch_id] = {
                    "name": snippet.get("title", ""),
                    "handle": snippet.get("customUrl", ""),
                    "subscribers": int(stats.get("subscriberCount", 0)),
                    "total_views": int(stats.get("viewCount", 0)),
                    "video_count": int(stats.get("videoCount", 0)),
                    "description": snippet.get("description", "")[:500],
                    "country": snippet.get("country", ""),
                    "thumbnail": snippet.get("thumbnails", {}).get("default", {}).get("url", ""),
                    "fetched_at": datetime.utcnow().isoformat(),
                }
        except Exception as e:
            print(f"[YouTube API] Channel fetch error: {e}")

    save_cache(cache)

    for v in videos:
        vid = v.get("video_id", "")
        cached_video = cache.get("videos", {}).get(vid, {})
        ch_id = cached_video.get("channel_id", "") or v.get("channel_id", "")
        cached_channel = cache.get("channels", {}).get(ch_id, {})

        if not v.get("title"):
            v["title"] = cached_video.get("title", "Unknown")
        v["description"] = cached_video.get("description", "")
        v["tags"] = cached_video.get("tags", [])
        v["category_id"] = cached_video.get("category_id", "")
        v["likes"] = cached_video.get("likes", 0)
        v["comments"] = cached_video.get("comments", 0)
        v["published_at"] = cached_video.get("published_at", v.get("upload_date", ""))
        v["thumbnail"] = (
            cached_video.get("thumbnail_max")
            or cached_video.get("thumbnail_high")
            or v.get("thumbnail", f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg")
        )

        v["channel_id"] = ch_id
        if not v.get("channel_name"):
            v["channel_name"] = cached_channel.get("name", v.get("channel_handle", ""))
        v["subscribers"] = cached_channel.get("subscribers", 0)
        v["channel_total_views"] = cached_channel.get("total_views", 0)
        v["channel_video_count"] = cached_channel.get("video_count", 0)
        v["channel_country"] = cached_channel.get("country", "")
        v["channel_thumbnail"] = cached_channel.get("thumbnail", "")

        views = v.get("views", 0) or cached_video.get("views", 0)
        v["views"] = views
        subs = v["subscribers"]
        v["virality_ratio"] = round(views / subs, 1) if subs > 0 else 0

        if v.get("published_at"):
            try:
                pub_date = datetime.fromisoformat(v["published_at"].replace("Z", "+00:00"))
                days = max((datetime.now(pub_date.tzinfo) - pub_date).days, 1)
                v["days_since_upload"] = days
                v["daily_avg_views"] = round(views / days)
            except Exception:
                v["days_since_upload"] = 0
                v["daily_avg_views"] = 0
        else:
            v["days_since_upload"] = 0
            v["daily_avg_views"] = 0

        interactions = v.get("likes", 0) + v.get("comments", 0)
        v["engagement_rate"] = round(interactions / views * 100, 2) if views > 0 else 0

    return videos


if __name__ == "__main__":
    test_videos = [{"video_id": "HBLxRb_4oDs", "rank": 1, "views": 159000000}]
    enriched = enrich_videos(test_videos)
    print(json.dumps(enriched[0], indent=2, ensure_ascii=False))
