import React, { useState } from 'react';
import {
  Modal,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { MedhaScreen } from '../components/medha-screen';
import { COLORS } from '../constants/colors';

interface LanguageOption {
  code: string;
  label: string;
}

const languages: LanguageOption[] = [
  {
    code: 'en',
    label: 'English',
  },
  {
    code: 'hi',
    label: 'Hindi',
  },
  {
    code: 'mr',
    label: 'Marathi',
  },
];

export default function ProfileScreen() {
  const router = useRouter();

  const [language, setLanguage] =
    useState<LanguageOption>(languages[0]);

  const [languageModal, setLanguageModal] =
    useState(false);

  /*
   * This object is intentionally shaped like
   * something we can later pass to the backend.
   *
   * No translation logic happens here.
   */
  const profilePreferences = {
    language: language.code,
  };

  return (
    <>
      <MedhaScreen
        eyebrow="Your space"
        title="Profile & settings"
        subtitle="Keep MEDHA feeling like your own quiet corner."
        onBack={() => router.back()}
      >

        {/* PROFILE */}

        <View style={styles.profile}>

          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              E
            </Text>
          </View>

          <View>
            <Text style={styles.name}>
              Esha
            </Text>

            <Text style={styles.email}>
              Your private MEDHA space
            </Text>
          </View>

        </View>


        {/* PREFERENCES */}

        <Text style={styles.section}>
          PREFERENCES
        </Text>

        <View style={styles.settings}>

          {/* REMINDERS */}

          <View style={styles.setting}>

            <View style={styles.settingIcon}>
              <Ionicons
                name="notifications-outline"
                size={18}
                color={COLORS.forest}
              />
            </View>

            <Text style={styles.settingText}>
              Gentle reminders
            </Text>

            <View style={styles.fakeToggle}>
              <View style={styles.toggleThumb} />
            </View>

          </View>


          {/* LANGUAGE */}

          <Pressable
            onPress={() =>
              setLanguageModal(true)
            }
            style={styles.setting}
          >

            <View style={styles.settingIcon}>
              <Ionicons
                name="language-outline"
                size={18}
                color={COLORS.forest}
              />
            </View>

            <View style={styles.languageCopy}>

              <Text style={styles.settingText}>
                Language
              </Text>

              <Text style={styles.languageValue}>
                {language.label}
              </Text>

            </View>

            <Ionicons
              name="chevron-forward"
              size={17}
              color={COLORS.mutedText}
            />

          </Pressable>


          {/* AMBIENT */}

          <Pressable
            onPress={() =>
              router.push('/ambient')
            }
            style={styles.setting}
          >

            <View style={styles.settingIcon}>
              <Ionicons
                name="musical-notes-outline"
                size={18}
                color={COLORS.forest}
              />
            </View>

            <Text style={styles.settingText}>
              Ambient sound
            </Text>

            <Ionicons
              name="chevron-forward"
              size={17}
              color={COLORS.mutedText}
            />

          </Pressable>


          {/* PRIVACY */}

          <View style={styles.setting}>

            <View style={styles.settingIcon}>
              <Ionicons
                name="lock-closed-outline"
                size={18}
                color={COLORS.forest}
              />
            </View>

            <Text style={styles.settingText}>
              Privacy
            </Text>

            <Ionicons
              name="chevron-forward"
              size={17}
              color={COLORS.mutedText}
            />

          </View>

        </View>


        {/* BACKEND PREVIEW */}

        <View style={styles.backendNote}>

          <Ionicons
            name="cloud-outline"
            size={16}
            color={COLORS.forest}
          />

          <Text style={styles.backendText}>
            Your language preference will be
            available to MEDHA's conversational
            services when backend integration is
            connected.
          </Text>

        </View>


        <Text style={styles.version}>
          MEDHA · 0.1 PROTOTYPE
        </Text>

      </MedhaScreen>


      {/* LANGUAGE MODAL */}

      <Modal
        visible={languageModal}
        transparent
        animationType="fade"
        onRequestClose={() =>
          setLanguageModal(false)
        }
      >

        <View style={styles.modalOverlay}>

          <View style={styles.modal}>

            <Text style={styles.modalEyebrow}>
              LANGUAGE
            </Text>

            <Text style={styles.modalTitle}>
              How would you like MEDHA to speak?
            </Text>

            <Text style={styles.modalSubtitle}>
              This preference will later be shared
              with MEDHA's conversational services.
            </Text>


            <View style={styles.languageList}>

              {languages.map((item) => {

                const selected =
                  language.code === item.code;

                return (
                  <Pressable
                    key={item.code}
                    onPress={() => {
                      setLanguage(item);
                      setLanguageModal(false);
                    }}
                    style={[
                      styles.languageOption,
                      selected &&
                        styles.selectedLanguage,
                    ]}
                  >

                    <Text
                      style={[
                        styles.languageText,
                        selected &&
                          styles.selectedLanguageText,
                      ]}
                    >
                      {item.label}
                    </Text>

                    {selected && (
                      <Ionicons
                        name="checkmark"
                        size={18}
                        color={COLORS.forest}
                      />
                    )}

                  </Pressable>
                );
              })}

            </View>


            <Pressable
              onPress={() =>
                setLanguageModal(false)
              }
              style={styles.closeModal}
            >
              <Text style={styles.closeText}>
                Close
              </Text>
            </Pressable>

          </View>

        </View>

      </Modal>
    </>
  );
}


const styles = StyleSheet.create({

  profile: {
    padding: 22,
    borderRadius: 24,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },

  avatar: {
    width: 58,
    height: 58,
    borderRadius: 29,
    backgroundColor: COLORS.forest,
    alignItems: 'center',
    justifyContent: 'center',
  },

  avatarText: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 28,
    color: COLORS.white,
  },

  name: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 25,
    color: COLORS.deepForest,
  },

  email: {
    fontFamily: 'Inter-Regular',
    fontSize: 10,
    color: COLORS.mutedText,
    marginTop: 2,
  },

  section: {
    fontFamily: 'Inter-Medium',
    fontSize: 9,
    letterSpacing: 1.8,
    color: COLORS.forest,
    marginTop: 30,
    marginBottom: 12,
  },

  settings: {
    backgroundColor: COLORS.surface,
    borderRadius: 22,
    borderWidth: 1,
    borderColor: COLORS.border,
    overflow: 'hidden',
  },

  setting: {
    minHeight: 65,
    paddingHorizontal: 17,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 13,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },

  settingIcon: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: COLORS.mist,
    alignItems: 'center',
    justifyContent: 'center',
  },

  settingText: {
    flex: 1,
    fontFamily: 'Inter-Regular',
    fontSize: 12,
    color: COLORS.text,
  },

  languageCopy: {
    flex: 1,
  },

  languageValue: {
    fontFamily: 'Inter-Regular',
    fontSize: 9,
    color: COLORS.mutedText,
    marginTop: 2,
  },

  fakeToggle: {
    width: 42,
    height: 25,
    borderRadius: 13,
    backgroundColor: COLORS.lichen,
    padding: 3,
    justifyContent: 'center',
    alignItems: 'flex-end',
  },

  toggleThumb: {
    width: 19,
    height: 19,
    borderRadius: 10,
    backgroundColor: COLORS.white,
  },

  backendNote: {
    marginTop: 22,
    padding: 16,
    borderRadius: 19,
    backgroundColor: COLORS.mist,
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 9,
  },

  backendText: {
    flex: 1,
    fontFamily: 'Inter-Regular',
    fontSize: 9,
    lineHeight: 15,
    color: COLORS.mutedText,
  },

  version: {
    textAlign: 'center',
    fontFamily: 'Inter-Medium',
    fontSize: 8,
    letterSpacing: 1.5,
    color: COLORS.subtleText,
    marginTop: 30,
  },

  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(40,58,49,0.35)',
    justifyContent: 'flex-end',
  },

  modal: {
    backgroundColor: COLORS.background,
    borderTopLeftRadius: 30,
    borderTopRightRadius: 30,
    paddingHorizontal: 24,
    paddingTop: 28,
    paddingBottom: 30,
  },

  modalEyebrow: {
    fontFamily: 'Inter-Medium',
    fontSize: 8,
    letterSpacing: 1.8,
    color: COLORS.forest,
  },

  modalTitle: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 28,
    lineHeight: 31,
    color: COLORS.deepForest,
    marginTop: 8,
  },

  modalSubtitle: {
    fontFamily: 'Inter-Regular',
    fontSize: 10,
    lineHeight: 16,
    color: COLORS.mutedText,
    marginTop: 8,
  },

  languageList: {
    marginTop: 22,
    gap: 8,
  },

  languageOption: {
    height: 54,
    borderRadius: 17,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    paddingHorizontal: 17,
    flexDirection: 'row',
    alignItems: 'center',
  },

  selectedLanguage: {
    backgroundColor: COLORS.mist,
    borderColor: COLORS.forest,
  },

  languageText: {
    flex: 1,
    fontFamily: 'Inter-Regular',
    fontSize: 12,
    color: COLORS.text,
  },

  selectedLanguageText: {
    fontFamily: 'Inter-Medium',
    color: COLORS.deepForest,
  },

  closeModal: {
    height: 50,
    borderRadius: 25,
    backgroundColor: COLORS.forest,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 18,
  },

  closeText: {
    fontFamily: 'Inter-Medium',
    fontSize: 12,
    color: COLORS.white,
  },

});