import React, { useState } from 'react';
import {
  Alert,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';
import { RADIUS, SHADOW, TOP_HEADER_PADDING } from '../constants/theme';
import { MedhaScreenBackground } from '../components/medha-screen-background';

type AppearanceMode = 'light' | 'dark' | 'system';

const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'Hindi' },
];

export default function SettingsScreen() {
  const router = useRouter();
  const [appearance, setAppearance] = useState<AppearanceMode>('light');
  const [language, setLanguage] = useState(LANGUAGES[0]);
  const [languageModal, setLanguageModal] = useState(false);
  const [dataPrivacyModal, setDataPrivacyModal] = useState(false);
  const [privacyExpanded, setPrivacyExpanded] = useState(false);

  const handleAccessibility = () => {
    Alert.alert(
      'Accessibility',
      'High-contrast readable typography and screen reader accessibility labels are enabled across all MEDHA screens.',
      [{ text: 'OK' }]
    );
  };

  const handleAbout = () => {
    Alert.alert(
      'About MEDHA',
      'MEDHA: A compassionate, evidence-grounded companion for mental wellbeing and mindful reflection.\n\nVersion 1.0.0 (Production Build)\nAll rights reserved.',
      [{ text: 'Close' }]
    );
  };

  return (
    <View style={styles.root}>
      <MedhaScreenBackground />
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.container}>
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* TOP BAR */}
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
              <Ionicons name="arrow-back" size={20} color={COLORS.navy} />
            </Pressable>
          </View>

          {/* SCREEN HEADER */}
          <View style={styles.header}>
            <Text style={styles.title}>Settings</Text>
            <Text style={styles.subtitle}>
              Customize your experience, preferences, and private space.
            </Text>
          </View>

          {/* APPEARANCE SECTION MATCHING REFERENCE SCREEN 27 */}
          <View style={styles.sectionCard}>
            <View style={styles.sectionHeaderRow}>
              <View style={[styles.sectionIconBadge, { backgroundColor: '#FFF4D6' }]}>
                <Ionicons name="color-palette-outline" size={18} color="#CCA01A" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.sectionLabel}>Appearance</Text>
                <Text style={styles.sectionSubLabel}>Choose how MEDHA looks</Text>
              </View>
            </View>

            {/* Segmented Control */}
            <View style={styles.segmentedControl}>
              {(['light', 'dark', 'system'] as AppearanceMode[]).map((mode) => {
                const isSelected = appearance === mode;
                const label =
                  mode === 'light' ? 'Light' : mode === 'dark' ? 'Dark' : 'System';

                return (
                  <Pressable
                    key={mode}
                    onPress={() => setAppearance(mode)}
                    style={[
                      styles.segmentBtn,
                      isSelected && styles.segmentBtnSelected,
                    ]}
                    accessibilityRole="tab"
                    accessibilityState={{ selected: isSelected }}
                  >
                    <Text
                      style={[
                        styles.segmentText,
                        isSelected && styles.segmentTextSelected,
                      ]}
                    >
                      {label}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          </View>

          {/* PREFERENCES GROUP MATCHING REFERENCE SCREEN 27 */}
          <View style={styles.menuGroup}>
            {/* Language */}
            <Pressable
              onPress={() => setLanguageModal(true)}
              style={({ pressed }) => [
                styles.menuItem,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Language"
            >
              <View style={[styles.menuIconBadge, { backgroundColor: '#EDE7FB' }]}>
                <Ionicons name="language-outline" size={18} color="#7856D6" />
              </View>
              <Text style={styles.menuTitle}>Language</Text>
              <Text style={styles.menuValueText}>{language.label}</Text>
              <Ionicons name="chevron-forward" size={18} color={COLORS.navyMuted} />
            </Pressable>

            {/* Notifications */}
            <Pressable
              onPress={() => router.push('/notifications')}
              style={({ pressed }) => [
                styles.menuItem,
                styles.menuItemBorder,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Notifications"
            >
              <View style={[styles.menuIconBadge, { backgroundColor: '#FFEADB' }]}>
                <Ionicons name="notifications-outline" size={18} color="#E66A35" />
              </View>
              <Text style={styles.menuTitle}>Notifications</Text>
              <Ionicons name="chevron-forward" size={18} color={COLORS.navyMuted} />
            </Pressable>

            {/* Data & Privacy */}
            <Pressable
              onPress={() => setPrivacyExpanded((prev) => !prev)}
              style={({ pressed }) => [
                styles.menuItem,
                styles.menuItemBorder,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Data and Privacy"
              accessibilityState={{ expanded: privacyExpanded }}
            >
              <View style={[styles.menuIconBadge, { backgroundColor: '#E4F6EB' }]}>
                <Ionicons name="shield-outline" size={18} color="#2D8A4E" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.menuTitle}>Data & Privacy</Text>
                <Text style={styles.menuSubText}>How MEDHA uses your information</Text>
              </View>
              <Ionicons
                name={privacyExpanded ? 'chevron-up' : 'chevron-down'}
                size={18}
                color={COLORS.navyMuted}
              />
            </Pressable>

            {/* EXPANDABLE "HOW MEDHA USES YOUR INFORMATION" SECTION */}
            {privacyExpanded && (
              <View style={styles.privacyExpandBox}>
                <Text style={styles.privacyExpandTitle}>
                  How MEDHA uses your information
                </Text>

                <View style={styles.privacyPoint}>
                  <View style={styles.privacyPointDot} />
                  <Text style={styles.privacyPointText}>
                    <Text style={styles.privacyPointBold}>Wellbeing Support: </Text>
                    MEDHA is designed to support wellbeing and connect users with appropriate human support when helpful.
                  </Text>
                </View>

                <View style={styles.privacyPoint}>
                  <View style={styles.privacyPointDot} />
                  <Text style={styles.privacyPointText}>
                    <Text style={styles.privacyPointBold}>Understanding Patterns: </Text>
                    Some information is used to understand emotional and reflection patterns over time.
                  </Text>
                </View>

                <View style={styles.privacyPoint}>
                  <View style={styles.privacyPointDot} />
                  <Text style={styles.privacyPointText}>
                    <Text style={styles.privacyPointBold}>User Control: </Text>
                    Optional monitoring features and check-in preferences can be controlled directly by you.
                  </Text>
                </View>

                <View style={styles.privacyPoint}>
                  <View style={styles.privacyPointDot} />
                  <Text style={styles.privacyPointText}>
                    <Text style={styles.privacyPointBold}>Not a Diagnostic Tool: </Text>
                    MEDHA is not a diagnostic tool and does not provide clinical diagnoses.
                  </Text>
                </View>

                <View style={styles.privacyPoint}>
                  <View style={styles.privacyPointDot} />
                  <Text style={styles.privacyPointText}>
                    <Text style={styles.privacyPointBold}>Professional Review: </Text>
                    AI-generated concerns are reviewed by designated professionals rather than being treated as a diagnosis.
                  </Text>
                </View>

                <View style={styles.privacyPoint}>
                  <View style={styles.privacyPointDot} />
                  <Text style={styles.privacyPointText}>
                    <Text style={styles.privacyPointBold}>Safety Process: </Text>
                    Emergency or safety concerns may require human review according to the app’s safety process.
                  </Text>
                </View>
              </View>
            )}

            {/* Accessibility */}
            <Pressable
              onPress={handleAccessibility}
              style={({ pressed }) => [
                styles.menuItem,
                styles.menuItemBorder,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Accessibility"
            >
              <View style={[styles.menuIconBadge, { backgroundColor: '#E8F2FA' }]}>
                <Ionicons name="accessibility-outline" size={18} color="#2B7CB0" />
              </View>
              <Text style={styles.menuTitle}>Accessibility</Text>
              <Ionicons name="chevron-forward" size={18} color={COLORS.navyMuted} />
            </Pressable>

            {/* Quick Support Access (Distress PIN) */}
            <Pressable
              onPress={() => router.push('/distress-pin')}
              style={({ pressed }) => [
                styles.menuItem,
                styles.menuItemBorder,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Quick Support Distress PIN"
            >
              <View style={[styles.menuIconBadge, { backgroundColor: '#EDE7FB' }]}>
                <Ionicons name="key-outline" size={18} color="#7856D6" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.menuTitle}>Quick Support Access</Text>
                <Text style={styles.menuSubText}>Verify personal Distress PIN</Text>
              </View>
              <Ionicons name="chevron-forward" size={18} color={COLORS.navyMuted} />
            </Pressable>

            {/* About MEDHA */}
            <Pressable
              onPress={handleAbout}
              style={({ pressed }) => [
                styles.menuItem,
                styles.menuItemBorder,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="About MEDHA"
            >
              <View style={[styles.menuIconBadge, { backgroundColor: '#EDE7FB' }]}>
                <Ionicons name="information-circle-outline" size={18} color="#7856D6" />
              </View>
              <Text style={styles.menuTitle}>About MEDHA</Text>
              <Ionicons name="chevron-forward" size={18} color={COLORS.navyMuted} />
            </Pressable>
          </View>
        </ScrollView>
      </View>

      {/* LANGUAGE SELECTOR MODAL */}
      <Modal
        visible={languageModal}
        transparent
        animationType="fade"
        onRequestClose={() => setLanguageModal(false)}
      >
        <View style={styles.overlay}>
          <View style={styles.modalCard}>
            <Text style={styles.modalEyebrow}>LANGUAGE PREFERENCE</Text>
            <Text style={styles.modalTitle}>Choose Language</Text>
            <Text style={styles.modalSub}>
              Select the language you prefer for reflection guides and interface text.
            </Text>

            {LANGUAGES.map((item) => {
              const selected = item.code === language.code;
              return (
                <Pressable
                  key={item.code}
                  style={[
                    styles.languageOption,
                    selected && styles.languageOptionSelected,
                  ]}
                  onPress={() => {
                    setLanguage(item);
                    setLanguageModal(false);
                  }}
                >
                  <Text
                    style={[
                      styles.languageText,
                      selected && styles.languageTextSelected,
                    ]}
                  >
                    {item.label}
                  </Text>
                  {selected && (
                    <Ionicons name="checkmark" size={18} color={COLORS.navy} />
                  )}
                </Pressable>
              );
            })}

            <Pressable
              onPress={() => setLanguageModal(false)}
              style={styles.modalCloseBtn}
            >
              <Text style={styles.modalCloseText}>Done</Text>
            </Pressable>
          </View>
        </View>
      </Modal>

      {/* DATA & PRIVACY MODAL */}
      <Modal
        visible={dataPrivacyModal}
        transparent
        animationType="fade"
        onRequestClose={() => setDataPrivacyModal(false)}
      >
        <View style={styles.overlay}>
          <View style={styles.modalCard}>
            <Text style={styles.modalEyebrow}>DATA & PRIVACY</Text>
            <Text style={styles.modalTitle}>How MEDHA uses your information</Text>
            <Text style={styles.modalSub}>
              • MEDHA is designed to support wellbeing and connect users with appropriate human support when helpful.{'\n\n'}
              • Some information is used to understand emotional and reflection patterns over time.{'\n\n'}
              • Optional monitoring features can be controlled directly by you.{'\n\n'}
              • MEDHA is not a diagnostic tool.{'\n\n'}
              • AI-generated concerns are reviewed by designated professionals rather than being treated as a diagnosis.{'\n\n'}
              • Emergency and safety concerns may require human review according to the app’s safety process.
            </Text>

            <Pressable
              onPress={() => setDataPrivacyModal(false)}
              style={styles.modalCloseBtn}
            >
              <Text style={styles.modalCloseText}>Done</Text>
            </Pressable>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: COLORS.porcelain,
  },
  safeArea: {
    flex: 1,
    backgroundColor: 'transparent',
  },
  container: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 20,
    paddingTop: TOP_HEADER_PADDING,
    paddingBottom: 36,
  },

  /* TOP BAR */
  topBar: {
    paddingVertical: 8,
  },
  iconButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    alignItems: 'center',
    justifyContent: 'center',
    ...SHADOW.subtle,
  },

  /* HEADER */
  header: {
    marginTop: 12,
    marginBottom: 20,
  },
  title: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 26,
    lineHeight: 32,
    color: COLORS.navy,
  },
  subtitle: {
    fontFamily: 'Nunito-Regular',
    fontSize: 13,
    lineHeight: 18,
    color: COLORS.navyMuted,
    marginTop: 4,
  },

  /* APPEARANCE SECTION */
  sectionCard: {
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.card,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    padding: 16,
    marginBottom: 16,
    ...SHADOW.subtle,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 14,
  },
  sectionIconBadge: {
    width: 36,
    height: 36,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sectionLabel: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 15,
    color: COLORS.navy,
  },
  sectionSubLabel: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    color: COLORS.navyMuted,
    marginTop: 1,
  },
  segmentedControl: {
    flexDirection: 'row',
    backgroundColor: COLORS.porcelain,
    borderRadius: RADIUS.pill,
    padding: 4,
    gap: 4,
  },
  segmentBtn: {
    flex: 1,
    height: 38,
    borderRadius: RADIUS.pill,
    alignItems: 'center',
    justifyContent: 'center',
  },
  segmentBtnSelected: {
    backgroundColor: COLORS.white,
    ...SHADOW.subtle,
  },
  segmentText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 13,
    color: COLORS.navyMuted,
  },
  segmentTextSelected: {
    fontFamily: 'Fredoka-Medium',
    color: COLORS.navy,
  },

  /* MENU GROUP */
  menuGroup: {
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.card,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    overflow: 'hidden',
    ...SHADOW.subtle,
  },
  menuItem: {
    minHeight: 58,
    paddingHorizontal: 16,
    paddingVertical: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  menuItemBorder: {
    borderTopWidth: 1,
    borderTopColor: 'rgba(0, 0, 0, 0.04)',
  },
  menuIconBadge: {
    width: 36,
    height: 36,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  menuTitle: {
    flex: 1,
    fontFamily: 'Nunito-SemiBold',
    fontSize: 14,
    color: COLORS.navy,
  },
  menuValueText: {
    fontFamily: 'Nunito-Regular',
    fontSize: 13,
    color: COLORS.navyMuted,
    marginRight: 4,
  },
  menuSubText: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    color: COLORS.navyMuted,
    marginTop: 2,
  },
  privacyExpandBox: {
    backgroundColor: '#F8FAF9',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0, 0, 0, 0.05)',
  },
  privacyExpandTitle: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 14.5,
    color: COLORS.navy,
    marginBottom: 10,
  },
  privacyPoint: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    marginBottom: 8,
  },
  privacyPointDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#2D8A4E',
    marginTop: 6,
  },
  privacyPointText: {
    flex: 1,
    fontFamily: 'Nunito-Regular',
    fontSize: 12.5,
    lineHeight: 18,
    color: COLORS.navy,
  },
  privacyPointBold: {
    fontFamily: 'Nunito-Bold',
    color: COLORS.navy,
  },

  /* CLINICAL GROUP */
  clinicalGroup: {
    marginTop: 16,
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.card,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    overflow: 'hidden',
    ...SHADOW.subtle,
  },

  /* MODALS */
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(24, 30, 44, 0.45)',
    justifyContent: 'flex-end',
  },
  modalCard: {
    backgroundColor: COLORS.white,
    borderTopLeftRadius: RADIUS.modal,
    borderTopRightRadius: RADIUS.modal,
    padding: 24,
    paddingBottom: 36,
  },
  modalEyebrow: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1.2,
    color: COLORS.coralDark,
  },
  modalTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 22,
    color: COLORS.navy,
    marginTop: 6,
  },
  modalSub: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    lineHeight: 18,
    color: COLORS.navyMuted,
    marginTop: 6,
    marginBottom: 16,
  },
  languageOption: {
    minHeight: 50,
    borderRadius: RADIUS.medium,
    backgroundColor: COLORS.porcelain,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
  },
  languageOptionSelected: {
    backgroundColor: '#EDE7FB',
  },
  languageText: {
    flex: 1,
    fontFamily: 'Nunito-SemiBold',
    fontSize: 14,
    color: COLORS.navy,
  },
  languageTextSelected: {
    color: '#7856D6',
    fontFamily: 'Fredoka-Medium',
  },
  modalCloseBtn: {
    height: 48,
    borderRadius: RADIUS.pill,
    backgroundColor: COLORS.navy,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 20,
  },
  modalCloseText: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 14,
    color: COLORS.white,
  },

  pressed: {
    transform: [{ scale: 0.98 }],
    opacity: 0.88,
  },
});
