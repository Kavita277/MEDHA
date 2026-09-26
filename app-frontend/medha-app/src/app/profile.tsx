import React, { useState } from 'react';
import {
  Alert,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { MedhaBottomNav } from '../components/medha-bottom-nav';
import { COLORS } from '../constants/colors';
import { RADIUS, SHADOW, TOP_HEADER_PADDING } from '../constants/theme';
import { clearAccessToken } from '../services/api';
import { MedhaScreenBackground } from '../components/medha-screen-background';

const languages = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'Hindi' },
];

interface EmergencyContactInfo {
  name: string;
  relation: string;
  phone: string;
  secondaryPhone?: string;
}

export default function ProfileScreen() {
  const router = useRouter();
  const [language, setLanguage] = useState(languages[0]);
  const [languageModal, setLanguageModal] = useState(false);
  const [personalInfoModal, setPersonalInfoModal] = useState(false);

  // Local user-managed emergency contact state (not synced to backend)
  const [emergencyContact, setEmergencyContact] = useState<EmergencyContactInfo | null>({
    name: 'Priya Sharma',
    relation: 'Sister',
    phone: '+91 98765 43210',
    secondaryPhone: '+91 98111 22334',
  });
  const [emergencyContactModal, setEmergencyContactModal] = useState(false);
  const [isEditingContact, setIsEditingContact] = useState(false);
  const [contactForm, setContactForm] = useState<EmergencyContactInfo>({
    name: 'Priya Sharma',
    relation: 'Sister',
    phone: '+91 98765 43210',
    secondaryPhone: '+91 98111 22334',
  });

  const handleOpenEmergencyModal = () => {
    if (emergencyContact) {
      setContactForm({ ...emergencyContact });
      setIsEditingContact(false);
    } else {
      setContactForm({ name: '', relation: '', phone: '', secondaryPhone: '' });
      setIsEditingContact(true);
    }
    setEmergencyContactModal(true);
  };

  const handleSaveContact = () => {
    if (!contactForm.name.trim() || !contactForm.phone.trim()) {
      if (Platform.OS === 'web') {
        window.alert('Please provide at least a contact name and phone number.');
      } else {
        Alert.alert('Required Information', 'Please provide at least a contact name and phone number.');
      }
      return;
    }
    setEmergencyContact({ ...contactForm });
    setIsEditingContact(false);
  };

  const handleRemoveContact = () => {
    const doRemove = () => {
      setEmergencyContact(null);
      setContactForm({ name: '', relation: '', phone: '', secondaryPhone: '' });
      setIsEditingContact(false);
    };

    if (Platform.OS === 'web') {
      const confirmed =
        typeof window !== 'undefined'
          ? window.confirm('Are you sure you want to remove this personal emergency contact from your device?')
          : true;
      if (confirmed) {
        doRemove();
      }
    } else {
      Alert.alert(
        'Remove Emergency Contact',
        'Are you sure you want to remove this personal emergency contact from your device?',
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Remove',
            style: 'destructive',
            onPress: doRemove,
          },
        ]
      );
    }
  };

  const performLogout = () => {
    clearAccessToken();
    router.replace('/login');
  };

  const handleLogout = () => {
    if (Platform.OS === 'web') {
      const confirmed =
        typeof window !== 'undefined'
          ? window.confirm('Are you sure you want to log out of your MEDHA space?')
          : true;
      if (confirmed) {
        performLogout();
      }
    } else {
      Alert.alert(
        'Log Out',
        'Are you sure you want to log out of your MEDHA space?',
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Log Out',
            style: 'destructive',
            onPress: performLogout,
          },
        ]
      );
    }
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

            <Pressable
              onPress={() => router.push('/settings')}
              style={({ pressed }) => [
                styles.iconButton,
                pressed && styles.pressed,
              ]}
              hitSlop={12}
              accessibilityRole="button"
              accessibilityLabel="Settings"
            >
              <Ionicons name="settings-outline" size={20} color={COLORS.navy} />
            </Pressable>
          </View>

          {/* USER IDENTITY CARD MATCHING REFERENCE SCREEN 22 */}
          <View style={styles.profileHeaderCard}>
            <View style={styles.avatarCircle}>
              <Text style={styles.avatarInitial}>K</Text>
            </View>
            <View style={styles.profileIdentity}>
              <Text style={styles.userName}>Kavita</Text>
              <Text style={styles.userEmail}>kavita@medha.care</Text>
            </View>
          </View>

          {/* MENU ITEMS GROUP 1 MATCHING REFERENCE SCREEN 22 */}
          <View style={styles.menuGroup}>
            {/* 1. Personal Information */}
            <Pressable
              onPress={() => setPersonalInfoModal(true)}
              style={({ pressed }) => [
                styles.menuItem,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Personal Information"
            >
              <View style={[styles.menuIconBadge, { backgroundColor: '#EDE7FB' }]}>
                <Ionicons name="person-outline" size={18} color="#7856D6" />
              </View>
              <Text style={styles.menuLabel}>Personal Information</Text>
              <Ionicons name="chevron-forward" size={18} color={COLORS.navyMuted} />
            </Pressable>

            {/* 2. Privacy & Security */}
            <Pressable
              onPress={() => router.push('/settings')}
              style={({ pressed }) => [
                styles.menuItem,
                styles.menuItemBorder,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Privacy & Security"
            >
              <View style={[styles.menuIconBadge, { backgroundColor: '#E4F6EB' }]}>
                <Ionicons name="shield-checkmark-outline" size={18} color="#2D8A4E" />
              </View>
              <Text style={styles.menuLabel}>Privacy & Security</Text>
              <Ionicons name="chevron-forward" size={18} color={COLORS.navyMuted} />
            </Pressable>

            {/* 3. Connected Devices */}
            <Pressable
              onPress={() => router.push('/connected-devices')}
              style={({ pressed }) => [
                styles.menuItem,
                styles.menuItemBorder,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Connected Devices"
            >
              <View style={[styles.menuIconBadge, { backgroundColor: '#FFF4D6' }]}>
                <Ionicons name="watch-outline" size={18} color="#CCA01A" />
              </View>
              <Text style={styles.menuLabel}>Connected Devices</Text>
              <Ionicons name="chevron-forward" size={18} color={COLORS.navyMuted} />
            </Pressable>

            {/* 4. Choose Your Atmosphere / Ambient */}
            <Pressable
              onPress={() => router.push('/ambient')}
              style={({ pressed }) => [
                styles.menuItem,
                styles.menuItemBorder,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Choose Your Atmosphere"
            >
              <View style={[styles.menuIconBadge, { backgroundColor: '#E0F2FE' }]}>
                <Ionicons name="musical-notes-outline" size={18} color="#0284C7" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.menuLabel}>Choose Your Atmosphere</Text>
                <Text style={styles.menuSubLabel}>Ambient sound & calming spaces</Text>
              </View>
              <Ionicons name="chevron-forward" size={18} color={COLORS.navyMuted} />
            </Pressable>

            {/* 5. App Settings */}
            <Pressable
              onPress={() => router.push('/settings')}
              style={({ pressed }) => [
                styles.menuItem,
                styles.menuItemBorder,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="App Settings"
            >
              <View style={[styles.menuIconBadge, { backgroundColor: '#FFEADB' }]}>
                <Ionicons name="options-outline" size={18} color="#E66A35" />
              </View>
              <Text style={styles.menuLabel}>App Settings</Text>
              <Ionicons name="chevron-forward" size={18} color={COLORS.navyMuted} />
            </Pressable>

            {/* 6. Emergency Contact (Safety & Support) */}
            <Pressable
              onPress={handleOpenEmergencyModal}
              style={({ pressed }) => [
                styles.menuItem,
                styles.menuItemBorder,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Personal Emergency Contact"
            >
              <View style={[styles.menuIconBadge, { backgroundColor: '#FFEBF1' }]}>
                <Ionicons name="call-outline" size={18} color="#E05375" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.menuLabel}>Emergency Contact</Text>
                <Text style={styles.menuSubLabel}>
                  {emergencyContact
                    ? `${emergencyContact.name} · ${emergencyContact.relation}`
                    : 'Add personal trusted contact'}
                </Text>
              </View>
              <Ionicons name="chevron-forward" size={18} color={COLORS.navyMuted} />
            </Pressable>

            {/* 7. Quick Support Access (Distress PIN) */}
            <Pressable
              onPress={() => router.push('/distress-pin')}
              style={({ pressed }) => [
                styles.menuItem,
                styles.menuItemBorder,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Quick Support Access"
            >
              <View style={[styles.menuIconBadge, { backgroundColor: '#E2F5E8' }]}>
                <Ionicons name="key-outline" size={18} color="#2D8A4E" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.menuLabel}>Quick Support Access</Text>
                <Text style={styles.menuSubLabel}>Direct access via personal Distress PIN</Text>
              </View>
              <Ionicons name="chevron-forward" size={18} color={COLORS.navyMuted} />
            </Pressable>

            {/* 8. Help & Support */}
            <Pressable
              onPress={() => router.push('/support')}
              style={({ pressed }) => [
                styles.menuItem,
                styles.menuItemBorder,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Help & Support"
            >
              <View style={[styles.menuIconBadge, { backgroundColor: '#E8F2FA' }]}>
                <Ionicons name="help-circle-outline" size={18} color="#2B7CB0" />
              </View>
              <Text style={styles.menuLabel}>Help & Support</Text>
              <Ionicons name="chevron-forward" size={18} color={COLORS.navyMuted} />
            </Pressable>
          </View>


          {/* LOG OUT BUTTON */}
          <View style={styles.logoutGroup}>
            <Pressable
              onPress={handleLogout}
              style={({ pressed }) => [
                styles.logoutBtn,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Log Out"
            >
              <Ionicons name="log-out-outline" size={18} color="#E03E3E" />
              <Text style={styles.logoutText}>Log Out</Text>
            </Pressable>
          </View>

          {/* APP VERSION */}
          <Text style={styles.versionText}>MEDHA · Release 1.0.0 (Production Ready)</Text>
        </ScrollView>

        {/* FLOATING BOTTOM NAVIGATION */}
        <MedhaBottomNav activeTab="profile" />
      </View>

      {/* PERSONAL INFO MODAL */}
      <Modal
        visible={personalInfoModal}
        transparent
        animationType="fade"
        onRequestClose={() => setPersonalInfoModal(false)}
      >
        <View style={styles.overlay}>
          <View style={styles.modalCard}>
            <Text style={styles.modalEyebrow}>PERSONAL INFORMATION</Text>
            <Text style={styles.modalTitle}>Your Profile Identity</Text>
            <Text style={styles.modalSub}>
              Data is stored securely on your device for personalised check-ins.
            </Text>

            <View style={styles.infoField}>
              <Text style={styles.fieldLabel}>Display Name</Text>
              <Text style={styles.fieldValue}>Kavita</Text>
            </View>

            <View style={styles.infoField}>
              <Text style={styles.fieldLabel}>Account Email</Text>
              <Text style={styles.fieldValue}>kavita@medha.care</Text>
            </View>

            <View style={styles.infoField}>
              <Text style={styles.fieldLabel}>Member Since</Text>
              <Text style={styles.fieldValue}>September 2025</Text>
            </View>

            <Pressable
              onPress={() => setPersonalInfoModal(false)}
              style={styles.modalCloseBtn}
            >
              <Text style={styles.modalCloseText}>Done</Text>
            </Pressable>
          </View>
        </View>
      </Modal>

      {/* EMERGENCY CONTACT MODAL */}
      <Modal
        visible={emergencyContactModal}
        transparent
        animationType="fade"
        onRequestClose={() => {
          setIsEditingContact(false);
          setEmergencyContactModal(false);
        }}
      >
        <View style={styles.overlay}>
          <View style={styles.modalCard}>
            <Text style={styles.modalEyebrow}>SAFETY & SUPPORT</Text>
            <Text style={styles.modalTitle}>Emergency Contact</Text>
            <Text style={styles.modalSub}>
              Stored locally on your device for your personal reference. MEDHA does not automatically place calls or send messages.
            </Text>

            {isEditingContact ? (
              <View style={styles.formContainer}>
                <View style={styles.inputGroup}>
                  <Text style={styles.inputLabel}>Contact Name *</Text>
                  <TextInput
                    style={styles.textInput}
                    value={contactForm.name}
                    onChangeText={(text) =>
                      setContactForm((prev) => ({ ...prev, name: text }))
                    }
                    placeholder="e.g. Priya Sharma"
                    placeholderTextColor={COLORS.navyMuted}
                  />
                </View>

                <View style={styles.inputGroup}>
                  <Text style={styles.inputLabel}>Relationship</Text>
                  <TextInput
                    style={styles.textInput}
                    value={contactForm.relation}
                    onChangeText={(text) =>
                      setContactForm((prev) => ({ ...prev, relation: text }))
                    }
                    placeholder="e.g. Sister, Friend, Partner"
                    placeholderTextColor={COLORS.navyMuted}
                  />
                </View>

                <View style={styles.inputGroup}>
                  <Text style={styles.inputLabel}>Phone Number *</Text>
                  <TextInput
                    style={styles.textInput}
                    value={contactForm.phone}
                    onChangeText={(text) =>
                      setContactForm((prev) => ({ ...prev, phone: text }))
                    }
                    placeholder="+91 98765 43210"
                    placeholderTextColor={COLORS.navyMuted}
                    keyboardType="phone-pad"
                  />
                </View>

                <View style={styles.inputGroup}>
                  <Text style={styles.inputLabel}>Secondary Contact (Optional)</Text>
                  <TextInput
                    style={styles.textInput}
                    value={contactForm.secondaryPhone}
                    onChangeText={(text) =>
                      setContactForm((prev) => ({ ...prev, secondaryPhone: text }))
                    }
                    placeholder="Optional second number"
                    placeholderTextColor={COLORS.navyMuted}
                    keyboardType="phone-pad"
                  />
                </View>

                <View style={styles.modalActionRow}>
                  <Pressable
                    onPress={handleSaveContact}
                    style={({ pressed }) => [
                      styles.modalPrimaryBtn,
                      pressed && styles.pressed,
                    ]}
                  >
                    <Text style={styles.modalPrimaryText}>Save Contact</Text>
                  </Pressable>
                  <Pressable
                    onPress={() => setIsEditingContact(false)}
                    style={({ pressed }) => [
                      styles.modalSecondaryBtn,
                      pressed && styles.pressed,
                    ]}
                  >
                    <Text style={styles.modalSecondaryText}>Cancel</Text>
                  </Pressable>
                </View>
              </View>
            ) : emergencyContact ? (
              <View>
                <View style={styles.infoField}>
                  <Text style={styles.fieldLabel}>Contact Name</Text>
                  <Text style={styles.fieldValue}>{emergencyContact.name}</Text>
                </View>

                <View style={styles.infoField}>
                  <Text style={styles.fieldLabel}>Relationship</Text>
                  <Text style={styles.fieldValue}>
                    {emergencyContact.relation || 'Not specified'}
                  </Text>
                </View>

                <View style={styles.infoField}>
                  <Text style={styles.fieldLabel}>Phone Number</Text>
                  <Text style={styles.fieldValue}>{emergencyContact.phone}</Text>
                </View>

                {emergencyContact.secondaryPhone ? (
                  <View style={styles.infoField}>
                    <Text style={styles.fieldLabel}>Secondary Contact</Text>
                    <Text style={styles.fieldValue}>
                      {emergencyContact.secondaryPhone}
                    </Text>
                  </View>
                ) : null}

                <View style={styles.modalActionRow}>
                  <Pressable
                    onPress={() => {
                      setContactForm({ ...emergencyContact });
                      setIsEditingContact(true);
                    }}
                    style={({ pressed }) => [
                      styles.modalEditBtn,
                      pressed && styles.pressed,
                    ]}
                  >
                    <Ionicons name="pencil-outline" size={15} color={COLORS.navy} />
                    <Text style={styles.modalEditText}>Edit</Text>
                  </Pressable>

                  <Pressable
                    onPress={handleRemoveContact}
                    style={({ pressed }) => [
                      styles.modalDeleteBtn,
                      pressed && styles.pressed,
                    ]}
                  >
                    <Ionicons name="trash-outline" size={15} color="#E03E3E" />
                    <Text style={styles.modalDeleteText}>Remove</Text>
                  </Pressable>
                </View>

                <Pressable
                  onPress={() => setEmergencyContactModal(false)}
                  style={styles.modalCloseBtn}
                >
                  <Text style={styles.modalCloseText}>Done</Text>
                </Pressable>
              </View>
            ) : (
              <View style={styles.emptyContactWrap}>
                <Ionicons name="call-outline" size={32} color={COLORS.coralDark} />
                <Text style={styles.emptyContactTitle}>No Contact Added</Text>
                <Text style={styles.emptyContactSub}>
                  Add a personal emergency contact for quick access during moments of need.
                </Text>
                <Pressable
                  onPress={() => {
                    setContactForm({ name: '', relation: '', phone: '', secondaryPhone: '' });
                    setIsEditingContact(true);
                  }}
                  style={styles.modalPrimaryBtn}
                >
                  <Text style={styles.modalPrimaryText}>Add Contact</Text>
                </Pressable>
                <Pressable
                  onPress={() => setEmergencyContactModal(false)}
                  style={[styles.modalSecondaryBtn, { marginTop: 8 }]}
                >
                  <Text style={styles.modalSecondaryText}>Close</Text>
                </Pressable>
              </View>
            )}
          </View>
        </View>
      </Modal>

      {/* LANGUAGE MODAL (Preserving existing modal behavior) */}
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
              Select the primary language you want to use with MEDHA.
            </Text>

            {languages.map((item) => {
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
              <Text style={styles.modalCloseText}>Close</Text>
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
    paddingBottom: 24,
  },

  /* TOP BAR */
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
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

  /* PROFILE HEADER CARD */
  profileHeaderCard: {
    marginTop: 12,
    marginBottom: 20,
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.card,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    padding: 18,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
    ...SHADOW.subtle,
  },
  avatarCircle: {
    width: 58,
    height: 58,
    borderRadius: 29,
    backgroundColor: COLORS.navy,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarInitial: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 24,
    color: COLORS.white,
  },
  profileIdentity: {
    flex: 1,
  },
  userName: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 19,
    color: COLORS.navy,
  },
  userEmail: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    color: COLORS.navyMuted,
    marginTop: 3,
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
    minHeight: 60,
    paddingHorizontal: 16,
    paddingVertical: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
  },
  menuItemBorder: {
    borderTopWidth: 1,
    borderTopColor: 'rgba(0, 0, 0, 0.04)',
  },
  menuIconBadge: {
    width: 38,
    height: 38,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  menuLabel: {
    flex: 1,
    fontFamily: 'Nunito-SemiBold',
    fontSize: 14,
    color: COLORS.navy,
  },
  menuSubLabel: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    color: COLORS.navyMuted,
    marginTop: 2,
  },


  /* LOGOUT GROUP */
  logoutGroup: {
    marginTop: 14,
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.card,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    overflow: 'hidden',
    ...SHADOW.subtle,
  },
  logoutBtn: {
    minHeight: 54,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  logoutText: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 14,
    color: '#E03E3E',
  },

  versionText: {
    textAlign: 'center',
    fontFamily: 'Nunito-Regular',
    fontSize: 10,
    color: COLORS.subtleText,
    marginTop: 24,
    marginBottom: 8,
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
    lineHeight: 17,
    color: COLORS.navyMuted,
    marginTop: 4,
    marginBottom: 16,
  },
  infoField: {
    backgroundColor: COLORS.porcelain,
    borderRadius: RADIUS.medium,
    padding: 12,
    marginVertical: 4,
  },
  fieldLabel: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 11,
    color: COLORS.navyMuted,
  },
  fieldValue: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 14,
    color: COLORS.navy,
    marginTop: 2,
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
    marginTop: 18,
  },
  modalCloseText: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 14,
    color: COLORS.white,
  },

  /* EMERGENCY CONTACT FORM & CONTROLS */
  formContainer: {
    marginTop: 6,
  },
  inputGroup: {
    marginBottom: 10,
  },
  inputLabel: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 12,
    color: COLORS.navyMuted,
    marginBottom: 4,
  },
  textInput: {
    backgroundColor: COLORS.porcelain,
    borderRadius: RADIUS.medium,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.08)',
    paddingHorizontal: 12,
    paddingVertical: 9,
    fontFamily: 'Nunito-Medium',
    fontSize: 13.5,
    color: COLORS.navy,
  },
  modalActionRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 14,
  },
  modalPrimaryBtn: {
    flex: 1,
    height: 46,
    borderRadius: RADIUS.pill,
    backgroundColor: COLORS.navy,
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalPrimaryText: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 14,
    color: COLORS.white,
  },
  modalSecondaryBtn: {
    flex: 1,
    height: 46,
    borderRadius: RADIUS.pill,
    backgroundColor: COLORS.porcelain,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.06)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalSecondaryText: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 14,
    color: COLORS.navy,
  },
  modalEditBtn: {
    flex: 1,
    height: 44,
    borderRadius: RADIUS.pill,
    backgroundColor: '#F0EFF5',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  modalEditText: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 13,
    color: COLORS.navy,
  },
  modalDeleteBtn: {
    height: 44,
    paddingHorizontal: 16,
    borderRadius: RADIUS.pill,
    backgroundColor: '#FDF2F2',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  modalDeleteText: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 13,
    color: '#E03E3E',
  },
  emptyContactWrap: {
    alignItems: 'center',
    paddingVertical: 18,
  },
  emptyContactTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 16,
    color: COLORS.navy,
    marginTop: 10,
  },
  emptyContactSub: {
    fontFamily: 'Nunito-Regular',
    fontSize: 13,
    color: COLORS.navyMuted,
    textAlign: 'center',
    marginTop: 4,
    marginBottom: 16,
    maxWidth: 280,
  },

  pressed: {
    transform: [{ scale: 0.98 }],
    opacity: 0.88,
  },
});
