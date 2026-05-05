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
3. ステータスが `✅ 必須Cookie取得OK` と表示されていることを確認する
   - `auth_token` / `ct0`（必須）が `✓` になっていれば OK
   - `twid` / `lang` などの任意 Cookie は `- name = (なし)` でも問題なし
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

初回のみ実施します。拡張ファイルはこのリポジトリの `chrome-extension/` フォルダに含まれています。

### インストール手順

1. このリポジトリをクローンまたは ZIP でダウンロードする
2. Chrome で `chrome://extensions` を開く
3. 右上の **デベロッパー モード** をオンにする
4. **「パッケージ化されていない拡張機能を読み込む」** をクリックし、`chrome-extension/` フォルダを選択する
5. ツールバーに **X Cookie Exporter** が表示されれば完了

### 更新時（拡張ファイルを変更した場合）

1. `git pull` でリポジトリを最新にする
2. `chrome://extensions` を開く
3. **X Cookie Exporter** の 🔄 アイコンをクリックして再読み込みする

### 拡張の仕様（v1.1）

| 項目 | 内容 |
|---|---|
| 対象ドメイン | x.com / twitter.com |
| 必須 Cookie | `auth_token`, `ct0`（これが揃わないとコピー不可） |
| 任意 Cookie | `twid`, `lang`, `guest_id`, `kdt` |
| ステータス表示 | `✅ 必須Cookie取得OK` / `⚠ 必須Cookie不足` / `❌ 未ログイン` |
| データ保存 | なし（ポップアップを閉じるとメモリから消える） |
| 外部送信 | なし |

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
