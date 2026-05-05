// Cookie の値はコンソール・ログへ一切出力しない
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

    const found = [];
    const missing = [];
    const parts = [];
    const previewLines = [];

    for (const name of NEEDED) {
      if (map[name]) {
        found.push(name);
        parts.push(`${name}=${map[name]}`);
        previewLines.push(
          `<span class="found">✓ ${name}</span> = ${mask(map[name])}`
        );
      } else {
        missing.push(name);
        previewLines.push(
          `<span class="missing">✗ ${name}</span> = (なし)`
        );
      }
    }

    cookieString = parts.join("; ");
    previewEl.innerHTML = previewLines.join("<br>");

    if (found.length === 0) {
      statusEl.textContent = "❌ x.com にログインしていないか、Cookie が見つかりません";
      return;
    }

    statusEl.textContent =
      `取得: ${found.length}件  未取得: ${missing.length}件` +
      ` — 値は伏字表示。コピー後は GitHub Secrets へ貼り付けてください`;

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
  // ポップアップを閉じると cookieString はメモリから消える
  setTimeout(() => window.close(), 1200);
});

loadCookies();
