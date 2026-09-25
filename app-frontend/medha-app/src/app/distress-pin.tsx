import React, { useState } from 'react';
import {
  Platform,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  Vibration,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';
import { RADIUS, SHADOW, TOP_HEADER_PADDING } from '../constants/theme';
import { MedhaScreenBackground } from '../components/medha-screen-background';

// Demo-safe local configured distress PIN
const DEFAULT_DISTRESS_PIN = '1234';

export default function DistressPinScreen() {
  const router = useRouter();
  const [pin, setPin] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleDigitPress = (digit: string) => {
    setErrorMsg(null);
    if (pin.length < 4) {
      const nextPin = pin + digit;
      setPin(nextPin);

      // Automatically verify when 4 digits are completed
      if (nextPin.length === 4) {
        verifyPin(nextPin);
      }
    }
  };

  const handleDelete = () => {
    setErrorMsg(null);
    if (pin.length > 0) {
      setPin(pin.slice(0, -1));
    }
  };

  const handleClear = () => {
    setPin('');
    setErrorMsg(null);
  };

  const verifyPin = (enteredPin: string) => {
    if (enteredPin === DEFAULT_DISTRESS_PIN) {
      // Correct PIN: route immediately to the existing Support screen
      if (Platform.OS !== 'web') {
        try {
          Vibration.vibrate(40);
        } catch {
          // ignore vibration errors
        }
      }
      setPin('');
      setErrorMsg(null);
      router.replace('/support');
    } else {
      // Incorrect PIN: provide clear feedback and deny entry to support
      if (Platform.OS !== 'web') {
        try {
          Vibration.vibrate([0, 60, 40, 60]);
        } catch {
          // ignore vibration errors
        }
      }
      setErrorMsg('Incorrect PIN. Please try again.');
      setPin('');
    }
  };

  return (
    <View style={styles.root}>
      <MedhaScreenBackground />
      <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
        <StatusBar barStyle="dark-content" backgroundColor="transparent" />

        {/* TOP BAR */}
        <View style={styles.topBar}>
          <Pressable
            onPress={() => router.back()}
            style={({ pressed }) => [styles.backBtn, pressed && styles.pressed]}
            accessibilityRole="button"
            accessibilityLabel="Back"
          >
            <Ionicons name="arrow-back" size={20} color={COLORS.navy} />
          </Pressable>
          <View style={styles.badge}>
            <Ionicons name="shield-checkmark" size={13} color="#2D8A4E" />
            <Text style={styles.badgeText}>QUICK ACCESS</Text>
          </View>
          <View style={{ width: 40 }} />
        </View>

        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.scrollContent}
        >
          {/* HEADER */}
          <View style={styles.header}>
            <View style={styles.iconWrap}>
              <Ionicons name="key-outline" size={28} color="#7C6EE6" />
            </View>
            <Text style={styles.title}>Quick Support Access</Text>
            <Text style={styles.subtitle}>
              Enter your 4-digit personal Distress PIN to immediately open your Emergency Support space.
            </Text>
          </View>

          {/* PIN DOTS CARD */}
          <View style={styles.card}>
            <View style={styles.dotsRow}>
              {[0, 1, 2, 3].map((index) => {
                const isFilled = pin.length > index;
                return (
                  <View
                    key={index}
                    style={[
                      styles.pinDot,
                      isFilled && styles.pinDotFilled,
                      errorMsg ? styles.pinDotError : null,
                    ]}
                  />
                );
              })}
            </View>

            {errorMsg ? (
              <View style={styles.errorBox}>
                <Ionicons name="alert-circle" size={16} color="#E8663F" />
                <Text style={styles.errorText}>{errorMsg}</Text>
              </View>
            ) : (
              <Text style={styles.hintText}>
                Demo PIN: <Text style={styles.hintCode}>{DEFAULT_DISTRESS_PIN}</Text>
              </Text>
            )}

            {/* KEYPAD */}
            <View style={styles.keypad}>
              {[
                ['1', '2', '3'],
                ['4', '5', '6'],
                ['7', '8', '9'],
              ].map((row, rowIdx) => (
                <View key={rowIdx} style={styles.keypadRow}>
                  {row.map((digit) => (
                    <Pressable
                      key={digit}
                      onPress={() => handleDigitPress(digit)}
                      style={({ pressed }) => [
                        styles.keyBtn,
                        pressed && styles.keyPressed,
                      ]}
                      accessibilityRole="button"
                      accessibilityLabel={`Digit ${digit}`}
                    >
                      <Text style={styles.keyText}>{digit}</Text>
                    </Pressable>
                  ))}
                </View>
              ))}

              {/* BOTTOM ROW: CLEAR, 0, DELETE */}
              <View style={styles.keypadRow}>
                <Pressable
                  onPress={handleClear}
                  style={({ pressed }) => [
                    styles.keyBtn,
                    styles.keyBtnSecondary,
                    pressed && styles.keyPressed,
                  ]}
                  accessibilityRole="button"
                  accessibilityLabel="Clear"
                >
                  <Text style={styles.secondaryKeyText}>Clear</Text>
                </Pressable>

                <Pressable
                  onPress={() => handleDigitPress('0')}
                  style={({ pressed }) => [
                    styles.keyBtn,
                    pressed && styles.keyPressed,
                  ]}
                  accessibilityRole="button"
                  accessibilityLabel="Digit 0"
                >
                  <Text style={styles.keyText}>0</Text>
                </Pressable>

                <Pressable
                  onPress={handleDelete}
                  style={({ pressed }) => [
                    styles.keyBtn,
                    styles.keyBtnSecondary,
                    pressed && styles.keyPressed,
                  ]}
                  accessibilityRole="button"
                  accessibilityLabel="Backspace"
                >
                  <Ionicons name="backspace-outline" size={22} color={COLORS.navy} />
                </Pressable>
              </View>
            </View>
          </View>

          {/* DIRECT SUPPORT ESCALATION */}
          <View style={styles.directSupportCard}>
            <Ionicons name="information-circle-outline" size={18} color="#2D8A4E" />
            <View style={styles.directSupportCopy}>
              <Text style={styles.directSupportTitle}>Need urgent assistance?</Text>
              <Text style={styles.directSupportText}>
                You do not need a PIN in an emergency. You can open verified support helplines directly.
              </Text>
              <Pressable
                onPress={() => router.replace('/support')}
                style={styles.openDirectBtn}
              >
                <Text style={styles.openDirectBtnText}>Open Support & Helplines directly →</Text>
              </Pressable>
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
    fontSize: 10,
    letterSpacing: 0.8,
    color: '#2D8A4E',
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingTop: 14,
  },
  header: {
    alignItems: 'center',
    marginBottom: 20,
  },
  iconWrap: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(124, 110, 230, 0.25)',
    ...SHADOW.card,
  },
  title: {
    fontFamily: 'Fredoka-Bold',
    fontSize: 26,
    color: COLORS.navy,
    letterSpacing: -0.3,
    marginBottom: 6,
    textAlign: 'center',
  },
  subtitle: {
    fontFamily: 'Nunito-Regular',
    fontSize: 13,
    lineHeight: 19,
    color: COLORS.navyMuted,
    textAlign: 'center',
    paddingHorizontal: 16,
  },
  card: {
    backgroundColor: COLORS.white,
    borderRadius: 24,
    padding: 22,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    ...SHADOW.card,
    marginBottom: 16,
  },
  dotsRow: {
    flexDirection: 'row',
    gap: 16,
    marginVertical: 14,
  },
  pinDot: {
    width: 16,
    height: 16,
    borderRadius: 8,
    borderWidth: 2,
    borderColor: '#CAD1DE',
    backgroundColor: 'transparent',
  },
  pinDotFilled: {
    backgroundColor: '#181E2C',
    borderColor: '#181E2C',
  },
  pinDotError: {
    borderColor: '#E8663F',
    backgroundColor: '#FFEADB',
  },
  errorBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#FFEADB',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: RADIUS.pill,
    marginBottom: 14,
  },
  errorText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 12,
    color: '#E8663F',
  },
  hintText: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    color: COLORS.navyMuted,
    marginBottom: 14,
  },
  hintCode: {
    fontFamily: 'Nunito-Bold',
    color: '#7C6EE6',
  },
  keypad: {
    width: '100%',
    gap: 10,
    marginTop: 6,
  },
  keypadRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
  },
  keyBtn: {
    flex: 1,
    height: 56,
    borderRadius: 16,
    backgroundColor: '#F8FAFC',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.04)',
  },
  keyBtnSecondary: {
    backgroundColor: '#F0F2F6',
  },
  keyPressed: {
    backgroundColor: '#E2E8F0',
    transform: [{ scale: 0.96 }],
  },
  keyText: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 22,
    color: COLORS.navy,
  },
  secondaryKeyText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 13,
    color: COLORS.navyMuted,
  },
  directSupportCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    ...SHADOW.card,
  },
  directSupportCopy: {
    flex: 1,
  },
  directSupportTitle: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 14,
    color: COLORS.navy,
  },
  directSupportText: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    lineHeight: 17,
    color: COLORS.navyMuted,
    marginTop: 2,
    marginBottom: 8,
  },
  openDirectBtn: {
    alignSelf: 'flex-start',
  },
  openDirectBtnText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 12,
    color: '#2D8A4E',
  },
  pressed: {
    opacity: 0.85,
    transform: [{ scale: 0.98 }],
  },
});
