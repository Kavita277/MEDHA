/**
 * MEDHA Step 17 — Chat Integration Tests
 * ======================================
 *
 * Integration tests to verify the frontend chat API interaction.
 * Makes real HTTP calls to the local backend.
 *
 * Run from the medha-app directory:
 *   npx tsx src/tests/step17-chat-integration.ts
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

async function getJSON(path: string, token?: string) {
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API}${path}`, { headers });
  return { status: res.status, json: await res.json().catch(() => null) };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

console.log('\n=== MEDHA Step 17 — Chat Integration Tests ===\n');

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
    // 201 Created or 200 OK (if we modified the endpoint to return existing).
    // The current backend endpoint might return 400 or 201 depending on how it's implemented.
    // If they already have an active session, let's try to fetch it.
    // Actually, in step 16, POST /sessions created the session.
    assert(status === 201 || status === 200, `Session creation failed: ${status}`);
    sessionId = json.id;
  });

  if (!sessionId) {
    console.error('Fatal: Could not obtain session ID. Aborting tests.');
    process.exit(1);
  }

  console.log('\n▸ Chat API');

  await test('GET /history returns 200 and messages array', async () => {
    const { status, json } = await getJSON(`/chat/sessions/${sessionId}/history`, patientToken!);
    assert(status === 200, `expected 200, got ${status}`);
    assert(Array.isArray(json?.messages), 'messages should be an array');
  });

  await test('POST /message with missing message returns 422', async () => {
    const { status } = await postJSON(`/chat/sessions/${sessionId}/message`, {}, patientToken!);
    assert(status === 422, `expected 422, got ${status}`);
  });

  await test('POST /message with valid text returns 200 and assistant response', async () => {
    const { status, json } = await postJSON(
      `/chat/sessions/${sessionId}/message`,
      { message: 'Hello, this is a test from step 17.' },
      patientToken!
    );
    assert(status === 200, `expected 200, got ${status}`);
    assert(json?.user_message === 'Hello, this is a test from step 17.', 'user_message mismatch');
    assert(typeof json?.assistant_response === 'string', 'missing assistant_response');
    
    // Check privacy semantics (should not leak ML internals like risk scores)
    assert(json?.risk_score === undefined, 'ML internals (risk_score) leaked!');
    assert(json?.dds === undefined, 'ML internals (dds) leaked!');
  });

  await test('GET /history without token returns 401', async () => {
    const { status } = await getJSON(`/chat/sessions/${sessionId}/history`);
    assert(status === 401 || status === 403, `expected 401/403, got ${status}`);
  });

  await test('POST /message without token returns 401', async () => {
    const { status } = await postJSON(
      `/chat/sessions/${sessionId}/message`,
      { message: 'Unauthorized test' }
    );
    assert(status === 401 || status === 403, `expected 401/403, got ${status}`);
  });

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
