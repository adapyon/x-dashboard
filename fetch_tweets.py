import asyncio
import json
import os
from datetime import datetime, timezone
from twikit import Client

COOKIES_STR = os.environ.get("X_COOKIES", "")

LIST_IDS = [
    {"id": "181994093", "label": "節約"},
    {"id": "1054516216868392960", "label": "要チェック"},
    {"id": "1403694821550686209", "label": "確認"},
]

OUTPUT_FILE = "docs/data.json"

def parse_cookie_string(cookie_str):
    cookies = {}
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies

def save_cookies_json(cookie_dict, path):
    cookie_list = []
    for name, value in cookie_dict.items():
        cookie_list.append({
            "name": name,
            "value": value,
            "domain": ".x.com",
            "path": "/",
        })
    with open(path, "w") as f:
        json.dump(cookie_list, f)

def get_media_urls(tweet):
    media_urls = []
    try:
        media = getattr(tweet, 'media', None)
        if not media:
            return []
        for m in media:
            url = (
                getattr(m, 'media_url_https', None)
                or getattr(m, 'media_url', None)
                or getattr(m, 'preview_image_url', None)
                or getattr(m, 'url', None)
            )
            if url and not url.startswith('https://t.co'):
                media_urls.append(url)
    except Exception as e:
        print("media err: " + str(e))
    return media_urls

def safe_get(obj, *attrs, default=None):
    for attr in attrs:
        try:
            val = getattr(obj, attr, None)
            if val is not None:
                return val
        except Exception:
            pass
    return default

def tweet_to_dict(tweet):
    try:
        user = safe_get(tweet, 'user')
        return {
            "id": safe_get(tweet, 'id', default=''),
            "text": safe_get(tweet, 'text', default=''),
            "created_at": safe_get(tweet, 'created_at', default=''),
            "user_name": safe_get(user, 'name', default='') if user else '',
            "user_screen_name": safe_get(user, 'screen_name', default='') if user else '',
            "user_icon": safe_get(user, 'profile_image_url', default='') if user else '',
            "like_count": safe_get(tweet, 'favorite_count', default=0),
            "retweet_count": safe_get(tweet, 'retweet_count', default=0),
            "reply_count": safe_get(tweet, 'reply_count', default=0),
            "url": "https://x.com/" + (safe_get(user, 'screen_name', default='') if user else '') + "/status/" + safe_get(tweet, 'id', default=''),
            "media": get_media_urls(tweet),
        }
    except Exception as e:
        print("tweet_to_dict err: " + str(e))
        return None

async def main():
    if not COOKIES_STR:
        raise Exception("X_COOKIES not set")

    client = Client("ja")
    cookie_dict = parse_cookie_string(COOKIES_STR)
    save_cookies_json(cookie_dict, "cookies.json")
    client.load_cookies("cookies.json")
    print("Cookies loaded.")

    columns = []
    for lst in LIST_IDS:
        list_id = lst["id"]
        list_label = lst["label"]
        try:
            list_tweets = await client.get_list_tweets(list_id, count=50)
            dicts = [tweet_to_dict(t) for t in list_tweets]
            dicts = [d for d in dicts if d is not None]
            columns.append({
                "id": "list_" + list_id,
                "label": list_label,
                "icon": "📋",
                "tweets": dicts,
            })
            print("ok " + list_label + ": " + str(len(dicts)))
        except Exception as e:
            print("err " + list_label + ": " + str(e))
            columns.append({
                "id": "list_" + list_id,
                "label": list_label,
                "icon": "📋",
                "tweets": [],
                "error": str(e),
            })

    os.makedirs("docs", exist_ok=True)
    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "columns": columns,
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("done: " + OUTPUT_FILE)

asyncio.run(main())
