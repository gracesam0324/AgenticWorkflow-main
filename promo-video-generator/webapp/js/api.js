/* api.js — Claude API client (browser-direct, no server) + config in localStorage.
 * The API key is NEVER hardcoded; the user enters it via the gear icon.
 * Shared LS namespace (lpg.*) so a key entered in any module/lesson-package app
 * on the same origin is reused. */

const LS_KEY = 'lpg.apiKey';
const LS_MODEL = 'lpg.model';
const DEFAULT_MODEL = 'claude-sonnet-4-6';
const API_URL = 'https://api.anthropic.com/v1/messages';

const Config = {
  getKey() { return localStorage.getItem(LS_KEY) || ''; },
  setKey(v) { v ? localStorage.setItem(LS_KEY, v.trim()) : localStorage.removeItem(LS_KEY); },
  getModel() { return localStorage.getItem(LS_MODEL) || DEFAULT_MODEL; },
  setModel(v) { localStorage.setItem(LS_MODEL, v || DEFAULT_MODEL); },
  hasKey() { return !!this.getKey(); },
};

async function callClaude({ system, user, maxTokens = 8192, signal }) {
  const apiKey = Config.getKey();
  if (!apiKey) throw new ApiError('NO_KEY', 'API 키가 설정되지 않았습니다. 우측 상단 ⚙️에서 입력하세요.');

  const body = {
    model: Config.getModel(),
    max_tokens: maxTokens,
    system,
    messages: [{ role: 'user', content: typeof user === 'string' ? user : JSON.stringify(user, null, 2) }],
  };

  let res;
  try {
    res = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true',
      },
      body: JSON.stringify(body),
      signal,
    });
  } catch (e) {
    if (e.name === 'AbortError') throw e;
    throw new ApiError('NETWORK', '네트워크 오류 또는 CORS 차단입니다. 인터넷 연결과 API 키를 확인하세요.');
  }

  if (!res.ok) {
    let detail = '';
    try { const j = await res.json(); detail = (j.error && j.error.message) || ''; } catch (_) {}
    if (res.status === 401) throw new ApiError('AUTH', 'API 키가 올바르지 않습니다 (401). ⚙️에서 다시 확인하세요.');
    if (res.status === 429) throw new ApiError('RATE', '요청 한도를 초과했습니다 (429). 잠시 후 다시 시도하세요.');
    throw new ApiError('HTTP_' + res.status, `API 오류 ${res.status}: ${detail || res.statusText}`);
  }

  const data = await res.json();
  const text = (data.content || []).map((b) => b.text || '').join('').trim();
  if (!text) throw new ApiError('EMPTY', '응답이 비어 있습니다.');
  return text;
}

function parseJsonResponse(text) {
  let t = text.trim();
  t = t.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/i, '').trim();
  try {
    return JSON.parse(t);
  } catch (_) {
    const start = t.indexOf('{');
    const end = t.lastIndexOf('}');
    if (start !== -1 && end > start) return JSON.parse(t.slice(start, end + 1));
    throw new ApiError('PARSE', '모델 응답을 JSON으로 해석하지 못했습니다.');
  }
}

class ApiError extends Error {
  constructor(code, message) { super(message); this.code = code; this.name = 'ApiError'; }
}
