import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { MedhaScreen } from '../components/medha-screen';
import { COLORS } from '../constants/colors';
import { authService } from '../services/api';

export default function TherapistLoginScreen() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (loginEmail?: string, loginPassword?: string) => {
    const targetEmail = (loginEmail || email).trim();
    const targetPass = loginPassword || password;

    if (!targetEmail || !targetPass) {
      setError('Please enter your work email and password.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await authService.login(targetEmail, targetPass);
      const role = (data.user?.role || '').toUpperCase();
      if (role !== 'THERAPIST' && role !== 'ADMIN') {
        setError('Access restricted: Authorized clinician role required.');
        setLoading(false);
        return;
      }
      router.replace('/therapist' as any);
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleDemo = () => {
    handleLogin('demo.therapist@medha.org', 'TherapistDemo123!');
  };

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

      {error && (
        <View style={{ backgroundColor: '#ffebee', padding: 12, borderRadius: 12, marginBottom: 8 }}>
          <Text style={{ color: '#c62828', fontSize: 11, fontFamily: 'Inter-Medium' }}>{error}</Text>
        </View>
      )}

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
        style={[styles.login, loading && { opacity: 0.7 }]}
        onPress={() => handleLogin()}
        disabled={loading}
      >
        <Text style={styles.loginText}>{loading ? 'Authenticating...' : 'Sign in'}</Text>
        <Ionicons name="arrow-forward" size={17} color={COLORS.white} />
      </Pressable>

      <View style={styles.demo}>
        <Text style={styles.demoTitle}>Verified clinician access</Text>
        <Text style={styles.demoText}>
          Authenticate using verified clinical seed credentials to review assigned active cases.
        </Text>
        <Pressable onPress={handleDemo} style={styles.demoButton} disabled={loading}>
          <Text style={styles.demoButtonText}>Sign in as Demo Clinician (demo.therapist@medha.org)</Text>
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
