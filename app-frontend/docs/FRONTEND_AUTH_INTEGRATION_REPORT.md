# STEP 16 — FRONTEND AUTH + API INTEGRATION REPORT

## 1. Inspection Findings (Pre-Implementation)

| Area | Finding |
|------|---------|
| `package.json` | No HTTP client, no secure storage, no AsyncStorage installed |
| `_layout.tsx` | Simple font loader + Stack navigator, no providers |
| `therapist-login.tsx` | "Prototype access" bypass button pointing directly to `/therapist` |
| `index.tsx` | Splash timer always navigated to `/onboarding` |
| Environment | No `.env.local`, no `EXPO_PUBLIC_API_URL` set |
| No existing contexts, hooks, or services folder | Completely bare integration layer |
| Backend CORS | Allowed only `localhost:3000/8000/8501` — Expo ports missing |
| Auth schema | `POST /auth/login` → `{ email, password }` → `{ access_token, token_type, expires_in, user }` |
| Session schema | `POST /sessions` → `{ case_id?, session_identifier? }` → `SessionResponse { id, case_id, ... }` |
| User roles | `USER` (patient) and `THERAPIST` — same login endpoint, role in returned `user.role` |

---

## 2. Files Created / Modified

### New Files

| File | Purpose |
|------|---------|
| [`api.ts`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/app-frontend/medha-app/src/services/api.ts) | Centralised fetch client with typed errors |
| [`auth.ts`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/app-frontend/medha-app/src/types/auth.ts) | TypeScript types mirroring all backend schemas |
| [`AuthContext.tsx`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/app-frontend/medha-app/src/context/AuthContext.tsx) | JWT storage, user state, login/logout/restore |
| [`SessionContext.tsx`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/app-frontend/medha-app/src/context/SessionContext.tsx) | Session lifecycle for patients |
| [`use-protected-route.ts`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/app-frontend/medha-app/src/hooks/use-protected-route.ts) | `usePatientRoute`, `useTherapistRoute`, `useAuthenticatedRoute` |
| [`login.tsx`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/app-frontend/medha-app/src/app/login.tsx) | Patient login screen (real backend auth) |
| [`.env.local`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/app-frontend/medha-app/.env.local) | `EXPO_PUBLIC_API_URL=http://localhost:8000` |
| [`step16-auth-integration.ts`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/app-frontend/medha-app/src/tests/step16-auth-integration.ts) | 12-test integration suite |

### Modified Files

| File | Change |
|------|--------|
| [`_layout.tsx`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/app-frontend/medha-app/src/app/_layout.tsx) | Wrapped app in `AuthProvider` + `SessionProvider`; added auth restoration gate |
| [`therapist-login.tsx`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/app-frontend/medha-app/src/app/therapist-login.tsx) | Wired to real backend auth; removed prototype bypass |
| [`home.tsx`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/app-frontend/medha-app/src/app/home.tsx) | Added `usePatientRoute()` guard; avatar letter from real user name |
| [`therapist.tsx`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/app-frontend/medha-app/src/app/therapist.tsx) | Added `useTherapistRoute()` guard |
| [`profile.tsx`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/app-frontend/medha-app/src/app/profile.tsx) | Shows real user name + email; added functional logout with Alert |
| [`index.tsx`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/app-frontend/medha-app/src/app/index.tsx) | Splash timer now navigates to `/login` instead of `/onboarding` |
| [`.env`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/.env) | Added `CORS_ORIGINS` with Expo dev server ports (19000, 8081, 19006) |

---

## 3. API Client Architecture

```
api.get(path, { token? })
api.post(path, body, { token? })
api.patch(path, body, { token? })
api.delete(path, { token? })
api.upload(path, formData, { token? })   ← for voice uploads (never sets Content-Type)
```

- Base URL: `EXPO_PUBLIC_API_URL` + `/api/v1`
- Non-2xx → throws `ApiError(statusCode, detail)`
- Network failure → throws `NetworkError`
- JSON responses parsed safely with null fallback
- **No** duplicated fetch logic — all screens use this single client

---

## 4. Auth Architecture

```
Startup:
  SecureStore.getItemAsync('medha_access_token')
      → token found? → GET /auth/me
          → valid → setToken + setUser
          → invalid/401 → deleteItemAsync (clear silently)
      → no token → unauthenticated state

Login:
  POST /api/v1/auth/login  { email, password }
      → 200: SecureStore.setItemAsync + setToken + setUser
      → 401: "Incorrect email or password"
      → 403: "Account restricted"
      → 5xx: "Server error"
      → NetworkError: "No connection"

Logout:
  setToken(null) + setUser(null) + deleteItemAsync
```

**Blind-trust prevention**: Stored token is always validated through `/auth/me` before restoring state.

---

## 5. Token Storage

- **Native (iOS/Android)**: `expo-secure-store` → hardware-backed Keychain / Keystore
- **Web**: `expo-secure-store` automatically falls back to `localStorage` on web
- Key: `medha_access_token`
- Session ID (patient only): `@react-native-async-storage/async-storage`, key `medha_session_id`

---

## 6. Patient Login Flow

1. `/login` screen renders (reached from splash or redirect)
2. User enters email + password
3. `login()` called → `POST /api/v1/auth/login`
4. On success → JWT stored → user in context → `router.replace('/home')`
5. `SessionContext` auto-triggers `POST /api/v1/sessions` for `USER` role
6. `sessionId` is globally available via `useSession()`

Error states: invalid credentials, network failure, server error — all shown inline without exposing raw backend errors.

---

## 7. Therapist Login Flow

