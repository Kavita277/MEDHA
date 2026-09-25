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

type UserRole = 'patient' | 'guardian' | 'therapist' | 'admin';

const ROLES: { id: UserRole; label: string; icon: keyof typeof Ionicons.glyphMap; badgeBg: string; badgeColor: string }[] = [
  { id: 'patient', label: 'Patient', icon: 'person-outline', badgeBg: '#E1F2FE', badgeColor: '#0284C7' },
  { id: 'guardian', label: 'Guardian', icon: 'people-outline', badgeBg: '#FFEADB', badgeColor: '#E8663F' },
  { id: 'therapist', label: 'Therapist', icon: 'medkit-outline', badgeBg: '#E2F5E8', badgeColor: '#2D8A4E' },
  { id: 'admin', label: 'Admin', icon: 'shield-outline', badgeBg: '#EEE9FA', badgeColor: '#7C6EE6' },
];

export default function LoginScreen() {
  const router = useRouter();

  const [role, setRole] = useState<UserRole>('patient');
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [focusedField, setFocusedField] = useState<string | null>(null);

  const handleLogin = () => {
    switch (role) {
      case 'therapist':
        router.replace('/therapist');
        break;
      case 'guardian':
        router.replace('/guardian' as any);
        break;
      case 'admin':
        router.replace('/admin' as any);
        break;
      case 'patient':
      default:
        router.replace('/home');
        break;
    }
  };

  const getPlaceholder = () => {
    switch (role) {
      case 'therapist':
        return 'Work Email or Clinician ID';
      case 'guardian':
        return 'Guardian Email or Mobile';
      case 'admin':
        return 'Admin Username or Email';
      case 'patient':
      default:
        return 'Email, Username, or Patient ID';
    }
  };

  return (
    <View style={styles.root}>
      <MedhaScreenBackground />
      <SafeAreaView style={styles.safe}>
        <StatusBar barStyle="dark-content" backgroundColor="transparent" />
        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          {/* HEADER */}
          <View style={styles.header}>
            <Text style={styles.eyebrow}>SIGN IN</Text>
            <Text style={styles.title}>Welcome to MEDHA</Text>
            <Text style={styles.subtitle}>
              Sign in to your private, evidence-grounded companion space.
            </Text>
          </View>

          {/* ROLE SELECTOR */}
          <View style={styles.roleSection}>
            <Text style={styles.roleSectionLabel}>SELECT YOUR ROLE</Text>
            <View style={styles.roleGrid}>
              {ROLES.map((item) => {
                const isSelected = role === item.id;
                return (
                  <Pressable
                    key={item.id}
                    onPress={() => setRole(item.id)}
                    style={({ pressed }) => [
                      styles.roleChip,
                      isSelected && styles.roleChipSelected,
                      pressed && styles.pressed,
                    ]}
                    accessibilityRole="tab"
                    accessibilityState={{ selected: isSelected }}
                    accessibilityLabel={`${item.label} login role`}
                  >
                    <View
                      style={[
                        styles.roleIconCircle,
                        { backgroundColor: isSelected ? 'rgba(255, 255, 255, 0.2)' : item.badgeBg },
                      ]}
                    >
                      <Ionicons
                        name={item.icon}
                        size={16}
                        color={isSelected ? COLORS.white : item.badgeColor}
                      />
                    </View>
                    <Text
                      style={[
                        styles.roleChipText,
                        isSelected && styles.roleChipTextSelected,
                      ]}
                    >
                      {item.label}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          </View>

          {/* FORM INPUTS */}
          <View style={styles.form}>
            {/* Identifier Input */}
            <View
              style={[
                styles.inputContainer,
                focusedField === 'identifier' && styles.inputContainerFocused,
              ]}
            >
              <View style={[styles.fieldIconBadge, { backgroundColor: '#E1F2FE' }]}>
                <Ionicons name="person-circle-outline" size={17} color="#0284C7" />
              </View>
              <TextInput
                placeholder={getPlaceholder()}
                placeholderTextColor="#8E97A8"
                value={identifier}
                onChangeText={setIdentifier}
                onFocus={() => setFocusedField('identifier')}
                onBlur={() => setFocusedField(null)}
                style={styles.input}
                autoCapitalize="none"
              />
            </View>

            {/* Password Input */}
            <View
              style={[
                styles.inputContainer,
                focusedField === 'password' && styles.inputContainerFocused,
              ]}
            >
              <View style={[styles.fieldIconBadge, { backgroundColor: '#FFF4D9' }]}>
                <Ionicons name="lock-closed-outline" size={16} color="#CCA01A" />
              </View>
              <TextInput
                placeholder="Password"
                placeholderTextColor="#8E97A8"
                secureTextEntry={!showPassword}
                value={password}
                onChangeText={setPassword}
                onFocus={() => setFocusedField('password')}
                onBlur={() => setFocusedField(null)}
                style={styles.input}
              />
              <Pressable
                onPress={() => setShowPassword(!showPassword)}
                hitSlop={10}
                style={styles.eyeButton}
                accessibilityRole="button"
                accessibilityLabel={showPassword ? 'Hide password' : 'Show password'}
              >
                <Ionicons
                  name={showPassword ? 'eye-off-outline' : 'eye-outline'}
                  size={18}
                  color="#8E97A8"
                />
              </Pressable>
            </View>

            {/* PRIMARY LOGIN BUTTON (MIDNIGHT NAVY #181E2C) */}
            <Pressable
              onPress={handleLogin}
              style={({ pressed }) => [
                styles.loginButton,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel={`Sign in as ${role}`}
            >
              <Text style={styles.loginText}>
                Sign In as {role.charAt(0).toUpperCase() + role.slice(1)}
              </Text>
              <Ionicons name="arrow-forward" size={18} color="#FFFFFF" />
            </Pressable>
          </View>

          {/* ONBOARDING CARE TEAM NOTICE */}
          <View style={styles.noticeCard}>
            <View style={styles.noticeIconWrap}>
              <Ionicons name="information-circle" size={18} color={COLORS.navyMuted} />
            </View>
            <Text style={styles.noticeText}>
              Patients and families are onboarded by their assigned healthcare professional or clinical care team.
            </Text>
          </View>
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
    backgroundColor: 'transparent',
  },
  scrollContent: {
    paddingHorizontal: 22,
    paddingTop: TOP_HEADER_PADDING + 8,
    paddingBottom: 40,
  },

  /* HEADER */
  header: {
    marginBottom: 24,
  },
  eyebrow: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1.5,
    color: '#FF735C',
    textTransform: 'uppercase',
    marginBottom: 6,
  },
  title: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 28,
    lineHeight: 34,
    color: '#181E2C',
  },
  subtitle: {
    fontFamily: 'Nunito-Regular',
    fontSize: 14,
    lineHeight: 20,
    color: '#5B6478',
    marginTop: 6,
  },

  /* ROLE SELECTOR */
  roleSection: {
    marginBottom: 20,
  },
  roleSectionLabel: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1.4,
    color: '#8E97A8',
    marginBottom: 10,
  },
  roleGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  roleChip: {
    flex: 1,
    minWidth: '47%',
    height: 48,
    borderRadius: 16,
    backgroundColor: '#FFFFFF',
    borderWidth: 1.5,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    gap: 8,
    ...SHADOW.subtle,
  },
  roleChipSelected: {
    backgroundColor: '#181E2C',
    borderColor: '#181E2C',
  },
  roleIconCircle: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  roleChipText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 13,
    color: '#181E2C',
  },
  roleChipTextSelected: {
    color: '#FFFFFF',
    fontFamily: 'Fredoka-Medium',
  },

  /* FORM INPUTS */
  form: {
    gap: 12,
  },
  inputContainer: {
    height: 54,
    borderRadius: 18,
    backgroundColor: '#FFFFFF',
    borderWidth: 1.5,
    borderColor: 'rgba(0, 0, 0, 0.06)',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    ...SHADOW.subtle,
  },
  inputContainerFocused: {
    borderColor: '#181E2C',
  },
  fieldIconBadge: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  input: {
    flex: 1,
    fontFamily: 'Nunito-Regular',
    fontSize: 14,
    color: '#181E2C',
    height: '100%',
  },
  eyeButton: {
    padding: 6,
  },

  /* LOGIN BUTTON (MIDNIGHT NAVY #181E2C) */
  loginButton: {
    height: 54,
    borderRadius: RADIUS.pill,
    backgroundColor: '#181E2C',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 10,
    ...SHADOW.subtle,
  },
  loginText: {
    fontFamily: 'Fredoka-SemiBold',
    color: '#FFFFFF',
    fontSize: 15,
  },

  /* NOTICE CARD */
  noticeCard: {
    marginTop: 24,
    backgroundColor: 'rgba(255, 255, 255, 0.65)',
    borderRadius: RADIUS.card,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    padding: 14,
    flexDirection: 'row',
    gap: 10,
    alignItems: 'center',
  },
  noticeIconWrap: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: 'rgba(24, 30, 44, 0.06)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  noticeText: {
    flex: 1,
    fontFamily: 'Nunito-Regular',
    fontSize: 11.5,
    lineHeight: 16,
    color: '#5B6478',
  },

  pressed: {
    transform: [{ scale: 0.98 }],
    opacity: 0.88,
  },
});
