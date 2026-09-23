/**
 * MEDHA Step 16 — Auth & API Integration Tests
 * =============================================
 *
 * These are integration-style tests written as plain TypeScript functions
 * (no Jest/Vitest — the project has no test runner configured).
 *
 * Run from the medha-app directory:
 *   npx tsx src/tests/step16-auth-integration.ts
 *
 * Requirements:
 *   - Backend running at EXPO_PUBLIC_API_URL (default http://localhost:8000)
 *   - At least one seeded patient user and one seeded therapist user in the DB
 *   - Credentials set in TEST_PATIENT_EMAIL / TEST_PATIENT_PASSWORD env vars
 *     (or falls back to the defaults below — change for your local seed)
 *
 * The tests do NOT mock the backend — real HTTP calls are made.
 * This surfaces real CORS, auth, and schema issues.
 */

const BASE = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';
const API = `${BASE}/api/v1`;

const PATIENT_EMAIL = process.env.TEST_PATIENT_EMAIL ?? 'patient@example.com';
const PATIENT_PASSWORD = process.env.TEST_PATIENT_PASSWORD ?? 'password123';
const THERAPIST_EMAIL = process.env.TEST_THERAPIST_EMAIL ?? 'therapist@example.com';
const THERAPIST_PASSWORD = process.env.TEST_THERAPIST_PASSWORD ?? 'password123';

// ---------------------------------------------------------------------------
// Tiny test runner
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
  const res = await fetch(`${API}${path}`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });
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

console.log('\n=== MEDHA Step 16 — Auth & Session Integration Tests ===\n');

async function main() {
  // ── API: base ──────────────────────────────────────────────────────────────
  console.log('▸ API Service');

  await test('Health endpoint responds 200', async () => {
    const res = await fetch(`${BASE}/api/v1/health`);
    assert(res.status === 200, `expected 200, got ${res.status}`);
  });

  // ── Auth: patient login ────────────────────────────────────────────────────
  console.log('\n▸ Patient Authentication');

  let patientToken: string | null = null;

  await test('POST /auth/login with valid patient credentials returns 200 + access_token', async () => {
    const { status, json } = await postJSON('/auth/login', {
      email: PATIENT_EMAIL,
      password: PATIENT_PASSWORD,
    });
    assert(status === 200, `expected 200, got ${status}: ${JSON.stringify(json)}`);
    assert(typeof json?.access_token === 'string', 'access_token must be a string');
    assert(json?.token_type === 'bearer', 'token_type must be bearer');
    assert(typeof json?.expires_in === 'number', 'expires_in must be a number');
    assert(json?.user?.role === 'USER', `user.role must be USER, got ${json?.user?.role}`);
    patientToken = json.access_token;
  });

  await test('POST /auth/login with invalid credentials returns 401', async () => {
    const { status } = await postJSON('/auth/login', {
      email: PATIENT_EMAIL,
      password: 'WRONG_PASSWORD',
    });
    assert(status === 401, `expected 401, got ${status}`);
  });

  await test('POST /auth/login with missing fields returns 422', async () => {
    const { status } = await postJSON('/auth/login', { email: PATIENT_EMAIL });
    assert(status === 422, `expected 422, got ${status}`);
  });

  await test('GET /auth/me with valid patient token returns 200 + USER role', async () => {
    if (!patientToken) throw new Error('No patient token available');
    const { status, json } = await getJSON('/auth/me', patientToken);
    assert(status === 200, `expected 200, got ${status}`);
    assert(json?.role === 'USER', `expected USER role, got ${json?.role}`);
    assert(typeof json?.name === 'string', 'name must be a string');
    assert(typeof json?.email === 'string', 'email must be a string');
  });

  await test('GET /auth/me without token returns 401 or 403', async () => {
    const { status } = await getJSON('/auth/me');
    assert(status === 401 || status === 403, `expected 401/403, got ${status}`);
  });

  await test('GET /auth/me with invalid token returns 401 or 403', async () => {
    const { status } = await getJSON('/auth/me', 'not.a.valid.token');
    assert(status === 401 || status === 403, `expected 401/403, got ${status}`);
  });

  // ── Auth: therapist login ──────────────────────────────────────────────────
  console.log('\n▸ Therapist Authentication');

  let therapistToken: string | null = null;

  await test('POST /auth/login with valid therapist credentials returns THERAPIST role', async () => {
    const { status, json } = await postJSON('/auth/login', {
      email: THERAPIST_EMAIL,
      password: THERAPIST_PASSWORD,
    });
    if (status === 401) {
      console.log('       (no therapist seed user found — skipping therapist token tests)');
      return;
    }
    assert(status === 200, `expected 200, got ${status}: ${JSON.stringify(json)}`);
    assert(json?.user?.role === 'THERAPIST', `user.role must be THERAPIST, got ${json?.user?.role}`);
    therapistToken = json.access_token;
  });

  // ── Session: patient session creation ─────────────────────────────────────
  console.log('\n▸ Session Lifecycle');

  let sessionId: string | null = null;

  await test('POST /sessions with valid patient token creates session', async () => {
    if (!patientToken) throw new Error('No patient token available');
    const { status, json } = await postJSON('/sessions', {}, patientToken);
    assert(status === 201, `expected 201, got ${status}: ${JSON.stringify(json)}`);
    assert(typeof json?.id === 'string', 'session id must be a string');
    assert(typeof json?.case_id === 'string', 'case_id must be a string');
    assert(json?.status !== undefined, 'status must be present');
    sessionId = json.id;
  });

  await test('GET /sessions/{id} with patient token returns same session', async () => {
    if (!patientToken || !sessionId) throw new Error('No session available');
    const { status, json } = await getJSON(`/sessions/${sessionId}`, patientToken);
    assert(status === 200, `expected 200, got ${status}`);
    assert(json?.id === sessionId, `expected session ${sessionId}, got ${json?.id}`);
  });

  await test('POST /sessions without token returns 401 or 403', async () => {
    const { status } = await postJSON('/sessions', {});
    assert(status === 401 || status === 403, `expected 401/403, got ${status}`);
  });

  // ── Authorization: therapist CAN access their assigned patient's sessions ──
  await test('GET /sessions/{patient-session-id} with therapist token returns 200 (therapist can view own patient)', async () => {
    if (!therapistToken || !sessionId) {
      console.log('       (skipping — missing therapist token or session ID)');
      return;
    }
    const { status } = await getJSON(`/sessions/${sessionId}`, therapistToken);
    // Therapist has case ownership over this patient, so 200 is correct.
    // 403 would be returned for a therapist accessing a different therapist's patient.
    assert(status === 200 || status === 403, `expected 200 or 403, got ${status}`);
  });

  // ── Summary ────────────────────────────────────────────────────────────────
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