1. `/therapist-login` screen renders
2. User enters work email + password
3. `login()` called → same `POST /api/v1/auth/login` endpoint
4. On success → JWT stored → user in context → `router.replace('/therapist')`
5. `useTherapistRoute()` on therapist dashboard: if `user.role !== 'THERAPIST'` → redirect to `/home`
6. Prototype bypass **completely removed**

---

## 8. Role-Based Routing

| Hook | Rule |
|------|------|
| `usePatientRoute()` | `!isAuthenticated` → `/login`; `role === THERAPIST` → `/therapist` |
| `useTherapistRoute()` | `!isAuthenticated` → `/therapist-login`; `role === USER` → `/home` |
| `useAuthenticatedRoute()` | `!isAuthenticated` → `/login` |

Guards run in `useEffect` after auth restoration completes. While `isLoading === true` (auth restoring), no redirect fires — prevents flash to login on cold start.

Applied to: `home.tsx` (patient guard), `therapist.tsx` (therapist guard).

---

## 9. Session Lifecycle

```
Patient Login
    ↓
SessionContext effect fires (isAuthenticated && role === 'USER')
    ↓
AsyncStorage.getItem('medha_session_id')
    ├── Found → restore session ID to state (no new session created)
    └── Not found → POST /api/v1/sessions → store ID → set state
    ↓
sessionId available via useSession() across all screens
    ↓
Logout
    ↓
isAuthenticated becomes false
    ↓
SessionContext clears state + AsyncStorage.removeItem('medha_session_id')
```

**Duplicate creation prevention**: `creatingRef` guard prevents double-firing in React StrictMode.

---

## 10. Error Handling

| Scenario | Behaviour |
|----------|-----------|
| 401 on login | "Incorrect email or password" |
| 403 on login | "Account restricted" |
| 5xx | "Server error. Please try again." |
| Network failure | "Could not reach the server. Check your connection." |
| 401 on `/auth/me` restore | Token cleared silently, user stays unauthenticated |
| 401 on any API call | Screens receive `ApiError(401)` — can redirect to login |
| Session creation fails | Error in SessionContext, `sessionId` remains null |
| Offline | Existing `/offline.tsx` screen available; `NetworkError` caught |

---

## 11. Tests — Results

Executed with real backend (`npx tsx`), no mocking.

```
=== MEDHA Step 16 — Auth & Session Integration Tests ===

▸ API Service
  ✅  Health endpoint responds 200

▸ Patient Authentication
  ✅  POST /auth/login with valid credentials → 200 + access_token
  ✅  POST /auth/login with invalid credentials → 401
  ✅  POST /auth/login with missing fields → 422
  ✅  GET /auth/me with valid token → 200 + USER role
  ✅  GET /auth/me without token → 401/403
  ✅  GET /auth/me with invalid token → 401/403

▸ Therapist Authentication
  ✅  POST /auth/login with therapist credentials → THERAPIST role

▸ Session Lifecycle
  ✅  POST /sessions with patient token → 201 + session
  ✅  GET /sessions/{id} with patient token → 200
  ✅  POST /sessions without token → 401/403
  ✅  Therapist reads own patient's session → 200 (correct; therapist owns case)

Tests: 12 | Passed: 12 | Failed: 0 ✅
```

---

## 12. Backend Changes

Only one change made to the backend:

**[`.env`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/.env)** — Added `CORS_ORIGINS` with Expo dev server ports:
```
http://localhost:19000  (Expo DevTools)
http://localhost:8081   (Expo Metro bundler / React Native Web)
http://localhost:19006  (Expo Web)
```

No FastAPI code, ML models, prediction logic, or therapist result logic was modified.

---

## 13. Known Limitations

| Limitation | Notes |
|------------|-------|
| Patient self-registration not implemented | Backend has no self-reg endpoint; patients are therapist-provisioned. Signup screen still navigates to `/personalize` (unchanged) |
| Physical device | Requires `EXPO_PUBLIC_API_URL` set to LAN IP (`http://192.168.x.x:8000`) — documented in `.env.local` |
| Demo patient passwords | `seed_service.py` seeds patients with `must_change_password=True`; `seed_db.py` users (`patient@medha.org`) work cleanly. Use `seed_db.py` credentials for testing |
| No token refresh | JWT expiry not handled automatically; expired tokens redirect to login |
| Therapist route guard is soft | Logged-in patients who manually navigate to `/therapist` are redirected, but the route is not truly isolated at the Expo Router level |

---

## 14. Next Recommended Frontend Step

**STEP 17: CHAT INTEGRATION**

Wire [`chat.tsx`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/app-frontend/medha-app/src/app/chat.tsx):
- Import `useAuth` and `useSession` — token + sessionId are now available
- Replace the hardcoded `"I'm listening…"` reply with `POST /api/v1/chat/sessions/{sessionId}/message`
- Implement `GET /api/v1/chat/sessions/{sessionId}/history` on mount
- Handle `ApiError(401)` → logout + redirect

This will be the first actual AI-interactive feature working end-to-end.

---

## STEP 16 STATUS: ✅ COMPLETE

All acceptance criteria satisfied:

- [x] Frontend has centralised API service
- [x] JWT is securely persisted (expo-secure-store)
- [x] App restores authentication on restart (validates via /auth/me)
- [x] Patient can perform real backend login
- [x] Therapist can perform real backend login
- [x] Role-based routing works
- [x] Prototype therapist bypass is removed
- [x] Authenticated patient gets a real backend session
- [x] Session ID is globally accessible via `useSession()`
- [x] Logout clears auth + session state
- [x] 401/403/network errors are handled
- [x] No hardcoded JWTs or credentials
- [x] No MEDHA V2/backend ML logic modified
- [x] Existing visual design remains intact
- [x] Tests pass: 12/12
