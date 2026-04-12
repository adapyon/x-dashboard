import asyncio
import json
import os
from datetime import datetime, timezone
from twikit import Client

USERNAME = os.environ["X_USERNAME"]
EMAIL = os.environ["X_EMAIL"]
PASSWORD = os.environ["X_PASSWORD"]

LIST_IDS = [
    {"id": "181994093", "label": "\u30ea\u30b9\u30c8\u2460"},
    {"id": "1054516216868392960", "label": "\u30ea\u30b9\u30c8\u2461"},
]

COOKIES_FILE = "cookies.json"
OUTPUT_FILE = "docs/data.json"


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
        "url": f"https://x.com/{tweet.user.screen_name}/status/{tweet.id}",
    }


async def main():
    client = Client("ja")

    if os.path.exists(COOKIES_FILE):
        client.load_cookies(COOKIES_FILE)
    else:
        await client.login(
            auth_info_1=USERNAME,
            auth_info_2=EMAIL,
            password=PASSWORD,
        )
        client.save_cookies(COOKIES_FILE)

    columns = []

    try:
        for_you = await client.get_timeline(count=30)
        columns.append({"id": "for_you", "label": "\u304a\u3059\u3059\u3081", "icon": "\u2728", "tweets": [tweet_to_dict(t) for t in for_you]})
        print(f"\u2705 \u304a\u3059\u3059\u3081: {len(for_you)}\u4ef6\u53d6\u5f97")
    except Exception as e:
        columns.append({"id": "for_you", "label": "\u304a\u3059\u3059\u3081", "icon": "\u2728", "tweets": [], "error": str(e)})

    try:
        following = await client.get_latest_timeline(count=30)
        columns.append({"id": "following", "label": "\u30d5\u30a9\u30ed\u30fc\u4e2d", "icon": "\U0001f465", "tweets": [tweet_to_dict(t) for t in following]})
        print(f"\u2705 \u30d5\u30a9\u30ed\u30fc\u4e2d: {len(following)}\u4ef6\u53d6\u5f97")
    except Exception as e:
        columns.append({"id": "following", "label": "\u30d5\u30a9\u30ed\u30fc\u4e2d", "icon": "\U0001f465", "tweets": [], "error": str(e)})

    for lst in LIST_IDS:
        try:
            list_tweets = await client.get_list_tweets(lst["id"], count=30)
            columns.append({"id": f"list_{lst[\"id\"]}", "label": lst["label"], "icon": "\U0001f4cb", "tweets": [tweet_to_dict(t) for t in list_tweets]})
        except Exception as e:
            columns.append({"id": f"list_{lst[\"id\"]}", "label": lst["label"], "icon": "\U0001f4cb", "tweets": [], "error": str(e)})

    os.makedirs("docs", exist_ok=True)
    output = {"updated_at": datetime.now(timezone.utc).isoformat(), "columns": columns}
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n\u2705 {OUTPUT_FILE} \u306b\u66f8\u304d\u51fa\u3057\u5b8c\u4e86")


asyncio.run(main())
