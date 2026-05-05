import asyncio
import json
import os
import sys
import traceback
from datetime import datetime, timezone

from twikit import Client

COOKIES_STR = os.environ.get("X_COOKIES", "")
COOKIES_SET_AT = os.environ.get("X_COOKIES_SET_AT", "")

LIST_IDS = [
    {"id": "181994093", "label": "節約"},
    {"id": "1054516216868392960", "label": "要チェック"},
    {"id": "1403694821550686209", "label": "確認"},
]

OUTPUT_FILE = "docs/data.json"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_existing_output():
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def get_previous_column(previous_output, list_id):
    target_id = "list_" + list_id
    for col in previous_output.get("columns", []):
        if col.get("id") == target_id:
            return col
    return None


def get_cookie_age_days():
    if not COOKIES_SET_AT:
        return None
    try:
        set_at = datetime.fromisoformat(COOKIES_SET_AT.replace("Z", "+00:00"))
        return max(0, (datetime.now(timezone.utc) - set_at).days)
    except Exception:
        return None


def is_auth_error(e):
    msg = str(e)
    return "Unauthorized" in msg or "401" in msg


def compute_cookie_warning(age_days, auth_failed):
    if auth_failed:
        return "critical", "X_COOKIES を入れ直してください", True
    if age_days is None:
        return "none", "", False
    if age_days >= 10:
        return "critical", f"X_COOKIES の入れ直しを推奨します（設定から{age_days}日経過）", False
    if age_days >= 7:
        return "warning", f"X_COOKIES の入れ直しを推奨します（設定から{age_days}日経過）", False
    return "none", "", False


def normalize_error_message(error):
    raw = str(error).strip() or error.__class__.__name__
    if raw in {"'code'", '"code"'}:
        return "Xの応答形式が変わったか、取得先リストで一時的な取得エラーが発生しました"
    if "Unauthorized" in raw or "401" in raw:
        return "認証エラーです。X_COOKIES の期限切れまたは権限不足の可能性があります"
    if "rate limit" in raw.lower() or "429" in raw:
        return "取得回数の上限に達した可能性があります"
    return raw


def write_output(
    *,
    columns=None,
    updated_at=None,
    error=None,
    partial_error=False,
    last_success_at=None,
    cookie_warning_level="none",
    cookie_warning_message="",
    needs_cookie_refresh=False,
):
    os.makedirs("docs", exist_ok=True)
    previous = load_existing_output()
    output = {
        "updated_at": updated_at or previous.get("updated_at"),
        "last_attempt_at": now_iso(),
        "last_success_at": last_success_at or previous.get("last_success_at"),
        "cookie_warning_level": cookie_warning_level,
        "cookie_warning_message": cookie_warning_message,
        "needs_cookie_refresh": needs_cookie_refresh,
        "columns": columns if columns is not None else previous.get("columns", []),
    }
    if partial_error:
        output["partial_error"] = True
    if error:
        output["error"] = error
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("done: " + OUTPUT_FILE)


def parse_cookie_string(cookie_str):
    cookies = {}
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies


def get_media_urls(tweet):
    media_urls = []
    try:
        media = getattr(tweet, "media", None)
        if not media:
            return []
        for m in media:
            url = (
                getattr(m, "media_url_https", None)
                or getattr(m, "media_url", None)
                or getattr(m, "preview_image_url", None)
                or getattr(m, "url", None)
            )
            if url and not url.startswith("https://t.co"):
                media_urls.append(url)
    except Exception as e:
        print("media err: " + str(e))
        print(traceback.format_exc())
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
        user = safe_get(tweet, "user")
        return {
            "id": safe_get(tweet, "id", default=""),
            "text": safe_get(tweet, "text", default=""),
            "created_at": safe_get(tweet, "created_at", default=""),
            "user_name": safe_get(user, "name", default="") if user else "",
            "user_screen_name": safe_get(user, "screen_name", default="") if user else "",
            "user_icon": safe_get(user, "profile_image_url", default="") if user else "",
            "like_count": safe_get(tweet, "favorite_count", default=0),
            "retweet_count": safe_get(tweet, "retweet_count", default=0),
            "reply_count": safe_get(tweet, "reply_count", default=0),
            "url": "https://x.com/"
            + (safe_get(user, "screen_name", default="") if user else "")
            + "/status/"
            + safe_get(tweet, "id", default=""),
            "media": get_media_urls(tweet),
        }
    except Exception as e:
        print("tweet_to_dict err: " + str(e))
        print(traceback.format_exc())
        return None


