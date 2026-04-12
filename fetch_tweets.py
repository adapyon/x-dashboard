import asyncio
import json
import os
from datetime import datetime, timezone
from twikit import Client

USERNAME = os.environ["X_USERNAME"]
EMAIL = os.environ["X_EMAIL"]
PASSWORD = os.environ["X_PASSWORD"]

LIST_IDS = [
    {"id": "181994093", "label": "list1"},
    {"id": "1054516216868392960", "label": "list2"},
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
        "url": "https://x.com/" + tweet.user.screen_name + "/status/" + tweet.id,
    }


async def main():
    client = Client("ja")

    if os.path.exists(COOKIES_FILE):
        print("Loading cookies...")
        client.load_cookies(COOKIES_FILE)
    else:
        print("Logging in...")
        await client.login(
            auth_info_1=USERNAME,
            auth_info_2=EMAIL,
            password=PASSWORD,
            cookies_file=COOKIES_FILE,
        )
        print("Login successful, cookies saved.")

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
        columns.append({
            "id": "for_you",
            "label": "おすすめ",
            "icon": "✨",
            "tweets": [],
            "error": str(e),
        })

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
        columns.append({
            "id": "following",
            "label": "フォロー中",
            "icon": "👥",
            "tweets": [],
            "error": str(e),
        })

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
