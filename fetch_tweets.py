import asyncio
import json
import os
from datetime import datetime, timezone
from twikit import Client

# X_COOKIES env var: cookie string from browser (e.g. "auth_token=xxx; ct0=yyy; ...")
COOKIES_STR = os.environ.get("X_COOKIES", "")

LIST_IDS = [
    {"id": "181994093", "label": "list1"},
    {"id": "1054516216868392960", "label": "list2"},
]

COOKIES_FILE = "cookies.json"
OUTPUT_FILE = "docs/data.json"


def parse_cookie_string(cookie_str):
    """Parse browser cookie string into dict"""
    cookies = {}
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies


def save_cookies_json(cookie_dict, path):
    """Save cookies in twikit-compatible format"""
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
    client = Client("ja")

    # Build cookies.json from X_COOKIES env var
    if COOKIES_STR:
        print("Using X_COOKIES from environment...")
        cookie_dict = parse_cookie_string(COOKIES_STR)
        save_cookies_json(cookie_dict, COOKIES_FILE)
        print("Cookies saved: " + str(list(cookie_dict.keys())))
    elif os.path.exists(COOKIES_FILE):
        print("Using existing cookies.json...")
    else:
        raise Exception("No cookies available. Set X_COOKIES secret.")

    client.load_cookies(COOKIES_FILE)

    columns = []

    # column1: for you
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

    # column2: following
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

    # columns 3,4: lists
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

    os.makedirs("docs", exist_ok=True)
    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "columns": columns,
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("done: " + OUTPUT_FILE)


asyncio.run(main())
