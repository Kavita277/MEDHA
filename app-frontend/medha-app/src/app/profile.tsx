import React, { useState } from 'react';
import { Modal, Pressable, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { MedhaScreen } from '../components/medha-screen';
import { COLORS } from '../constants/colors';
import { authService } from '../services/api';

const languages = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'Hindi' },
];

export default function ProfileScreen() {
  const router = useRouter();
  const [language, setLanguage] = useState(languages[0]);
  const [languageModal, setLanguageModal] = useState(false);
  const [user, setUser] = useState<any>(null);

  React.useEffect(() => {
    let active = true;
    authService.getMe()
      .then((data) => {
        if (active && data) setUser(data);
      })
      .catch(() => {});
    return () => { active = false; };
  }, []);

  const handleLogout = () => {
    authService.logout();
    router.replace('/' as any);
  };

  const displayName = user?.name || 'Patient';
  const displayEmail = user?.email || 'Authenticated User';
  const initial = displayName.charAt(0).toUpperCase() || 'P';
  const roleTag = user?.role === 'THERAPIST' ? 'Clinician' : 'Patient';

  return (
    <>
      <MedhaScreen
        eyebrow="Your space"
        title="Profile & settings"
        subtitle="Keep MEDHA feeling like your own quiet corner."
        onBack={() => router.back()}
      >
        <View style={styles.profile}>
          <View style={styles.avatar}><Text style={styles.avatarText}>{initial}</Text></View>
          <View style={{ flex: 1 }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
              <Text style={styles.name}>{displayName}</Text>
              <View style={{ backgroundColor: COLORS.mist, paddingHorizontal: 7, paddingVertical: 2, borderRadius: 8 }}>
                <Text style={{ fontSize: 9, fontFamily: 'Inter-Medium', color: COLORS.forest }}>{roleTag}</Text>
              </View>
            </View>
            <Text style={styles.email}>{displayEmail}</Text>
          </View>
        </View>

        <Text style={styles.section}>PREFERENCES</Text>
        <View style={styles.settings}>
          <View style={styles.setting}>
            <View style={styles.settingIcon}><Ionicons name="notifications-outline" size={18} color={COLORS.forest} /></View>
            <Text style={styles.settingText}>Gentle reminders</Text>
            <View style={styles.toggle}><View style={styles.thumb} /></View>
          </View>

          <Pressable style={styles.setting} onPress={() => setLanguageModal(true)}>
            <View style={styles.settingIcon}><Ionicons name="language-outline" size={18} color={COLORS.forest} /></View>
            <View style={{ flex: 1 }}>
              <Text style={styles.settingText}>Language</Text>
              <Text style={styles.languageValue}>{language.label}</Text>
            </View>
            <Ionicons name="chevron-forward" size={17} color={COLORS.mutedText} />
          </Pressable>

          <Pressable style={styles.setting} onPress={() => router.push('/ambient')}>
            <View style={styles.settingIcon}><Ionicons name="musical-notes-outline" size={18} color={COLORS.forest} /></View>
            <Text style={styles.settingText}>Ambient sound</Text>
            <Ionicons name="chevron-forward" size={17} color={COLORS.mutedText} />
          </Pressable>

          <View style={styles.setting}>
            <View style={styles.settingIcon}><Ionicons name="lock-closed-outline" size={18} color={COLORS.forest} /></View>
            <Text style={styles.settingText}>Privacy & security</Text>
            <Ionicons name="chevron-forward" size={17} color={COLORS.mutedText} />
          </View>
        </View>

        <Text style={styles.section}>SUPPORT</Text>
        <View style={styles.settings}>
          <Pressable style={styles.setting} onPress={() => router.push('/support')}>
            <View style={styles.settingIcon}><Ionicons name="help-circle-outline" size={18} color={COLORS.forest} /></View>
            <Text style={styles.settingText}>Help & feedback</Text>
            <Ionicons name="chevron-forward" size={17} color={COLORS.mutedText} />
          </Pressable>
          <Pressable style={styles.setting} onPress={() => router.push('/therapist-login' as any)}>
            <View style={styles.settingIcon}><Ionicons name="lock-closed-outline" size={18} color={COLORS.forest} /></View>
            <View style={{ flex: 1 }}>
              <Text style={styles.settingText}>Therapist workspace</Text>
              <Text style={styles.languageValue}>For authorised clinicians</Text>
            </View>
            <Ionicons name="chevron-forward" size={17} color={COLORS.mutedText} />
          </Pressable>
        </View>

        <Text style={styles.section}>ACCOUNT</Text>
        <View style={styles.settings}>
          <Pressable style={styles.setting} onPress={handleLogout}>
            <View style={[styles.settingIcon, { backgroundColor: '#ffebee' }]}>
              <Ionicons name="log-out-outline" size={18} color="#c62828" />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={[styles.settingText, { color: '#c62828', fontFamily: 'Inter-Medium' }]}>Log out</Text>
              <Text style={styles.languageValue}>Sign out of this MEDHA account</Text>
            </View>
            <Ionicons name="chevron-forward" size={17} color="#c62828" />
          </Pressable>
        </View>

        <Text style={styles.version}>MEDHA · 0.1 PROTOTYPE</Text>
      </MedhaScreen>

      <Modal visible={languageModal} transparent animationType="fade" onRequestClose={() => setLanguageModal(false)}>
        <View style={styles.overlay}>
          <View style={styles.modal}>
            <Text style={styles.modalEyebrow}>LANGUAGE</Text>
            <Text style={styles.modalTitle}>How would you like MEDHA to speak?</Text>
            <Text style={styles.modalSubtitle}>Choose the language you want to use with MEDHA.</Text>
            {languages.map((item) => {
              const selected = item.code === language.code;
              return (
                <Pressable key={item.code} style={[styles.languageOption, selected && styles.selected]} onPress={() => { setLanguage(item); setLanguageModal(false); }}>
                  <Text style={[styles.languageText, selected && styles.selectedText]}>{item.label}</Text>
                  {selected && <Ionicons name="checkmark" size={18} color={COLORS.forest} />}
                </Pressable>
              );
            })}
            <Pressable onPress={() => setLanguageModal(false)} style={styles.close}><Text style={styles.closeText}>Close</Text></Pressable>
          </View>
        </View>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  profile: { padding: 20, borderRadius: 24, backgroundColor: COLORS.surface, borderWidth: 1, borderColor: COLORS.border, flexDirection: 'row', alignItems: 'center', gap: 15 },
  avatar: { width: 58, height: 58, borderRadius: 29, backgroundColor: COLORS.forest, alignItems: 'center', justifyContent: 'center' },
  avatarText: { fontFamily: 'CormorantGaramond-Regular', fontSize: 28, color: COLORS.white },
  name: { fontFamily: 'CormorantGaramond-Regular', fontSize: 25, color: COLORS.deepForest },
  email: { fontFamily: 'Inter-Regular', fontSize: 10, color: COLORS.mutedText, marginTop: 2 },
  section: { fontFamily: 'Inter-Medium', fontSize: 8, letterSpacing: 1.7, color: COLORS.forest, marginTop: 28, marginBottom: 11 },
  settings: { backgroundColor: COLORS.surface, borderRadius: 22, borderWidth: 1, borderColor: COLORS.border, overflow: 'hidden' },
  setting: { minHeight: 65, paddingHorizontal: 16, flexDirection: 'row', alignItems: 'center', gap: 12, borderBottomWidth: 1, borderBottomColor: COLORS.border },
  settingIcon: { width: 34, height: 34, borderRadius: 17, backgroundColor: COLORS.mist, alignItems: 'center', justifyContent: 'center' },
  settingText: { flex: 1, fontFamily: 'Inter-Regular', fontSize: 12, color: COLORS.text },
  languageValue: { fontFamily: 'Inter-Regular', fontSize: 9, color: COLORS.mutedText, marginTop: 2 },
  toggle: { width: 42, height: 25, borderRadius: 13, backgroundColor: COLORS.lichen, padding: 3, justifyContent: 'center', alignItems: 'flex-end' },
  thumb: { width: 19, height: 19, borderRadius: 10, backgroundColor: COLORS.white },
  version: { textAlign: 'center', fontFamily: 'Inter-Regular', fontSize: 8, color: COLORS.subtleText, marginTop: 28, marginBottom: 20 },
  overlay: { flex: 1, backgroundColor: 'rgba(25,35,29,0.25)', justifyContent: 'flex-end' },
  modal: { backgroundColor: COLORS.surface, borderTopLeftRadius: 30, borderTopRightRadius: 30, padding: 24, paddingBottom: 35 },
  modalEyebrow: { fontFamily: 'Inter-Medium', fontSize: 8, letterSpacing: 1.7, color: COLORS.forest },
  modalTitle: { fontFamily: 'CormorantGaramond-Regular', fontSize: 28, color: COLORS.deepForest, marginTop: 8 },
  modalSubtitle: { fontFamily: 'Inter-Regular', fontSize: 10, lineHeight: 15, color: COLORS.mutedText, marginTop: 6, marginBottom: 15 },
  languageOption: { minHeight: 52, borderRadius: 15, backgroundColor: COLORS.surfaceWarm, paddingHorizontal: 15, flexDirection: 'row', alignItems: 'center', marginTop: 8 },
  selected: { backgroundColor: COLORS.mist },
  languageText: { flex: 1, fontFamily: 'Inter-Medium', fontSize: 12, color: COLORS.text },
  selectedText: { color: COLORS.forest },
  close: { height: 50, borderRadius: 25, backgroundColor: COLORS.forest, alignItems: 'center', justifyContent: 'center', marginTop: 17 },
  closeText: { fontFamily: 'Inter-Medium', fontSize: 12, color: COLORS.white },
});
