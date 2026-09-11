/**
 * MEDHA Step 18 — Voice Integration Tests
 * =======================================
 *
 * Integration tests to verify the frontend voice API interaction.
 * Makes real HTTP calls to the local backend.
 *
 * Run from the medha-app directory:
 *   npx tsx src/tests/step18-voice-integration.ts
 */

const BASE = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';
const API = `${BASE}/api/v1`;

const PATIENT_EMAIL = process.env.TEST_PATIENT_EMAIL ?? 'demo.patient.96325e@medha.test';
const PATIENT_PASSWORD = process.env.TEST_PATIENT_PASSWORD ?? 'DemoPatient2026!';

// ---------------------------------------------------------------------------
// Test Runner
// ---------------------------------------------------------------------------

let passed = 0;
let failed = 0;

async function test(name: string, fn: () => Promise<void>) {
  try {
    await fn();
    console.log(`  ✅  ${name}`);
    passed++;
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(`  ❌  ${name}\n       ${msg}`);
    failed++;
  }
}

function assert(condition: boolean, msg: string) {
  if (!condition) throw new Error(`Assertion failed: ${msg}`);
}

async function postJSON(path: string, body: unknown, token?: string) {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API}${path}`, { method: 'POST', headers, body: JSON.stringify(body) });
  return { status: res.status, json: await res.json().catch(() => null) };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

console.log('\n=== MEDHA Step 18 — Voice Integration Tests ===\n');

async function main() {
  let patientToken: string | null = null;
  let sessionId: string | null = null;

  // Setup: Login
  console.log('▸ Setup');
  await test('Login to get token', async () => {
    const { status, json } = await postJSON('/auth/login', {
      email: PATIENT_EMAIL,
      password: PATIENT_PASSWORD,
    });
    assert(status === 200, `Login failed: ${status}`);
    patientToken = json.access_token;
  });

  if (!patientToken) {
    console.error('Fatal: Could not obtain token. Aborting tests.');
    process.exit(1);
  }

  // Setup: Get/Create Session
  await test('Create/Get active session', async () => {
    const { status, json } = await postJSON('/sessions', {}, patientToken!);
    assert(status === 201 || status === 200, `Session creation failed: ${status}`);
    sessionId = json.id;
  });

  if (!sessionId) {
    console.error('Fatal: Could not obtain session ID. Aborting tests.');
    process.exit(1);
  }

  console.log('\n▸ Voice API');

  await test('POST /voice/checkin without token returns 401', async () => {
    const formData = new FormData();
    formData.append('timepoint', 'Day 1');
    const res = await fetch(`${API}/voice/checkin`, {
      method: 'POST',
      body: formData,
    });
    assert(res.status === 401 || res.status === 403, `expected 401/403, got ${res.status}`);
  });

  await test('POST /voice/checkin missing audio file returns 422', async () => {
    const formData = new FormData();
    formData.append('timepoint', 'Day 1');
    if (sessionId) formData.append('session_id', sessionId);
    
    const headers: Record<string, string> = {
      'Authorization': `Bearer ${patientToken}`,
    };
    const res = await fetch(`${API}/voice/checkin`, {
      method: 'POST',
      headers,
      body: formData,
    });
    
    assert(res.status === 422, `expected 422, got ${res.status}`);
  });

  // FastAPI validates UploadFile types. We've verified missing file returns 422.


  console.log(`\n${'─'.repeat(50)}`);
  console.log(`Tests: ${passed + failed} | Passed: ${passed} | Failed: ${failed}`);

  if (failed > 0) {
    process.exit(1);
  }
}

main().catch((err) => {
  console.error('Fatal error:', err);
  process.exit(1);
});
