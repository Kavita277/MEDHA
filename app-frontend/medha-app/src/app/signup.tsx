import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { COLORS } from '../constants/colors';
import { authService } from '../services/api';

export default function PatientLoginScreen() {
  const [email, setEmail] = useState('ananya.sharma@medha.org');
  const [password, setPassword] = useState('PatientPass123!');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSignIn = async () => {
    if (!email || !password || loading) return;
    setError(null);
    setLoading(true);

    try {
      await authService.login(email.trim(), password);
      router.replace('/home' as any);
    } catch (err: any) {
      setError(err?.message || 'Invalid patient credentials. Please verify with your therapist.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
      >
        <Pressable
          onPress={() => router.back()}
          style={styles.back}
          accessibilityRole="button"
          accessibilityLabel="Back"
        >
          <Ionicons
            name="arrow-back"
            size={19}
            color={COLORS.deepForest}
          />
        </Pressable>

        <Text style={styles.eyebrow}>PATIENT PORTAL</Text>
        <Text style={styles.title}>Patient Sign In</Text>

        <Text style={styles.subtitle}>
          Sign in with the confidential credentials provided by your assigned clinician.
        </Text>

        {error && (
          <View style={styles.errorBox}>
            <Ionicons name="alert-circle-outline" size={16} color="#c62828" />
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {/* CREDENTIALS FORM */}
        <Text style={styles.inputLabel}>PATIENT EMAIL</Text>
        <TextInput
          placeholder="e.g. ananya.sharma@medha.org"
          placeholderTextColor="#8A8A82"
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          keyboardType="email-address"
          style={styles.input}
        />

        <Text style={styles.inputLabel}>PASSWORD</Text>
        <View style={styles.passwordContainer}>
          <TextInput
            placeholder="Enter password"
            placeholderTextColor="#8A8A82"
            value={password}
            onChangeText={setPassword}
            secureTextEntry={!showPassword}
            style={styles.passwordInput}
          />

          <Pressable onPress={() => setShowPassword(!showPassword)} hitSlop={10}>
            <Ionicons
              name={showPassword ? 'eye-off-outline' : 'eye-outline'}
              size={18}
              color="#777970"
            />
          </Pressable>
        </View>

        <Pressable
          onPress={handleSignIn}
          disabled={loading || !email || !password}
          style={({ pressed }) => [
            styles.signInButton,
            (!email || !password) && styles.buttonDisabled,
            pressed && styles.pressed,
          ]}
        >
          {loading ? (
            <ActivityIndicator color={COLORS.white} size="small" />
          ) : (
            <Text style={styles.signInText}>Sign In to MEDHA</Text>
          )}
        </Pressable>

        {/* CLINICIAN NAVIGATION */}
        <View style={styles.therapistNotice}>
          <Ionicons name="shield-checkmark-outline" size={16} color={COLORS.forest} />
          <Text style={styles.therapistNoticeText}>
            Public registration is disabled. Patient accounts are created strictly by verified clinicians.
          </Text>
        </View>

        <Pressable
          onPress={() => router.push('/therapist-login' as any)}
          style={styles.therapistLink}
        >
          <Text style={styles.therapistLinkText}>
            Are you a clinician? <Text style={styles.therapistLinkBold}>Sign in to Therapist Portal →</Text>
          </Text>
        </Pressable>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },

  content: {
    paddingHorizontal: 24,
    paddingTop: 55,
    paddingBottom: 35,
  },

  back: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },

  eyebrow: {
    fontFamily: 'Inter-Medium',
    color: COLORS.forest,
    fontSize: 10,
    letterSpacing: 2,
    marginBottom: 6,
  },

  title: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 36,
    lineHeight: 40,
    color: COLORS.deepForest,
  },

  subtitle: {
    fontFamily: 'Inter-Regular',
    fontSize: 13,
    lineHeight: 20,
    color: COLORS.mutedText,
    marginTop: 8,
    marginBottom: 24,
  },

  errorBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#ffebee',
    padding: 12,
    borderRadius: 12,
    marginBottom: 16,
  },

  errorText: {
    color: '#c62828',
    fontSize: 11,
    fontFamily: 'Inter-Regular',
    flex: 1,
  },

  inputLabel: {
    fontFamily: 'Inter-Medium',
    fontSize: 9,
    letterSpacing: 1.5,
    color: COLORS.deepForest,
    marginBottom: 6,
    marginTop: 6,
  },

  input: {
    height: 48,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: COLORS.border,
    backgroundColor: COLORS.surface,
    paddingHorizontal: 16,
    fontFamily: 'Inter-Regular',
    fontSize: 13,
    color: COLORS.text,
    marginBottom: 14,
  },

  passwordContainer: {
    height: 48,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: COLORS.border,
    backgroundColor: COLORS.surface,
    flexDirection: 'row',
    alignItems: 'center',
    paddingRight: 15,
    marginBottom: 24,
  },

  passwordInput: {
    flex: 1,
    paddingHorizontal: 16,
    fontFamily: 'Inter-Regular',
    fontSize: 13,
    color: COLORS.text,
  },

  signInButton: {
    height: 52,
    borderRadius: 26,
    backgroundColor: COLORS.forest,
    alignItems: 'center',
    justifyContent: 'center',
  },

  buttonDisabled: {
    backgroundColor: COLORS.lichen,
  },

  signInText: {
    fontFamily: 'Inter-Medium',
    color: COLORS.white,
    fontSize: 13,
  },

  pressed: {
    opacity: 0.75,
    transform: [{ scale: 0.98 }],
  },

  therapistNotice: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 9,
    backgroundColor: COLORS.surfaceWarm,
    borderRadius: 14,
    padding: 14,
    marginTop: 28,
    borderWidth: 1,
    borderColor: COLORS.border,
  },

  therapistNoticeText: {
    flex: 1,
    color: COLORS.mutedText,
    fontFamily: 'Inter-Regular',
    fontSize: 10,
    lineHeight: 15,
  },

  therapistLink: {
    alignItems: 'center',
    marginTop: 22,
    paddingVertical: 8,
  },

  therapistLinkText: {
    fontFamily: 'Inter-Regular',
    fontSize: 11,
    color: COLORS.mutedText,
  },

  therapistLinkBold: {
    fontFamily: 'Inter-Medium',
    color: COLORS.deepForest,
  },
});