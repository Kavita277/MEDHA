/**
 * Root Layout
 * ===========
 *
 * Wraps the entire application in:
 *   1. AuthProvider  — JWT storage, user identity
 *   2. SessionProvider — active backend session for patients
 *
 * Auth restoration gate:
 *   While isLoading is true (auth state is being restored from SecureStore),
 *   we render null to avoid a flash to the login screen on cold start.
 *   Expo Router's splash-screen stays up until the first render resolves.
 */

import { useFonts } from 'expo-font';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';

import {
  CormorantGaramond_300Light,
  CormorantGaramond_400Regular,
} from '@expo-google-fonts/cormorant-garamond';

import {
  Inter_400Regular,
  Inter_500Medium,
  Inter_600SemiBold,
} from '@expo-google-fonts/inter';

import { AuthProvider, useAuth } from '../context/AuthContext';
import { SessionProvider } from '../context/SessionContext';

// ---------------------------------------------------------------------------
// Inner layout — must be inside AuthProvider so it can read auth state
// ---------------------------------------------------------------------------

function InnerLayout() {
  const { isLoading } = useAuth();

  // While auth restoration is pending, render nothing.
  // The Expo splash screen remains visible during this phase.
  if (isLoading) {
    return null;
  }

  return (
    <>
      <StatusBar style="dark" />

      <Stack
        screenOptions={{
          headerShown: false,
          animation: 'fade',
          contentStyle: {
            backgroundColor: '#F3EFE4',
          },
        }}
      />
    </>
  );
}

// ---------------------------------------------------------------------------
// Root layout
// ---------------------------------------------------------------------------

export default function RootLayout() {
  const [fontsLoaded] = useFonts({
    'CormorantGaramond-Light': CormorantGaramond_300Light,
    'CormorantGaramond-Regular': CormorantGaramond_400Regular,

    'Inter-Regular': Inter_400Regular,
    'Inter-Medium': Inter_500Medium,
    'Inter-SemiBold': Inter_600SemiBold,
  });

  if (!fontsLoaded) {
    return null;
  }

  return (
    <AuthProvider>
      <SessionProvider>
        <InnerLayout />
      </SessionProvider>
    </AuthProvider>
  );
}