async def main():
    print("fetch start")
    previous = load_existing_output()

    if not COOKIES_STR:
        msg = "X_COOKIES not set"
        print(msg)
        write_output(error=msg)
        raise RuntimeError(msg)

    cookie_dict = parse_cookie_string(COOKIES_STR)
    if not cookie_dict:
        msg = "X_COOKIES could not be parsed"
        print(msg)
        write_output(error=msg)
        raise RuntimeError(msg)

    print("X_COOKIES detected")

    client = Client("ja")
    auth_failed = False
    try:
        client.set_cookies(cookie_dict)
        print("Cookies loaded.")
    except Exception as e:
        auth_failed = True
        msg = "set_cookies failed (details hidden)"
        print(msg)
        print(traceback.format_exc())
        age_days = get_cookie_age_days()
        w_level, w_msg, needs_refresh = compute_cookie_warning(age_days, auth_failed=True)
        write_output(
            error=normalize_error_message(e),
            cookie_warning_level=w_level,
            cookie_warning_message=w_msg,
            needs_cookie_refresh=needs_refresh,
        )
        raise

    columns = []
    partial_error = False
    had_any_success = False

    for lst in LIST_IDS:
        list_id = lst["id"]
        list_label = lst["label"]
        print("fetch list start: " + list_label + " (" + list_id + ")")
        try:
            list_tweets = await client.get_list_tweets(list_id, count=50)
            dicts = [tweet_to_dict(t) for t in list_tweets]
            dicts = [d for d in dicts if d is not None]
            columns.append(
                {
                    "id": "list_" + list_id,
                    "label": list_label,
                    "icon": "📋",
                    "tweets": dicts,
                }
            )
            had_any_success = True
            print("ok " + list_label + ": " + str(len(dicts)))
        except Exception as e:
            partial_error = True
            if is_auth_error(e):
                auth_failed = True
            raw_err_msg = str(e)
            err_msg = normalize_error_message(e)
            print("err " + list_label + ": " + raw_err_msg)
            print(traceback.format_exc())

            previous_col = get_previous_column(previous, list_id)
            fallback_tweets = previous_col.get("tweets", []) if previous_col else []
            columns.append(
                {
                    "id": "list_" + list_id,
                    "label": list_label,
                    "icon": "📋",
                    "tweets": fallback_tweets,
                    "error": err_msg,
                    "raw_error": raw_err_msg,
                    "stale": True,
                }
            )

    age_days = get_cookie_age_days()
    w_level, w_msg, needs_refresh = compute_cookie_warning(age_days, auth_failed)
    last_success_at = now_iso() if had_any_success else None

    write_output(
        columns=columns,
        updated_at=now_iso(),
        partial_error=partial_error,
        last_success_at=last_success_at,
        cookie_warning_level=w_level,
        cookie_warning_message=w_msg,
        needs_cookie_refresh=needs_refresh,
    )
    print("fetch end")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print("fatal: " + str(e))
        print(traceback.format_exc())
        try:
            existing = load_existing_output()
            if not existing.get("error"):
                write_output(error="fatal: " + normalize_error_message(e))
        except Exception as write_err:
            print("failed to write error output: " + str(write_err))
            print(traceback.format_exc())
        sys.exit(1)
