// Cookie の値はコンソール・ログへ一切出力しない
const REQUIRED = ["auth_token", "ct0"];
const OPTIONAL = ["twid", "lang", "guest_id", "kdt"];
const NEEDED = [...REQUIRED, ...OPTIONAL];

let cookieString = "";

function mask(value) {
  if (!value || value.length < 6) return "***";
  return value.slice(0, 3) + "..." + value.slice(-3);
}

async function getCookiesForDomains() {
  const domains = ["x.com", "twitter.com"];
  const map = {};

  for (const domain of domains) {
    const cookies = await chrome.cookies.getAll({ domain });
    for (const c of cookies) {
      if (!map[c.name]) {
        map[c.name] = c.value;
      }
    }
  }

  return map;
}

function buildStatus(foundRequired, missingRequired, foundOptional, missingOptional) {
  if (foundRequired.length === 0) {
    return "❌ ログインCookieが見つかりません。x.com にログインした状態で開いてください";
  }
  if (missingRequired.length > 0) {
    return `⚠ 必須Cookie不足: ${missingRequired.join(", ")} / 任意: ${foundOptional.length}件取得`;
  }
  return `✅ 必須Cookie取得OK / 任意: ${foundOptional.length}件取得`;
}

async function loadCookies() {
  const statusEl = document.getElementById("status");
  const previewEl = document.getElementById("preview");
  const copyBtn = document.getElementById("copy-btn");
  const logEl = document.getElementById("log");

  try {
    const map = await getCookiesForDomains();

    const foundRequired = [];
    const missingRequired = [];
    const foundOptional = [];
    const missingOptional = [];
    const parts = [];
    const previewLines = [];

    for (const name of REQUIRED) {
      if (map[name]) {
        foundRequired.push(name);
        parts.push(`${name}=${map[name]}`);
        previewLines.push(`<span class="found">✓ ${name}</span> = ${mask(map[name])}`);
      } else {
        missingRequired.push(name);
        previewLines.push(`<span class="missing">✗ ${name}</span> = (なし)`);
      }
    }

    for (const name of OPTIONAL) {
      if (map[name]) {
        foundOptional.push(name);
        parts.push(`${name}=${map[name]}`);
        previewLines.push(`<span class="found">✓ ${name}</span> = ${mask(map[name])}`);
      } else {
        missingOptional.push(name);
        previewLines.push(`<span class="missing">- ${name}</span> = (なし)`);
      }
    }

    cookieString = parts.join("; ");
    previewEl.innerHTML = previewLines.join("<br>");
    statusEl.textContent = buildStatus(foundRequired, missingRequired, foundOptional, missingOptional);

    copyBtn.disabled = foundRequired.length === 0 || missingRequired.length > 0;
    logEl.textContent = "※ Cookie値は画面で伏字表示、ログ保存なし、外部送信なし";
  } catch (err) {
    statusEl.textContent = "エラー: " + err.message;
    copyBtn.disabled = true;
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
