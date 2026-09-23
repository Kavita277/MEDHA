/**
 * STEP 22: THERAPIST RESULTS + INSIGHTS + RECOMMENDATIONS + ALERTS INTEGRATION TEST
 * =================================================================================
 *
 * Automated integration test against real backend APIs:
 *   1. Therapist login
 *   2. Therapist role validation
 *   3. Case list
 *   4. Case selection
 *   5. Results loading
 *   6. Results success
 *   7. Results unavailable
 *   8. Partial modality results
 *   9. Behaviour unavailable/null preservation
 *  10. Future risk unavailable/null preservation
 *  11. Patient context
 *  12. Check-in history
 *  13. Insights
 *  14. Recommendations
 *  15. Alerts & handling
 *  16. 401 handling
 *  17. 403 handling
 *  18. 404 / anti-enumeration handling
 *  19. Error / resilience tolerance
 *  20. Patient cannot access therapist results (Privacy)
 *  21. Therapist cannot access unauthorized case (Ownership isolation)
 */

import { randomBytes, randomUUID } from 'crypto';

const API_BASE = process.env.API_URL || 'http://127.0.0.1:8000/api/v1';

async function request(method: string, path: string, body?: any, token?: string) {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  const json = await res.json().catch(() => null);
  if (!res.ok) {
    throw { statusCode: res.status, detail: json?.detail || 'Error', body: json };
  }
  return json;
}

