import type { E2EConfig } from 'e2e';
import { web } from '@e2e-dev/web';
import { createOpenAICompatible } from '@ai-sdk/openai-compatible';

import fs from 'node:fs';
import path from 'node:path';

// Load local .env safely without hardcoding secrets in version control
try {
  const envPath = path.resolve(process.cwd(), '.env');
  if (fs.existsSync(envPath)) {
    const lines = fs.readFileSync(envPath, 'utf8').split(/\r?\n/);
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;
      const eqIdx = trimmed.indexOf('=');
      if (eqIdx > 0) {
        const k = trimmed.slice(0, eqIdx).trim();
        const v = trimmed.slice(eqIdx + 1).trim().replace(/^['"]|['"]$/g, '');
        if (!process.env[k]) {
          process.env[k] = v;
        }
      }
    }
  }
} catch {
  // ignore
}

// 9router defaults to text/event-stream unless stream: false is explicitly set in the request JSON
const routerFetch: typeof fetch = async (url, options) => {
  if (options?.body && typeof options.body === 'string') {
    try {
      const parsed = JSON.parse(options.body);
      if (parsed.stream === undefined) {
        parsed.stream = false;
        options.body = JSON.stringify(parsed);
      }
    } catch {
      // ignore
    }
  }
  return fetch(url, options);
};

const router = createOpenAICompatible({
  name: '9router',
  baseURL: process.env.OPENAI_BASE_URL ?? process.env.ROUTER_BASE_URL ?? 'https://9router.chitraparatama.com/v1',
  apiKey: process.env.OPENAI_API_KEY ?? process.env.ROUTER_API_KEY ?? '',
  fetch: routerFetch,
});

export default {
  agents: {
    default: {
      model: router(process.env.E2E_MODEL ?? process.env.OPENAI_MODEL ?? 'cx/gpt-5.6-luna'),
      system: 'You are a thorough QA agent. Verify every outcome on screen.',
    },
  },
  targets: [{
    engine: web(),
    app: {
      url: process.env.APP_URL ?? 'http://127.0.0.1:8765',
    },
  }],
} satisfies E2EConfig;
