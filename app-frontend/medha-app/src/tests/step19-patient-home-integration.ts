/**
 * MEDHA Step 19 — Patient Home Integration Tests
 * ==============================================
 *
 * Verifies that the home screen / dashboard correctly accesses the
 * backend's auth and session endpoints without inventing mocked endpoints.
 *
 * Run from the medha-app directory:
 *   npx tsx src/tests/step19-patient-home-integration.ts
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

async function getJSON(path: string, token: string) {
  const headers: Record<string, string> = { 'Authorization': `Bearer ${token}` };
  const res = await fetch(`${API}${path}`, { method: 'GET', headers });
  return { status: res.status, json: await res.json().catch(() => null) };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

console.log('\n=== MEDHA Step 19 — Patient Home Integration Tests ===\n');

async function main() {
  let patientToken: string | null = null;
  let sessionId: string | null = null;

  // 1. AuthContext Dependencies (Login)
  console.log('▸ AuthContext & User Data (from Step 16)');
  await test('Can login and get patient token', async () => {
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

  await test('Can fetch /auth/me for patient name (Category A data)', async () => {
    const { status, json } = await getJSON('/auth/me', patientToken!);
    assert(status === 200, `Failed to fetch /auth/me: ${status}`);
    assert(!!json.name, 'Name missing from user profile');
  });

  // 2. SessionContext Dependencies (Session)
  console.log('\n▸ SessionContext & Dashboard Widgets');
  await test('SessionContext can create/restore session via POST /sessions', async () => {
    const { status, json } = await postJSON('/sessions', {}, patientToken!);
    assert(status === 201 || status === 200, `Session creation failed: ${status}`);
    sessionId = json.id;
  });

  if (!sessionId) {
    console.error('Fatal: Could not obtain session ID. Aborting tests.');
    process.exit(1);
  }

  // 3. New Step 19 Fetches (GET /sessions/{id})
  await test('Home screen can GET /sessions/{session_id} for state_summary (turn_count)', async () => {
    const { status, json } = await getJSON(`/sessions/${sessionId}`, patientToken!);
    assert(status === 200, `Failed to fetch session metadata: ${status}`);
    assert('state_summary' in json, 'SessionResponse missing state_summary schema field');
    
    // We don't assert turn_count > 0 here since this is just an endpoint structural test,
    // but we ensure the schema doesn't leak internal ML values at the top level
    const disallowedKeys = ['DDS', 'Temporal_Risk', 'Future_Escalation', 'Triage', 'Text_Pred'];
    for (const key of disallowedKeys) {
      assert(!(key in json), `Privacy violation: SessionResponse leaked ${key}`);
      if (json.state_summary) {
        assert(!(key in json.state_summary), `Privacy violation: state_summary leaked ${key}`);
      }
    }
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
