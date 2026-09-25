import React, { useState } from 'react';
import {
  Platform,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';
import { RADIUS, SHADOW, TOP_HEADER_PADDING } from '../constants/theme';
import { MedhaScreenBackground } from '../components/medha-screen-background';

export default function TherapistLoginScreen() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [focusedField, setFocusedField] = useState<string | null>(null);

  const handleLogin = () => {
    router.replace('/therapist');
  };

  return (
    <View style={styles.root}>
      <MedhaScreenBackground />
      <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
        <StatusBar barStyle="dark-content" backgroundColor="transparent" />

        {/* TOP BAR */}
        <View style={styles.topBar}>
          <Pressable
            onPress={() => router.replace('/login')}
            style={({ pressed }) => [styles.backBtn, pressed && styles.pressed]}
            accessibilityRole="button"
            accessibilityLabel="Back to login"
          >
            <Ionicons name="arrow-back" size={20} color={COLORS.navy} />
          </Pressable>
          <View style={styles.badge}>
            <Ionicons name="medkit" size={13} color="#2D8A4E" />
            <Text style={styles.badgeText}>CLINICIAN PORTAL</Text>
          </View>
          <View style={{ width: 40 }} />
        </View>

        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          {/* HEADER */}
          <View style={styles.header}>
            <View style={styles.logoWrap}>
              <Ionicons name="shield-checkmark" size={32} color="#7C6EE6" />
            </View>
            <Text style={styles.eyebrow}>MEDHA CARE WORKSPACE</Text>
            <Text style={styles.title}>Therapist Workspace</Text>
            <Text style={styles.subtitle}>
              Secure clinician access to patient-consented longitudinal explainability and clinical case reviews.
            </Text>
          </View>

          {/* FORM CARD */}
          <View style={styles.card}>
            {/* Work Email / Clinician ID */}
            <View
              style={[
                styles.inputContainer,
                focusedField === 'email' && styles.inputContainerFocused,
              ]}
            >
              <View style={[styles.fieldIconBadge, { backgroundColor: '#E2F5E8' }]}>
                <Ionicons name="medkit-outline" size={17} color="#2D8A4E" />
              </View>
              <TextInput
                placeholder="Work Email or Clinician ID"
                placeholderTextColor="#8E97A8"
                value={email}
                onChangeText={setEmail}
                onFocus={() => setFocusedField('email')}
                onBlur={() => setFocusedField(null)}
                style={styles.input}
                autoCapitalize="none"
                keyboardType="email-address"
              />
            </View>

            {/* Password */}
            <View
              style={[
                styles.inputContainer,
                focusedField === 'password' && styles.inputContainerFocused,
              ]}
            >
              <View style={[styles.fieldIconBadge, { backgroundColor: '#EEE9FA' }]}>
                <Ionicons name="lock-closed-outline" size={17} color="#7C6EE6" />
              </View>
              <TextInput
                placeholder="Password"
                placeholderTextColor="#8E97A8"
                value={password}
                onChangeText={setPassword}
                onFocus={() => setFocusedField('password')}
                onBlur={() => setFocusedField(null)}
                secureTextEntry={!showPassword}
                style={styles.input}
                autoCapitalize="none"
              />
              <Pressable
                onPress={() => setShowPassword((prev) => !prev)}
                style={styles.eyeBtn}
                hitSlop={10}
              >
                <Ionicons
                  name={showPassword ? 'eye-off-outline' : 'eye-outline'}
                  size={18}
                  color="#8E97A8"
                />
              </Pressable>
            </View>

            {/* LOGIN BUTTON */}
            <Pressable
              onPress={handleLogin}
              style={({ pressed }) => [styles.loginBtn, pressed && styles.pressed]}
              accessibilityRole="button"
              accessibilityLabel="Sign in to Therapist Workspace"
            >
              <Text style={styles.loginBtnText}>Enter Workspace</Text>
              <Ionicons name="arrow-forward" size={18} color="#FFFFFF" />
            </Pressable>
          </View>

          {/* CLINICAL COMPLIANCE REASSURANCE */}
          <View style={styles.complianceCard}>
            <Ionicons name="shield-checkmark-outline" size={18} color="#2D8A4E" />
            <View style={styles.complianceCopy}>
              <Text style={styles.complianceTitle}>ISO/IEC 27001 & HIPAA Aligned</Text>
              <Text style={styles.complianceText}>
                All session notes and explainability insights are encrypted end-to-end. Access events are strictly audited.
              </Text>
            </View>
          </View>

          <View style={{ height: 40 }} />
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: '#FAF3D6',
  },
  safe: {
    flex: 1,
  },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: TOP_HEADER_PADDING - (StatusBar.currentHeight ?? 32) + 6,
    paddingBottom: 10,
  },
  backBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
    alignItems: 'center',
    justifyContent: 'center',
    ...SHADOW.card,
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: RADIUS.pill,
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
  },
  badgeText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 11,
    letterSpacing: 0.8,
    color: '#2D8A4E',
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingTop: 16,
  },
  header: {
    alignItems: 'center',
    marginBottom: 24,
  },
  logoWrap: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(124, 110, 230, 0.25)',
    ...SHADOW.card,
  },
  eyebrow: {
    fontFamily: 'Nunito-Bold',
    fontSize: 12,
    letterSpacing: 1.2,
    color: '#7C6EE6',
    marginBottom: 6,
  },
  title: {
    fontFamily: 'Fredoka-Bold',
    fontSize: 28,
    color: COLORS.navy,
    letterSpacing: -0.3,
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontFamily: 'Nunito-Regular',
    fontSize: 13,
    lineHeight: 19,
    color: COLORS.navyMuted,
    textAlign: 'center',
    paddingHorizontal: 12,
  },
  card: {
    backgroundColor: COLORS.white,
    borderRadius: 24,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    ...SHADOW.card,
    marginBottom: 20,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F8FAFC',
    borderRadius: 16,
    paddingHorizontal: 14,
    paddingVertical: 4,
    marginBottom: 14,
    borderWidth: 1.5,
    borderColor: 'rgba(0, 0, 0, 0.06)',
    minHeight: 54,
  },
  inputContainerFocused: {
    borderColor: '#7C6EE6',
    backgroundColor: COLORS.white,
  },
  fieldIconBadge: {
    width: 32,
    height: 32,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  input: {
    flex: 1,
    fontFamily: 'Nunito-SemiBold',
    fontSize: 14,
    color: COLORS.navy,
  },
  eyeBtn: {
    padding: 6,
  },
  loginBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#181E2C',
    borderRadius: RADIUS.medium,
    paddingVertical: 14,
    marginTop: 6,
  },
  loginBtnText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 15,
    color: '#FFFFFF',
  },
  complianceCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.8)',
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    ...SHADOW.card,
  },
  complianceCopy: {
    flex: 1,
  },
  complianceTitle: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 14,
    color: COLORS.navy,
  },
  complianceText: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    lineHeight: 17,
    color: COLORS.navyMuted,
    marginTop: 2,
  },
  pressed: {
    opacity: 0.85,
    transform: [{ scale: 0.98 }],
  },
});
