import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { MedhaScreen } from '../components/medha-screen';
import { COLORS } from '../constants/colors';

export default function TherapistLoginScreen() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  return (
    <MedhaScreen
      eyebrow="THERAPIST WORKSPACE"
      title="A private clinical space."
      subtitle="For authorised clinicians reviewing MEDHA-supported cases."
      onBack={() => router.back()}
    >
      <View style={styles.lock}>
        <Ionicons name="lock-closed-outline" size={25} color={COLORS.forest} />
      </View>

      <TextInput
        value={email}
        onChangeText={setEmail}
        placeholder="Work email"
        placeholderTextColor={COLORS.subtleText}
        autoCapitalize="none"
        keyboardType="email-address"
        style={styles.input}
      />
      <TextInput
        value={password}
        onChangeText={setPassword}
        placeholder="Password"
        placeholderTextColor={COLORS.subtleText}
        secureTextEntry
        style={styles.input}
      />

      <Pressable
        style={styles.login}
        onPress={() => router.replace('/therapist')}
      >
        <Text style={styles.loginText}>Sign in</Text>
        <Ionicons name="arrow-forward" size={17} color={COLORS.white} />
      </Pressable>

      <View style={styles.demo}>
        <Text style={styles.demoTitle}>Prototype access</Text>
        <Text style={styles.demoText}>
          The dashboard is already built, but a real clinician authentication endpoint is not connected to this frontend yet. This button is only for demonstrating the therapist flow.
        </Text>
        <Pressable onPress={() => router.replace('/therapist')} style={styles.demoButton}>
          <Text style={styles.demoButtonText}>Open therapist dashboard</Text>
        </Pressable>
      </View>
    </MedhaScreen>
  );
}

const styles = StyleSheet.create({
  lock: { width: 58, height: 58, borderRadius: 29, backgroundColor: COLORS.mist, alignItems: 'center', justifyContent: 'center', alignSelf: 'center', marginVertical: 15 },
  input: { height: 53, borderRadius: 17, backgroundColor: COLORS.surface, borderWidth: 1, borderColor: COLORS.border, paddingHorizontal: 16, fontFamily: 'Inter-Regular', fontSize: 12, color: COLORS.text, marginTop: 10 },
  login: { height: 54, borderRadius: 27, backgroundColor: COLORS.forest, alignItems: 'center', justifyContent: 'center', flexDirection: 'row', gap: 9, marginTop: 14 },
  loginText: { fontFamily: 'Inter-Medium', fontSize: 13, color: COLORS.white },
  demo: { marginTop: 22, padding: 18, borderRadius: 21, backgroundColor: COLORS.mist },
  demoTitle: { fontFamily: 'CormorantGaramond-Regular', fontSize: 21, color: COLORS.deepForest },
  demoText: { fontFamily: 'Inter-Regular', fontSize: 9, lineHeight: 15, color: COLORS.mutedText, marginTop: 5 },
  demoButton: { alignSelf: 'flex-start', marginTop: 13, paddingHorizontal: 15, paddingVertical: 10, borderRadius: 18, backgroundColor: COLORS.surface },
  demoButtonText: { fontFamily: 'Inter-Medium', fontSize: 9, color: COLORS.forest },
});
