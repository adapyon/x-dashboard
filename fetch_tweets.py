import asyncio
import json
import os
from datetime import datetime, timezone
from twikit import Client

COOKIES_STR = os.environ.get("X_COOKIES", "")

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
            columns.append({
                "id": "list_" + list_id,
                "label": list_label,
                "icon": "📋",
                "tweets": [tweet_to_dict(t) for t in list_tweets],
            })
            print("ok " + list_label + ": " + str(len(list_tweets)))
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
