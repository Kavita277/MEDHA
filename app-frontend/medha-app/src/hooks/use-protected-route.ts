/**
 * useProtectedRoute
 * =================
 *
 * Redirect helpers for route-level role enforcement.
 *
 * Usage:
 *   usePatientRoute()   — inside any patient-only screen
 *   useTherapistRoute() — inside any therapist-only screen
 *
 * While auth is restoring (isLoading === true) neither redirect fires,
 * preventing a flash to the login screen on cold start.
 */

import { useEffect } from 'react';
import { router } from 'expo-router';
import { useAuth } from '../context/AuthContext';

// ---------------------------------------------------------------------------
// Patient route guard — role must be 'USER'
// ---------------------------------------------------------------------------

export function usePatientRoute() {
  const { isAuthenticated, isLoading, user } = useAuth();

  useEffect(() => {
    if (isLoading) return; // Still restoring — wait

    if (!isAuthenticated) {
      // Not logged in → patient login
      router.replace('/login');
      return;
    }

    if (user?.role === 'THERAPIST') {
      // Therapist in a patient-only area → send to their dashboard
      router.replace('/therapist');
    }
  }, [isLoading, isAuthenticated, user?.role]);
}

// ---------------------------------------------------------------------------
// Therapist route guard — role must be 'THERAPIST'
// ---------------------------------------------------------------------------

export function useTherapistRoute() {
  const { isAuthenticated, isLoading, user } = useAuth();

  useEffect(() => {
    if (isLoading) return;

    if (!isAuthenticated) {
      // Not logged in → therapist login
      router.replace('/therapist-login');
      return;
    }

    if (user?.role === 'USER') {
      // Patient trying to access therapist area → deny
      router.replace('/home');
    }
  }, [isLoading, isAuthenticated, user?.role]);
}

// ---------------------------------------------------------------------------
// Generic authenticated guard (any role)
// ---------------------------------------------------------------------------

export function useAuthenticatedRoute() {
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      router.replace('/login');
    }
  }, [isLoading, isAuthenticated]);
}
