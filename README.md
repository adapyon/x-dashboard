# x-dashboard

X (Twitter) のリストをまとめて表示するプライベートダッシュボードです。  
GitHub Actions が 15 分ごとにツイートを取得し、GitHub Pages で表示します。

---

## ダッシュボードの状態表示

ページ上部のステータスバーで現在の取得状況を確認できます。

| 表示 | 意味 | 対応 |
|---|---|---|
| ● 正常 | 全リストの取得成功 | 不要 |
| ● 一部失敗 | 一部リストの取得に失敗（前回値を表示中） | 次回実行を待つ、または原因を調べる |
| ● 更新推奨 | X_COOKIES を設定してから 7 日以上経過 | 早めに Cookie を入れ直す |
| ● 要対応 | 認証エラー、または 10 日以上経過 | 下記の手順で Cookie を更新する |

「要対応」が出たらダッシュボードが正常に更新されなくなっています。早めに対応してください。

---

## X_COOKIES 更新手順

### 必要なもの

- Chrome（x.com にログイン済み）
- [X Cookie Exporter 拡張機能](#chrome-拡張機能のセットアップ)（初回のみインストール）
- GitHub リポジトリの管理権限

---

### 手順

#### 1. Chrome 拡張で Cookie を取得する

1. Chrome で `https://x.com` を開き、ログイン済みであることを確認する
2. ツールバーの **X Cookie Exporter** アイコンをクリック
3. `auth_token` / `ct0` など必要な Cookie が ✓ で表示されていることを確認する
4. **「クリップボードへコピー」** ボタンを押す
5. ポップアップが閉じたら Cookie 文字列がクリップボードに入っている

> Cookie の値はポップアップ内でマスク表示されます。コピー後はメモリから消えます。

---

#### 2. GitHub Secrets を更新する

1. GitHub でこのリポジトリを開く
2. **Settings** → **Secrets and variables** → **Actions** を開く
3. **Secrets** タブの `X_COOKIES` を選び **Update secret** をクリック
4. クリップボードの内容を貼り付けて **Save** する

---

#### 3. GitHub Variables を更新する

1. 同じページの **Variables** タブを開く
2. `X_COOKIES_SET_AT` を選び **Edit variable** をクリック
3. 現在時刻を **UTC** で入力して **Save** する

**UTC 変換ルール（JST → UTC）**

```
UTC = JST − 9 時間
例: JST 14:30 → UTC 05:30
```

入力フォーマット例:

```
2026-05-05T05:30:00Z
```

---

#### 4. 動作確認する

1. リポジトリの **Actions** タブを開く
2. **Fetch Tweets** ワークフローを選ぶ
3. **Run workflow** → **Run workflow** をクリック
4. ワークフローが緑で完了したことを確認する
5. ダッシュボードを開いてステータスが **● 正常** になっていることを確認する

---

## Chrome 拡張機能のセットアップ

初回のみ実施します。

1. 以下の3ファイルを同じフォルダ（例: `x-cookie-export/`）に作成する

**manifest.json**

```json
{
  "manifest_version": 3,
  "name": "X Cookie Exporter",
  "version": "1.0",
  "permissions": ["cookies", "clipboardWrite"],
  "host_permissions": ["*://*.x.com/*"],
  "action": {
    "default_popup": "popup.html"
  }
}
```

**popup.html**

```html
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<style>
  body { font-family: monospace; padding: 16px; width: 480px; background: #0d0f14; color: #e8ecf4; }
  h2 { font-size: 14px; margin-bottom: 12px; color: #4f8ef7; }
  #status { font-size: 12px; color: #8890a8; margin-bottom: 8px; }
  #preview { background: #1c2030; border: 1px solid #252a3a; border-radius: 6px;
             padding: 10px; font-size: 11px; word-break: break-all;
             color: #555e7a; margin-bottom: 12px; min-height: 40px; }
  .found { color: #4caf88; }
  .missing { color: #f06292; }
  button { background: #4f8ef7; color: #fff; border: none; padding: 8px 16px;
           border-radius: 6px; cursor: pointer; font-size: 13px; width: 100%; }
  button:hover { background: #7c5af7; }
  button:disabled { background: #252a3a; color: #555e7a; cursor: default; }
  #log { font-size: 10px; color: #555e7a; margin-top: 10px; }
</style>
</head>
<body>
<h2>X Cookie Exporter</h2>
<div id="status">読み込み中...</div>
<div id="preview">--</div>
<button id="copy-btn" disabled>クリップボードへコピー</button>
<div id="log"></div>
<script src="popup.js"></script>
</body>
</html>
```

**popup.js**

```javascript
const NEEDED = ["auth_token", "ct0", "twid", "lang", "guest_id", "kdt"];

let cookieString = "";

function mask(value) {
  if (!value || value.length < 6) return "***";
  return value.slice(0, 3) + "..." + value.slice(-3);
}

async function loadCookies() {
  const statusEl = document.getElementById("status");
  const previewEl = document.getElementById("preview");
  const copyBtn = document.getElementById("copy-btn");
  const logEl = document.getElementById("log");

  try {
    const all = await chrome.cookies.getAll({ domain: "x.com" });
    const map = {};
    for (const c of all) map[c.name] = c.value;

    const found = [], missing = [], parts = [], previewLines = [];

    for (const name of NEEDED) {
      if (map[name]) {
        found.push(name);
        parts.push(`${name}=${map[name]}`);
        previewLines.push(`<span class="found">✓ ${name}</span> = ${mask(map[name])}`);
      } else {
        missing.push(name);
        previewLines.push(`<span class="missing">✗ ${name}</span> = (なし)`);
      }
    }

    cookieString = parts.join("; ");
    previewEl.innerHTML = previewLines.join("<br>");

    if (found.length === 0) {
      statusEl.textContent = "❌ x.com にログインしていないか、Cookie が見つかりません";
      return;
    }

    statusEl.textContent =
      `取得: ${found.length}件  未取得: ${missing.length}件  ` +
      `(値は伏字表示。コピー後は GitHub Secrets へ貼り付け)`;

    copyBtn.disabled = false;
    logEl.textContent = "※ Cookie の値はこのログには記録されません";
  } catch (err) {
    statusEl.textContent = "エラー: " + err.message;
  }
}

document.getElementById("copy-btn").addEventListener("click", async () => {
  if (!cookieString) return;
  await navigator.clipboard.writeText(cookieString);
  const btn = document.getElementById("copy-btn");
  btn.textContent = "✓ コピー完了";
  btn.disabled = true;
  setTimeout(() => window.close(), 1200);
});

loadCookies();
```

2. Chrome で `chrome://extensions` を開く
3. 右上の **デベロッパー モード** をオンにする
4. **「パッケージ化されていない拡張機能を読み込む」** をクリックし、作成したフォルダを選択する

---

## セキュリティ注意事項

- **Cookie 文字列をチャット・メモ帳・Slack などに貼り付けない**
- **コピー後はすぐに別の文字列をコピーしてクリップボードを上書きする**（GitHub への貼り付けが終わったら）
- この拡張機能は Chrome Web Store に公開しない。自分の Chrome にのみインストールして使う
- GitHub Secrets に保存された Cookie は GitHub のサーバーで暗号化される。ログには出力されない

---

## 仕組み

```
Chrome拡張 → クリップボード → GitHub Secrets (X_COOKIES)
                                      ↓
                          GitHub Actions (15分ごと)
                                      ↓
                            fetch_tweets.py が取得
                                      ↓
                            docs/data.json を更新
                                      ↓
                          GitHub Pages でダッシュボード表示
```

data.json には以下のフィールドが含まれます。

| フィールド | 内容 |
|---|---|
| `updated_at` | 最後に data.json を書き込んだ時刻 |
| `last_attempt_at` | 最後に取得を試みた時刻 |
| `last_success_at` | 最後に 1 件以上の取得に成功した時刻 |
| `cookie_warning_level` | `none` / `warning` / `critical` |
| `cookie_warning_message` | ダッシュボードに表示するメッセージ |
| `needs_cookie_refresh` | 認証エラーが発生した場合 `true` |
