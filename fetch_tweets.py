import asyncio
import json
import os
from datetime import datetime, timezone
from twikit import Client

# X_COOKIES: @adapyon (main) cookie string - for columns 1 & 2
# X_COOKIES_VJ: @vj_duch cookie string - for columns 3 & 4 (lists)
COOKIES_MAIN_STR = os.environ.get("X_COOKIES", "")
COOKIES_VJ_STR = os.environ.get("X_COOKIES_VJ", "")

LIST_IDS = [
    {"id": "181994093", "label": "節約"},
    {"id": "1054516216868392960", "label": "要チェック"},
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


def tweet_to_dict(tweet):
    return {
        "id": tweet.id,
        "text": tweet.text,
        "created_at": tweet.created_at,
        "user_name": tweet.user.name,
        "user_screen_name": tweet.user.screen_name,
        "user_icon": tweet.user.profile_image_url,
        "like_count": tweet.favorite_count,
        "retweet_count": tweet.retweet_count,
        "reply_count": tweet.reply_count,
        "url": "https://x.com/" + tweet.user.screen_name + "/status/" + tweet.id,
    }


async def fetch_main_columns(columns):
    """Fetch columns 1 & 2 using @adapyon cookies"""
    if not COOKIES_MAIN_STR:
        print("X_COOKIES not set, skipping main columns")
        columns.append({"id": "for_you", "label": "おすすめ", "icon": "✨", "tweets": [], "error": "X_COOKIES not set"})
        columns.append({"id": "following", "label": "フォロー中", "icon": "👥", "tweets": [], "error": "X_COOKIES not set"})
        return

    client = Client("ja")
    cookie_dict = parse_cookie_string(COOKIES_MAIN_STR)
    save_cookies_json(cookie_dict, "cookies_main.json")
    client.load_cookies("cookies_main.json")

    try:
        for_you = await client.get_timeline(count=30)
        columns.append({
            "id": "for_you",
            "label": "おすすめ",
            "icon": "✨",
            "tweets": [tweet_to_dict(t) for t in for_you],
        })
        print("ok for_you: " + str(len(for_you)))
    except Exception as e:
        print("err for_you: " + str(e))
        columns.append({"id": "for_you", "label": "おすすめ", "icon": "✨", "tweets": [], "error": str(e)})

    try:
        following = await client.get_latest_timeline(count=30)
        columns.append({
            "id": "following",
            "label": "フォロー中",
            "icon": "👥",
            "tweets": [tweet_to_dict(t) for t in following],
        })
        print("ok following: " + str(len(following)))
    except Exception as e:
        print("err following: " + str(e))
        columns.append({"id": "following", "label": "フォロー中", "icon": "👥", "tweets": [], "error": str(e)})


async def fetch_list_columns(columns):
    """Fetch columns 3 & 4 using @vj_duch cookies"""
    cookies_str = COOKIES_VJ_STR if COOKIES_VJ_STR else COOKIES_MAIN_STR
    if not cookies_str:
        for lst in LIST_IDS:
            columns.append({"id": "list_" + lst["id"], "label": lst["label"], "icon": "📋", "tweets": [], "error": "No cookies"})
        return

    client = Client("ja")
    cookie_dict = parse_cookie_string(cookies_str)
    save_cookies_json(cookie_dict, "cookies_vj.json")
    client.load_cookies("cookies_vj.json")

    for lst in LIST_IDS:
        list_id = lst["id"]
        list_label = lst["label"]
        try:
            list_tweets = await client.get_list_tweets(list_id, count=30)
            columns.append({
                "id": "list_" + list_id,
                "label": list_label,
                "icon": "📋",
                "tweets": [tweet_to_dict(t) for t in list_tweets],
            })
            print("ok list " + list_label + ": " + str(len(list_tweets)))
        except Exception as e:
            print("err list " + list_label + ": " + str(e))
            columns.append({"id": "list_" + list_id, "label": list_label, "icon": "📋", "tweets": [], "error": str(e)})


async def main():
    columns = []
    await fetch_main_columns(columns)
    await fetch_list_columns(columns)

    os.makedirs("docs", exist_ok=True)
    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "columns": columns,
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("done: " + OUTPUT_FILE)


asyncio.run(main())
