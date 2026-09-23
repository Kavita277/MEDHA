const API_BASE = 'http://localhost:8000/api/v1';
import { randomBytes } from 'crypto';

async function request(method: string, path: string, body?: any, token?: string) {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json'
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined
  });

  const json = await res.json().catch(() => null);
  if (!res.ok) {
    throw { statusCode: res.status, detail: json?.detail || 'Error' };
  }
  return json;
}

async function runTest() {
  console.log("Starting Step 20 Journal Integration Test...");
  let passed = 0;
  let failed = 0;

  function assert(condition: boolean, msg: string) {
    if (condition) {
      console.log(`✅ PASS: ${msg}`);
      passed++;
    } else {
      console.error(`❌ FAIL: ${msg}`);
      failed++;
    }
  }

  try {
    // 0. Setup: Therapist login -> Create Patient
    const tLogin = await request('POST', '/auth/login', {
      email: 'demo.therapist@medha.test',
      password: 'TherapistPass2026!'
    });
    const tToken = tLogin.access_token;
    
    const uniqueSuffix = randomBytes(4).toString('hex');
    const patientEmail = `journal.test.${uniqueSuffix}@medha.test`;
    const patientPass = 'PatientPass2026!';
    
    await request('POST', '/therapist/users', {
      name: "Journal Test Patient",
      email: patientEmail,
      password: patientPass,
      victim_id: `V-TEST-${uniqueSuffix}`
    }, tToken);
    
    console.log(`Created test patient: ${patientEmail}`);

    // 1. Patient login
    const loginRes = await request('POST', '/auth/login', {
      email: patientEmail,
      password: patientPass
    });
    const token = loginRes.access_token;
    assert(!!token, 'Patient login succeeds');

    // 2. Unauthenticated GET /journal returns 401
    try {
      await request('GET', '/journal', undefined, 'invalid_token');
      assert(false, 'Unauthenticated GET /journal should fail');
    } catch (e: any) {
      assert(e.statusCode === 401, 'Unauthenticated GET /journal returns 401');
    }

    // 3. Unauthenticated POST /journal returns 401
    try {
      await request('POST', '/journal', { content: 'test' }, 'invalid_token');
      assert(false, 'Unauthenticated POST /journal should fail');
    } catch (e: any) {
      assert(e.statusCode === 401, 'Unauthenticated POST /journal returns 401');
    }

    // 4. Authenticated journal list
    let listRes = await request('GET', '/journal', undefined, token);
    assert(Array.isArray(listRes.entries), 'Authenticated journal list succeeds and returns array');
    assert(listRes.entries.length === 0, 'Empty journal state is handled');

    // 5. Create journal entry
    const newContent = `Test entry at ${Date.now()}`;
    const createRes = await request('POST', '/journal', { content: newContent }, token);
    assert(!!createRes.id, 'Create journal entry succeeds with real ID');
    assert(createRes.content === newContent, 'Created entry has correct content');

    // 6. GET journal list contains the created entry
    listRes = await request('GET', '/journal', undefined, token);
    const foundInList = listRes.entries.some((e: any) => e.id === createRes.id);
    assert(foundInList, 'GET journal list contains the created entry');

    // 7. GET journal/{id} returns the created entry
    const getRes = await request('GET', `/journal/${createRes.id}`, undefined, token);
    assert(getRes.id === createRes.id && getRes.content === newContent, 'GET journal/{id} returns the created entry');

    // 8. PATCH journal/{id} updates an editable field
    const updatedContent = `${newContent} - UPDATED`;
    const updateRes = await request('PATCH', `/journal/${createRes.id}`, { content: updatedContent }, token);
    assert(updateRes.id === createRes.id && updateRes.content === updatedContent, 'PATCH journal/{id} updates content');

    // 9. GET journal/{id} reflects the update
    const getUpdatedRes = await request('GET', `/journal/${createRes.id}`, undefined, token);
    assert(getUpdatedRes.content === updatedContent, 'GET journal/{id} reflects the update');

    // 10. Invalid journal ID
    try {
      await request('GET', '/journal/00000000-0000-0000-0000-000000000000', undefined, token);
      assert(false, 'Invalid journal ID should fail');
    } catch (e: any) {
      assert(e.statusCode === 404, 'Invalid journal ID returns 404');
    }

    // 11. Invalid payload
    try {
      await request('POST', '/journal', { wrong_field: 'test' }, token);
      assert(false, 'Invalid payload should fail');
    } catch (e: any) {
      assert(e.statusCode === 422, 'Invalid payload produces 422 validation error');
    }

    // 12. Cross-user access rejected
    const secondPatientEmail = `journal.test.two.${uniqueSuffix}@medha.test`;
    await request('POST', '/therapist/users', {
      name: "Journal Test Patient 2",
      email: secondPatientEmail,
      password: patientPass,
      victim_id: `V-TEST2-${uniqueSuffix}`
    }, tToken);
    
    const loginRes2 = await request('POST', '/auth/login', {
      email: secondPatientEmail,
      password: patientPass
    });
    const token2 = loginRes2.access_token;
    
    try {
      await request('GET', `/journal/${createRes.id}`, undefined, token2);
      assert(false, 'Cross-user GET should fail');
    } catch (e: any) {
      assert(e.statusCode === 404 || e.statusCode === 403, 'Cross-user access is rejected (returns 404)');
    }

  } catch (error: any) {
    console.error("Test execution failed abruptly:", error);
    failed++;
  }

  console.log(`\nTest Summary: ${passed} passed, ${failed} failed`);
  if (failed > 0) {
    process.exit(1);
  }
}

runTest();
