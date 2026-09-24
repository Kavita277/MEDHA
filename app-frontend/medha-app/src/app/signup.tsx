import React, { useState } from 'react';
import {
  Platform,
  Pressable,
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { RADIUS, SHADOW } from '../constants/theme';

export default function SignupScreen() {
  const router = useRouter();

  const [name, setName] = useState('');
  const [mobile, setMobile] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [focusedField, setFocusedField] = useState<string | null>(null);

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="dark-content" backgroundColor="#FAF9F6" />
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        {/* TOP BAR: BACK BUTTON */}
        <View style={styles.topBar}>
          <Pressable
            onPress={() => router.back()}
            style={({ pressed }) => [
              styles.iconButton,
              pressed && styles.pressed,
            ]}
            hitSlop={12}
            accessibilityRole="button"
            accessibilityLabel="Back"
          >
            <Ionicons name="arrow-back" size={20} color="#181E2C" />
          </Pressable>
        </View>

        {/* HEADER */}
        <View style={styles.header}>
          <Text style={styles.eyebrow}>GET STARTED</Text>
          <Text style={styles.title}>Create your account</Text>
          <Text style={styles.subtitle}>
            Your journey to a calmer you begins here.
          </Text>
        </View>

        {/* SOCIAL LOGIN */}
        <View style={styles.socialGroup}>
          <Pressable
            style={({ pressed }) => [
              styles.socialButton,
              pressed && styles.pressed,
            ]}
            accessibilityRole="button"
            accessibilityLabel="Continue with Google"
          >
            <View style={[styles.socialIconCircle, { backgroundColor: '#FFEBF1' }]}>
              <Ionicons name="logo-google" size={17} color="#E05375" />
            </View>
            <Text style={styles.socialText}>Continue with Google</Text>
          </Pressable>

          <Pressable
            style={({ pressed }) => [
              styles.socialButton,
              pressed && styles.pressed,
            ]}
            accessibilityRole="button"
            accessibilityLabel="Continue with Apple"
          >
            <View style={[styles.socialIconCircle, { backgroundColor: '#EEE9FA' }]}>
              <Ionicons name="logo-apple" size={18} color="#181E2C" />
            </View>
            <Text style={styles.socialText}>Continue with Apple</Text>
          </Pressable>
        </View>

        {/* DIVIDER */}
        <View style={styles.orRow}>
          <View style={styles.orLine} />
          <Text style={styles.orText}>or enter your details</Text>
          <View style={styles.orLine} />
        </View>

        {/* FORM INPUTS */}
        <View style={styles.form}>
          {/* Name Input */}
          <View
            style={[
              styles.inputContainer,
              focusedField === 'name' && styles.inputContainerFocused,
            ]}
          >
            <View style={[styles.fieldIconBadge, { backgroundColor: '#E1F2FE' }]}>
              <Ionicons name="person-outline" size={16} color="#0284C7" />
            </View>
            <TextInput
              placeholder="Full Name"
              placeholderTextColor="#8E97A8"
              value={name}
              onChangeText={setName}
              onFocus={() => setFocusedField('name')}
              onBlur={() => setFocusedField(null)}
              style={styles.input}
              autoCapitalize="words"
            />
          </View>

          {/* Mobile Number Input */}
          <View
            style={[
              styles.inputContainer,
              focusedField === 'mobile' && styles.inputContainerFocused,
            ]}
          >
            <View style={[styles.fieldIconBadge, { backgroundColor: '#E2F5E8' }]}>
              <Ionicons name="call-outline" size={16} color="#2D8A4E" />
            </View>
            <TextInput
              placeholder="Mobile Number"
              placeholderTextColor="#8E97A8"
              keyboardType="phone-pad"
              value={mobile}
              onChangeText={setMobile}
              onFocus={() => setFocusedField('mobile')}
              onBlur={() => setFocusedField(null)}
              style={styles.input}
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

          {/* PRIMARY CREATE ACCOUNT BUTTON */}
          <Pressable
            onPress={() => router.replace('/personalize')}
            style={({ pressed }) => [
              styles.createButton,
              pressed && styles.pressed,
            ]}
            accessibilityRole="button"
            accessibilityLabel="Create Account"
          >
            <Text style={styles.createText}>Create Account</Text>
            <Ionicons name="arrow-forward" size={18} color="#FFFFFF" />
          </Pressable>
        </View>

        {/* TERMS & PRIVACY */}
        <Text style={styles.terms}>
          By creating an account, you agree to our{'\n'}
          <Text style={styles.termsBold}>Terms of Service</Text> and{' '}
          <Text style={styles.termsBold}>Privacy Policy</Text>.
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: '#FAF9F6',
  },
  scrollContent: {
    paddingHorizontal: 22,
    paddingTop: Platform.OS === 'android' ? (StatusBar.currentHeight ?? 24) + 10 : 12,
    paddingBottom: 40,
  },

  /* TOP BAR */
  topBar: {
    height: 48,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  iconButton: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    alignItems: 'center',
    justifyContent: 'center',
    ...SHADOW.subtle,
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

  /* SOCIAL GROUP */
  socialGroup: {
    gap: 10,
    marginBottom: 16,
  },
  socialButton: {
    height: 52,
    borderRadius: 18,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.06)',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 16,
    ...SHADOW.subtle,
  },
  socialIconCircle: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  socialText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 14,
    color: '#181E2C',
  },

  /* DIVIDER */
  orRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 18,
  },
  orLine: {
    flex: 1,
    height: 1,
    backgroundColor: 'rgba(24, 30, 44, 0.08)',
  },
  orText: {
    fontFamily: 'Nunito-Medium',
    fontSize: 12,
    color: '#8E97A8',
    marginHorizontal: 12,
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
    borderColor: '#FF735C',
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

  /* CREATE BUTTON */
  createButton: {
    height: 54,
    borderRadius: RADIUS.pill,
    backgroundColor: '#FF735C',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 8,
    ...SHADOW.subtle,
  },
  createText: {
    fontFamily: 'Fredoka-SemiBold',
    color: '#FFFFFF',
    fontSize: 15,
  },

  /* TERMS */
  terms: {
    textAlign: 'center',
    color: '#8E97A8',
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    lineHeight: 17,
    marginTop: 20,
  },
  termsBold: {
    fontFamily: 'Nunito-Bold',
    color: '#181E2C',
  },

  pressed: {
    transform: [{ scale: 0.98 }],
    opacity: 0.88,
  },
});