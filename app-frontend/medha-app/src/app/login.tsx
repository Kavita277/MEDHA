/**
 * Patient Login Screen
 * ====================
 *
 * Authenticates a patient (role: USER) against:
 *   POST /api/v1/auth/login
 *
 * On success:
 *   - JWT is persisted (handled by AuthContext)
 *   - Session is created (handled by SessionContext after auth state updates)
 *   - Navigates to /home
 *
 * Handles:
 *   - Invalid credentials (401)
 *   - Suspended/deactivated account (403)
 *   - Network unavailable
 *   - Server errors (5xx)
 *   - Loading state while awaiting response
 */

import React, { useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../constants/colors';
import { useAuth } from '../context/AuthContext';
import { ApiError, NetworkError } from '../services/api';

export default function LoginScreen() {
  const { login, isAuthenticated } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // If already authenticated (e.g. back-navigation), redirect away
  React.useEffect(() => {
    if (isAuthenticated) {
      router.replace('/home');
    }
  }, [isAuthenticated]);

  async function handleLogin() {
    const trimmedEmail = email.trim().toLowerCase();
    const trimmedPassword = password.trim();

    if (!trimmedEmail || !trimmedPassword) {
      setErrorMsg('Please enter your email and password.');
      return;
    }

    setErrorMsg(null);
    setIsLoading(true);

    try {
      await login({ email: trimmedEmail, password: trimmedPassword });
      // login() sets token + user in context; navigate to home
      router.replace('/home');
    } catch (err) {
      // AuthContext.login already sets context error, but we also
      // show it inline on this screen.
      setErrorMsg(resolveMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        {/* ── Header ── */}
        <View style={styles.header}>
          <Text style={styles.eyebrow}>YOUR SPACE</Text>
          <Text style={styles.title}>Welcome back.</Text>
          <Text style={styles.subtitle}>
            Log in to continue your journey with MEDHA.
          </Text>
        </View>

        {/* ── Error banner ── */}
        {errorMsg ? (
          <View style={styles.errorBanner}>
            <Ionicons name="alert-circle-outline" size={16} color={COLORS.support} />
            <Text style={styles.errorText}>{errorMsg}</Text>
          </View>
        ) : null}

        {/* ── Form ── */}
        <View style={styles.form}>
          <TextInput
            value={email}
            onChangeText={setEmail}
            placeholder="Email address"
            placeholderTextColor={COLORS.subtleText}
            autoCapitalize="none"
            keyboardType="email-address"
            returnKeyType="next"
            style={[styles.input, errorMsg ? styles.inputError : null]}
            editable={!isLoading}
          />

          <View style={styles.passwordWrap}>
            <TextInput
              value={password}
              onChangeText={setPassword}
              placeholder="Password"
              placeholderTextColor={COLORS.subtleText}
              secureTextEntry={!showPassword}
              returnKeyType="done"
              onSubmitEditing={handleLogin}
              style={[styles.passwordInput, errorMsg ? styles.inputError : null]}
              editable={!isLoading}
            />
            <Pressable
              onPress={() => setShowPassword((v) => !v)}
              hitSlop={10}
              style={styles.eyeButton}
            >
              <Ionicons
                name={showPassword ? 'eye-off-outline' : 'eye-outline'}
                size={18}
                color={COLORS.mutedText}
              />
            </Pressable>
          </View>

          <Pressable
            onPress={handleLogin}
            disabled={isLoading}
            style={({ pressed }) => [
              styles.loginButton,
              pressed && styles.loginButtonPressed,
              isLoading && styles.loginButtonDisabled,
            ]}
          >
            {isLoading ? (
              <ActivityIndicator color={COLORS.white} size="small" />
            ) : (
              <>
                <Text style={styles.loginButtonText}>Sign in</Text>
                <Ionicons name="arrow-forward" size={18} color={COLORS.white} />
              </>
            )}
          </Pressable>
        </View>

        {/* ── Therapist link ── */}
        <View style={styles.therapistRow}>
          <Text style={styles.therapistHint}>Are you a clinician?</Text>
          <Pressable
            onPress={() => router.push('/therapist-login')}
            hitSlop={8}
          >
            <Text style={styles.therapistLink}>Therapist sign-in →</Text>
          </Pressable>
        </View>

        <Text style={styles.version}>MEDHA · Patient Access · 0.1</Text>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

function resolveMessage(err: unknown): string {
  if (err instanceof NetworkError) {
    return 'Could not reach the server. Please check your connection.';
  }
  if (err instanceof ApiError) {
    if (err.statusCode === 401) return 'Incorrect email or password.';
    if (err.statusCode === 403)
      return 'Your account access has been restricted. Please contact support.';
    if (err.statusCode >= 500) return 'Server error. Please try again shortly.';
    return err.detail;
  }
  if (err instanceof Error && err.message) {
    return err.message;
  }
  return 'Something went wrong. Please try again.';
}

const styles = StyleSheet.create({
  flex: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  content: {
    flexGrow: 1,
    paddingHorizontal: 24,
    paddingTop: 72,
    paddingBottom: 40,
  },
  header: {
    marginBottom: 32,
  },
  eyebrow: {
    fontFamily: 'Inter-Medium',
    fontSize: 9,
    letterSpacing: 2,
    color: COLORS.forest,
    marginBottom: 12,
  },
  title: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 42,
    lineHeight: 44,
    color: COLORS.deepForest,
  },
  subtitle: {
    fontFamily: 'Inter-Regular',
    fontSize: 13,
    lineHeight: 20,
    color: COLORS.mutedText,
    marginTop: 10,
  },
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 9,
    padding: 14,
    borderRadius: 16,
    backgroundColor: '#F5E8E4',
    marginBottom: 18,
  },
  errorText: {
    flex: 1,
    fontFamily: 'Inter-Regular',
    fontSize: 12,
    lineHeight: 18,
    color: COLORS.support,
  },
  form: {
    gap: 11,
  },
  input: {
    height: 52,
    borderRadius: 16,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    paddingHorizontal: 17,
    fontFamily: 'Inter-Regular',
    fontSize: 13,
    color: COLORS.text,
  },
  inputError: {
    borderColor: COLORS.support,
  },
  passwordWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    height: 52,
    borderRadius: 16,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    paddingRight: 14,
  },
  passwordInput: {
    flex: 1,
    height: '100%',
    paddingHorizontal: 17,
    fontFamily: 'Inter-Regular',
    fontSize: 13,
    color: COLORS.text,
    borderRadius: 16,
  },
  eyeButton: {
    padding: 4,
  },
  loginButton: {
    height: 54,
    borderRadius: 27,
    backgroundColor: COLORS.forest,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 9,
    marginTop: 6,
  },
  loginButtonPressed: {
    opacity: 0.82,
    transform: [{ scale: 0.98 }],
  },
  loginButtonDisabled: {
    opacity: 0.6,
  },
  loginButtonText: {
    fontFamily: 'Inter-Medium',
    fontSize: 14,
    color: COLORS.white,
  },
  therapistRow: {
    marginTop: 32,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  therapistHint: {
    fontFamily: 'Inter-Regular',
    fontSize: 11,
    color: COLORS.mutedText,
  },
  therapistLink: {
    fontFamily: 'Inter-Medium',
    fontSize: 11,
    color: COLORS.forest,
  },
  version: {
    textAlign: 'center',
    fontFamily: 'Inter-Regular',
    fontSize: 8,
    color: COLORS.subtleText,
    marginTop: 28,
  },
});