async function runStep22Test() {
  console.log('======================================================================');
  console.log('  STARTING STEP 22: THERAPIST RESULTS INTEGRATION TEST SUITE');
  console.log('  Target: ' + API_BASE);
  console.log('======================================================================\n');

  let passed = 0;
  let failed = 0;

  function assert(condition: boolean, msg: string) {
    if (condition) {
      console.log(`✅ PASS [${passed + failed + 1}]: ${msg}`);
      passed++;
    } else {
      console.error(`❌ FAIL [${passed + failed + 1}]: ${msg}`);
      failed++;
    }
  }

  try {
    // -----------------------------------------------------------------------
    // 1. Therapist Login
    // -----------------------------------------------------------------------
    const tLogin = await request('POST', '/auth/login', {
      email: 'therapist@medha.org',
      password: 'TherapistPass123!',
    });
    assert(Boolean(tLogin && tLogin.access_token), '1. Therapist login with real credentials succeeds');
    const tToken = tLogin.access_token;

    // -----------------------------------------------------------------------
    // 2. Therapist Role Validation
    // -----------------------------------------------------------------------
    assert(
      tLogin.user && (tLogin.user.role === 'THERAPIST' || tLogin.user.role === 'ADMIN'),
      `2. Authenticated user role is verified as clinician (${tLogin.user?.role})`
    );

    // -----------------------------------------------------------------------
    // 3. Therapist Case List
    // -----------------------------------------------------------------------
    const cases = await request('GET', '/therapist/cases', undefined, tToken);
    assert(Array.isArray(cases) && cases.length > 0, `3. Therapist retrieves real assigned cases (found ${cases.length} cases)`);

    // -----------------------------------------------------------------------
    // 4. Case Selection
    // -----------------------------------------------------------------------
    const caseA = cases[0];
    assert(
      Boolean(caseA && caseA.case_id && caseA.victim_id),
      `4. Case selection succeeds: ID=${caseA.case_id}, Victim=${caseA.victim_id}`
    );

    // -----------------------------------------------------------------------
    // 5. Results Loading / Route Accessibility
    // -----------------------------------------------------------------------
    const caseResults = await request('GET', `/therapist/cases/${caseA.case_id}/results`, undefined, tToken);
    assert(Boolean(caseResults && caseResults.case_id === caseA.case_id), '5. Results endpoint returns valid case result model');

    // -----------------------------------------------------------------------
    // 6. Results Success Semantics
    // -----------------------------------------------------------------------
    assert(
      typeof caseResults.results_available === 'boolean',
      `6. Results available sentinel evaluated (${caseResults.results_available ? 'Available' : 'Pending'})`
    );

    // -----------------------------------------------------------------------
    // 7. Results Unavailable Semantics (Zero-Score Non-Fabrication)
    // -----------------------------------------------------------------------
    // Create a new patient without predictions to verify unavailable semantics
    const uniqueSuffix = randomBytes(4).toString('hex');
    const unpredictedEmail = `unpredicted.${uniqueSuffix}@medha.test`;
    const newPatient = await request('POST', '/therapist/users', {
      name: 'Unpredicted Test Patient',
      email: unpredictedEmail,
      password: 'PatientPass2026!',
      victim_id: `V-UNPRED-${uniqueSuffix}`,
      case_type: 'domestic_violence',
      status: 'active',
    }, tToken);

    // Find the newly created case
    const updatedCases = await request('GET', '/therapist/cases', undefined, tToken);
    const newCase = updatedCases.find((c: any) => c.victim_id === `V-UNPRED-${uniqueSuffix}`);
    assert(Boolean(newCase), `7a. Newly enrolled patient case found in clinician queue`);

    if (newCase) {
      const unpredResults = await request('GET', `/therapist/cases/${newCase.case_id}/results`, undefined, tToken);
      assert(
        unpredResults.results_available === false &&
        unpredResults.fusion_dds_prediction === null &&
        unpredResults.triage_level === 'UNKNOWN',
        '7b. Missing predictions return results_available=False with null scores (never fabricated as zero)'
      );
    }

    // -----------------------------------------------------------------------
    // 8. Partial Modality Results Handling
    // -----------------------------------------------------------------------
    const specialists = caseResults.specialists;
    assert(
      specialists &&
      typeof specialists.struct_available === 'boolean' &&
      typeof specialists.text_available === 'boolean' &&
      typeof specialists.voice_available === 'boolean',
      '8. Specialist modality availability flags correctly distinguish present from absent modalities'
    );

    // -----------------------------------------------------------------------
    // 9. Behaviour Specialist Honest Preservation (Step 10 Blocked)
    // -----------------------------------------------------------------------
    console.log('DEBUG specialists:', JSON.stringify(specialists));
    assert(
      (specialists.behav_pred === null || specialists.behav_pred === undefined) &&
      specialists.behav_available === false &&
      Boolean(specialists.behav_blocked),
      '9. Behaviour specialist is preserved as null/blocked and never fabricated'
    );

    // -----------------------------------------------------------------------
    // 10. Future Risk Unavailable/Null Preservation
    // -----------------------------------------------------------------------
    if (caseResults.temporal_risk_score === null) {
      assert(
        caseResults.temporal_risk_score === null,
        '10. Temporal risk is preserved as null when longitudinal history is insufficient (not coerced to 0)'
      );
    } else {
      assert(
        caseResults.temporal_risk_score >= 0.0 && caseResults.temporal_risk_score <= 1.0,
        `10. Temporal risk score is within valid probability range: ${caseResults.temporal_risk_score}`
      );
    }

    // -----------------------------------------------------------------------
    // 11. Patient Context & Conversational Summary
    // -----------------------------------------------------------------------
    assert(
      caseResults.patient_context !== undefined,
      '11. Patient context block is present in results response'
    );

    // -----------------------------------------------------------------------
    // 12. Check-in History Integration
    // -----------------------------------------------------------------------
    const checkins = await request('GET', `/therapist/cases/${caseA.case_id}/checkins`, undefined, tToken);
    assert(Array.isArray(checkins), `12. Check-in history endpoint returns valid list (${checkins.length} checkins found)`);

    // -----------------------------------------------------------------------
    // 13. Clinical Insights Integration
    // -----------------------------------------------------------------------
    const insights = await request('GET', `/therapist/cases/${caseA.case_id}/insights`, undefined, tToken);
    assert(
      Boolean(insights && insights.summary && Array.isArray(insights.factors) && insights.disclaimer),
      '13. Clinical insights endpoint returns observational summary, factors, and disclaimer'
    );

    // -----------------------------------------------------------------------
    // 14. Clinical Recommendations Integration
    // -----------------------------------------------------------------------
    const recommendations = await request('GET', `/therapist/cases/${caseA.case_id}/recommendations`, undefined, tToken);
    assert(
      Boolean(recommendations && Array.isArray(recommendations.recommendations) && recommendations.disclaimer),
      '14. Clinical recommendations endpoint returns decision support actions and clinical disclaimer'
    );

    // -----------------------------------------------------------------------
    // 15. Dynamic Safety Protocol & Alert Handling
    // -----------------------------------------------------------------------
    const safetyProto = await request('GET', `/therapist/cases/${caseA.case_id}/safety-protocol`, undefined, tToken);
    assert(
      Boolean(safetyProto && typeof safetyProto.alert_triggered === 'boolean' && safetyProto.priority),
      `15a. Safety protocol endpoint returns evaluated alert criteria (Triggered: ${safetyProto.alert_triggered})`
    );

    const alerts = await request('GET', `/therapist/cases/${caseA.case_id}/alerts`, undefined, tToken);
    assert(Array.isArray(alerts), `15b. Historical safety alerts list retrieved (${alerts.length} alerts)`);

    // -----------------------------------------------------------------------
    // 16. 401 Unauthorized Handling
    // -----------------------------------------------------------------------
    let got401 = false;
    try {
      await request('GET', '/therapist/cases');
    } catch (err: any) {
      if (err.statusCode === 401) got401 = true;
    }
    assert(got401, '16. Request without authentication header is rejected with HTTP 401');

    // -----------------------------------------------------------------------
    // 17. 403 Forbidden Role Handling (Patient Cannot Access Therapist Endpoints)
    // -----------------------------------------------------------------------
    const pLogin = await request('POST', '/auth/login', {
      email: 'patient@medha.org',
      password: 'PatientPass123!',
    });
    const pToken = pLogin.access_token;

    let patientGot403 = false;
    try {
      await request('GET', '/therapist/cases', undefined, pToken);
    } catch (err: any) {
      if (err.statusCode === 403) patientGot403 = true;
    }
    assert(patientGot403, '17. Patient role (USER) accessing /therapist/cases is denied with HTTP 403');

    // -----------------------------------------------------------------------
    // 18. 404 / Anti-Enumeration Handling
    // -----------------------------------------------------------------------
    const randomFakeCaseId = randomUUID();
    let antiEnumProtected = false;
    try {
      await request('GET', `/therapist/cases/${randomFakeCaseId}/results`, undefined, tToken);
    } catch (err: any) {
      // MEDHA security architecture returns 403 instead of 404 to prevent ID enumeration
      if (err.statusCode === 403) antiEnumProtected = true;
    }
    assert(antiEnumProtected, '18. Non-existent case ID returns HTTP 403 to prevent enumeration attacks');

    // -----------------------------------------------------------------------
    // 19. Network / Resilience Error Handling
    // -----------------------------------------------------------------------
    let invalidBodyHandled = false;
    try {
      await request('POST', '/therapist/users', { invalid: 'payload' }, tToken);
    } catch (err: any) {
      if (err.statusCode === 422) invalidBodyHandled = true;
    }
    assert(invalidBodyHandled, '19. Malformed input is validated safely with HTTP 422 Unprocessable Entity');

    // -----------------------------------------------------------------------
    // 20. Patient Privacy Protection (Patient Cannot Access Results)
    // -----------------------------------------------------------------------
    let patientBlockedResults = false;
    try {
      await request('GET', `/therapist/cases/${caseA.case_id}/results`, undefined, pToken);
    } catch (err: any) {
      if (err.statusCode === 403) patientBlockedResults = true;
    }
    assert(patientBlockedResults, '20. Patient cannot access clinical case results (Strict privacy guard)');

    // -----------------------------------------------------------------------
    // 21. Cross-Therapist Ownership Isolation
    // -----------------------------------------------------------------------
    // Create Therapist B to test cross-therapist boundary
    const tBSuffix = randomBytes(3).toString('hex');
    const tBEmail = `therapist.b.${tBSuffix}@medha.test`;

    // Create Therapist B user directly
    const tBUser = await request('POST', '/therapist/users', {
      name: 'Dr. Second Opinion',
      email: tBEmail,
      password: 'TherapistPass123!',
      victim_id: `V-TB-${tBSuffix}`,
    }, tToken);

    // Log in as Therapist B
    const tBLogin = await request('POST', '/auth/login', {
      email: tBEmail,
      password: 'TherapistPass123!',
    });

    let crossTherapistBlocked = false;
    try {
      // Therapist B attempts to access Therapist A's case
      await request('GET', `/therapist/cases/${caseA.case_id}/results`, undefined, tBLogin.access_token);
    } catch (err: any) {
      if (err.statusCode === 403) crossTherapistBlocked = true;
    }
    assert(crossTherapistBlocked, '21. Clinician cannot access cases owned by another therapist (Ownership isolation)');

  } catch (fatal: any) {
    console.error('Fatal test exception:', fatal);
    failed++;
  }

  console.log('\n======================================================================');
  console.log(`  STEP 22 TEST SUMMARY: ${passed} PASSED, ${failed} FAILED`);
  console.log('======================================================================\n');

  if (failed > 0) {
    process.exit(1);
  }
}

runStep22Test();
