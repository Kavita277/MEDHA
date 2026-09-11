import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  ImageBackground,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { useSession } from '../context/SessionContext';
import { checkinService } from '../services/checkin';
import { COLORS } from '../constants/colors';
import { useAuth } from '../context/AuthContext';

const forestImage =
  'https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=1200&q=85';

export default function HomeScreen() {
  const router = useRouter();
  const { sessionId } = useSession();
  const { user, token } = useAuth();

  // Check-in Pop-up Modal State
  const [showCheckinModal, setShowCheckinModal] = useState(false);
  const [checkinStep, setCheckinStep] = useState<'prompt' | 'questionnaire' | 'completed'>('prompt');
  const [loadingCheckin, setLoadingCheckin] = useState(false);
  const [checkinData, setCheckinData] = useState<any>(null);
  const [currentQuestion, setCurrentQuestion] = useState<any>(null);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [customText, setCustomText] = useState('');
  const [submittingAnswer, setSubmittingAnswer] = useState(false);
  const [totalQuestions, setTotalQuestions] = useState(12);
  const [answeredCount, setAnsweredCount] = useState(0);
  const [checkinError, setCheckinError] = useState<string | null>(null);

  // Auto-pop check-in on first open if not completed today
  useEffect(() => {
    if (!token) return;
    let mounted = true;
    checkinService.getTodayStatus(token)
      .then((status) => {
        if (mounted && status && !status.completed_today) {
          setShowCheckinModal(true);
          setCheckinStep('prompt');
        }
      })
      .catch((err) => {
        console.warn('Today check-in status check failed:', err);
        if (mounted) {
          setShowCheckinModal(true);
          setCheckinStep('prompt');
        }
      });
    return () => { mounted = false; };
  }, [token]);

  const handleStartCheckin = async () => {
    setLoadingCheckin(true);
    setCheckinError(null);
    setCheckinStep('questionnaire');
    try {
      if (!sessionId || !token) {
        setCheckinError('Cannot start checkin: No active session or token');
        return;
      }
      const chk = await checkinService.startCheckin(sessionId, token);
      if (chk) {
        setCheckinData(chk);
        const qList = chk.questions || [];
        setTotalQuestions(qList.length > 0 ? qList.length : 12);
        
        const activeQ = qList.find(
          (q: any) => q.question_id === chk.current_question_id || q.answer_status === 'pending'
        );
        if (activeQ) {
          setCurrentQuestion(activeQ);
          const answered = qList.filter((q: any) => q.answer_status === 'answered').length;
          setAnsweredCount(answered);
        } else if (qList.length > 0) {
          setCurrentQuestion(qList[0]);
          setAnsweredCount(0);
        } else {
          setCheckinError('No questions available for this check-in.');
        }
      } else {
        setCheckinError('Failed to load check-in data.');
      }
    } catch (err: any) {
      console.warn('Failed to start checkin:', err);
      setCheckinError(err.message || 'An error occurred while starting the check-in.');
    } finally {
      setLoadingCheckin(false);
    }
  };

  const handleAnswerSubmit = async (val?: string) => {
    const valueToSubmit = val || selectedOption || customText.trim();
    if (!valueToSubmit || submittingAnswer || !checkinData || !currentQuestion || !token) return;
    setSubmittingAnswer(true);

    try {
      const res = await checkinService.submitAnswer(checkinData.id, {
        value: valueToSubmit,
        question_id: currentQuestion.question_id,
      }, token);

      setAnsweredCount((prev) => prev + 1);
      setSelectedOption(null);
      setCustomText('');

      if (res && res.next_question) {
        setCurrentQuestion(res.next_question);
      } else {
        // All questions completed!
        setCheckinStep('completed');
      }
    } catch (err) {
      console.warn('Failed to submit check-in answer:', err);
    } finally {
      setSubmittingAnswer(false);
    }
  };

  return (
    <View style={styles.screen}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.content}
      >
        {/* HEADER */}

        <View style={styles.header}>
          <View>
            <Text style={styles.small}>GOOD MORNING</Text>
            <Text style={styles.logo}>MEDHA</Text>
          </View>

          <Pressable
            style={styles.profileButton}
            onPress={() => router.push('/profile')}
          >
            <Text style={styles.profileLetter}>E</Text>
          </Pressable>
        </View>

        {/* HERO */}

        <View style={styles.hero}>
          <ImageBackground
            source={{ uri: forestImage }}
            style={styles.heroImage}
            imageStyle={styles.heroImageStyle}
          >
            <View style={styles.heroOverlay} />

            <View style={styles.heroContent}>
              <Text style={styles.heroEyebrow}>A QUIET MOMENT</Text>

              <Text style={styles.heroTitle}>
                {'Take a breath.\nYou’re here.'}
              </Text>

              <Text style={styles.heroText}>
                Nothing needs to be solved all at once.
              </Text>
            </View>
          </ImageBackground>
        </View>

        {/* ARRIVE / CHECK-IN */}

        <View style={styles.section}>
          <Text style={styles.sectionEyebrow}>ARRIVE</Text>

          <Text style={styles.sectionTitle}>
            How would you like to arrive?
          </Text>

          <View style={styles.arrivalRow}>
            {/* QUICK CHECK-IN */}

            <Pressable
              style={styles.arrival}
              onPress={() => {
                setShowCheckinModal(true);
                handleStartCheckin();
              }}
            >
              <View style={styles.arrivalIcon}>
                <Ionicons
                  name="sparkles-outline"
                  size={21}
                  color={COLORS.forest}
                />
              </View>

              <Text style={styles.arrivalTitle}>Check in</Text>

              <Text style={styles.arrivalText}>
                A few gentle questions
              </Text>
            </Pressable>

            {/* VOICE CHECK-IN */}

            <Pressable
              style={styles.arrival}
              onPress={() => router.push('/voice')}
            >
              <View style={styles.arrivalIcon}>
                <Ionicons
                  name="mic-outline"
                  size={21}
                  color={COLORS.forest}
                />
              </View>

              <Text style={styles.arrivalTitle}>Speak</Text>

              <Text style={styles.arrivalText}>
                Say what you’re feeling
              </Text>
            </Pressable>
          </View>
        </View>

        {/* YOUR SPACE */}

        <View style={styles.section}>
          <Text style={styles.sectionEyebrow}>YOUR SPACE</Text>

          <View style={styles.list}>
            {/* TALK WITH MEDHA */}

            <Pressable
              style={styles.listItem}
              onPress={() => router.push('/chat')}
            >
              <View style={styles.listIcon}>
                <Ionicons
                  name="chatbubble-outline"
                  size={20}
                  color={COLORS.forest}
                />
              </View>

              <View style={styles.listCopy}>
                <Text style={styles.listTitle}>
                  Talk with MEDHA
                </Text>

                <Text style={styles.listText}>
                  Type or talk about what’s on your mind.
                </Text>
              </View>

              <Ionicons
                name="arrow-forward"
                size={18}
                color={COLORS.mutedText}
              />
            </Pressable>

            {/* FIND YOUR CENTRE */}

            <Pressable
              style={styles.listItem}
              onPress={() => router.push('/grounding')}
            >
              <View style={styles.listIcon}>
                <Ionicons
                  name="leaf-outline"
                  size={20}
                  color={COLORS.forest}
                />
              </View>

              <View style={styles.listCopy}>
                <Text style={styles.listTitle}>
                  Find your centre
                </Text>

                <Text style={styles.listText}>
                  A few quiet minutes to breathe and settle.
                </Text>
              </View>

              <Ionicons
                name="arrow-forward"
                size={18}
                color={COLORS.mutedText}
              />
            </Pressable>

            {/* JOURNAL */}

            <Pressable
              style={styles.listItem}
              onPress={() => router.push('/journal')}
            >
              <View style={styles.listIcon}>
                <Ionicons
                  name="book-outline"
                  size={20}
                  color={COLORS.forest}
                />
              </View>

              <View style={styles.listCopy}>
                <Text style={styles.listTitle}>
                  Write in your journal
                </Text>

                <Text style={styles.listText}>
                  Leave a thought somewhere private.
                </Text>
              </View>

              <Ionicons
                name="arrow-forward"
                size={18}
                color={COLORS.mutedText}
              />
            </Pressable>

            {/* SELF HELP */}

            <Pressable
              style={styles.listItem}
              onPress={() => router.push('/self-help' as any)}
            >
              <View style={styles.listIcon}>
                <Ionicons
                  name="heart-outline"
                  size={20}
                  color={COLORS.forest}
                />
              </View>

              <View style={styles.listCopy}>
                <Text style={styles.listTitle}>
                  Self Help
                </Text>

                <Text style={styles.listText}>
                  Small, gentle steps for difficult moments.
                </Text>
              </View>

              <Ionicons
                name="arrow-forward"
                size={18}
                color={COLORS.mutedText}
              />
            </Pressable>
          </View>
        </View>

        {/* SELF HELP FEATURE CARD */}

        <Pressable
          style={styles.selfHelpCard}
          onPress={() => router.push('/self-help' as any)}
        >
          <View style={styles.selfHelpCopy}>
            <Text style={styles.selfHelpEyebrow}>
              A LITTLE SUPPORT
            </Text>

            <Text style={styles.selfHelpTitle}>
              Small steps.{'\n'}A calmer moment.
            </Text>

            <Text style={styles.selfHelpText}>
              Explore gentle, evidence-informed guides for stress,
              anxiety, low mood and everyday wellbeing.
            </Text>

            <View style={styles.selfHelpButton}>
              <Text style={styles.selfHelpButtonText}>
                Explore Self Help
              </Text>

              <Ionicons
                name="arrow-forward"
                size={16}
                color={COLORS.deepForest}
              />
            </View>
          </View>

          <View style={styles.selfHelpIllustration}>
            <View style={styles.illustrationCircleLarge} />
            <View style={styles.illustrationCircleSmall} />

            <Ionicons
              name="leaf-outline"
              size={45}
              color={COLORS.forest}
            />
          </View>
        </Pressable>

        {/* BOTTOM TOOLS */}

        <View style={styles.tools}>
          <Pressable
            onPress={() => router.push('/ambient')}
            style={styles.tool}
          >
            <Ionicons
              name="musical-notes-outline"
              size={19}
              color={COLORS.forest}
            />

            <Text style={styles.toolText}>Ambient</Text>
          </Pressable>

          <Pressable
            onPress={() => router.push('/notifications')}
            style={styles.tool}
          >
            <Ionicons
              name="notifications-outline"
              size={19}
              color={COLORS.forest}
            />

            <Text style={styles.toolText}>Notifications</Text>
          </Pressable>

          <Pressable
            onPress={() => router.push('/support')}
            style={styles.tool}
          >
            <Ionicons
              name="heart-outline"
              size={19}
              color={COLORS.forest}
            />

            <Text style={styles.toolText}>Support</Text>
          </Pressable>

          <Pressable
            onPress={() => router.push('/profile')}
            style={styles.tool}
          >
            <Ionicons
              name="person-outline"
              size={19}
              color={COLORS.forest}
            />

            <Text style={styles.toolText}>Profile</Text>
          </Pressable>
        </View>
      </ScrollView>

      {/* DAILY CHECK-IN POP-UP MODAL */}
      <Modal
        visible={showCheckinModal}
        transparent={true}
        animationType="fade"
        onRequestClose={() => setShowCheckinModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            {checkinStep === 'prompt' && (
              <View style={styles.promptContent}>
                <Pressable
                  style={styles.modalCloseButton}
                  onPress={() => setShowCheckinModal(false)}
                  hitSlop={10}
                >
                  <Ionicons name="close" size={20} color={COLORS.mutedText} />
                </Pressable>

                <View style={styles.promptIconWrap}>
                  <Ionicons name="sparkles" size={28} color={COLORS.forest} />
                </View>

                <Text style={styles.promptEyebrow}>DAILY WELLBEING CHECK-IN</Text>
                <Text style={styles.promptTitle}>How are you feeling today?</Text>
                <Text style={styles.promptSubtitle}>
                  Take a quiet moment. 10–15 gentle questions randomly tailored to check in on your safety, stress, sleep, and wellbeing.
                </Text>

                <View style={styles.promptButtonRow}>
                  <Pressable
                    style={[styles.primaryButton, loadingCheckin && styles.buttonDisabled]}
                    onPress={handleStartCheckin}
                    disabled={loadingCheckin}
                  >
                    {loadingCheckin ? (
                      <ActivityIndicator size="small" color={COLORS.white} />
                    ) : (
                      <>
                        <Ionicons name="play" size={16} color={COLORS.white} />
                        <Text style={styles.primaryButtonText}>Start Check-in Now</Text>
                      </>
                    )}
                  </Pressable>

                  <Pressable
                    style={styles.secondaryButton}
                    onPress={() => setShowCheckinModal(false)}
                  >
                    <Text style={styles.secondaryButtonText}>Maybe Later</Text>
                  </Pressable>
                </View>
              </View>
            )}

            {checkinStep === 'questionnaire' && (
              <View style={styles.questionnaireContent}>
                {checkinError ? (
                  <View style={styles.loadingContainer}>
                    <Ionicons name="alert-circle-outline" size={48} color={COLORS.support} />
                    <Text style={[styles.loadingText, { color: COLORS.support, marginTop: 16 }]}>{checkinError}</Text>
                    <Pressable
                      style={[styles.primaryButton, { marginTop: 24 }]}
                      onPress={() => setShowCheckinModal(false)}
                    >
                      <Text style={styles.primaryButtonText}>Close</Text>
                    </Pressable>
                  </View>
                ) : loadingCheckin || !currentQuestion ? (
                  <View style={styles.loadingContainer}>
                    <ActivityIndicator size="large" color={COLORS.forest} />
                    <Text style={styles.loadingText}>Preparing your daily questions...</Text>
                  </View>
                ) : (
                  <>
                    <View style={styles.questionnaireHeader}>
                      <View style={styles.progressInfo}>
                        <View style={styles.domainBadge}>
                          <Text style={styles.domainBadgeText}>
                            {currentQuestion.domain || 'CLINICAL CHECK-IN'}
                          </Text>
                        </View>
                        <Text style={styles.progressText}>
                          {`Question ${answeredCount + 1} of ${totalQuestions}`}
                        </Text>
                      </View>

                      <Pressable
                        style={styles.modalCloseButton}
                        onPress={() => setShowCheckinModal(false)}
                        hitSlop={10}
                      >
                        <Ionicons name="close" size={18} color={COLORS.mutedText} />
                      </Pressable>
                    </View>

                    {/* Progress Bar */}
                    <View style={styles.progressBarTrack}>
                      <View
                        style={[
                          styles.progressBarFill,
                          {
                            width: `${Math.min(100, Math.max(5, ((answeredCount + 1) / totalQuestions) * 100))}%`,
                          },
                        ]}
                      />
                    </View>

                    {/* Question Prompt */}
                    <ScrollView
                      style={styles.questionScroll}
                      showsVerticalScrollIndicator={false}
                    >
                      <Text style={styles.questionTitle}>{currentQuestion.question_text}</Text>

                      {/* Options rendering based on response_type */}
                      {currentQuestion.response_type === 'scale_1_5' && (
                        <View style={styles.optionsList}>
                          {(currentQuestion.options && currentQuestion.options.length > 0
                            ? currentQuestion.options
                            : ['1 - Very Low', '2 - Low', '3 - Moderate', '4 - Good', '5 - Optimal']
                          ).map((opt: string, i: number) => {
                            const isSelected = selectedOption === opt;
                            return (
                              <Pressable
                                key={opt}
                                style={[
                                  styles.scaleOptionRow,
                                  isSelected && styles.scaleOptionActive,
                                ]}
                                disabled={submittingAnswer}
                                onPress={() => {
                                  setSelectedOption(opt);
                                  handleAnswerSubmit(opt);
                                }}
                              >
                                <View
                                  style={[
                                    styles.scaleNumberCircle,
                                    isSelected && styles.scaleNumberCircleActive,
                                  ]}
                                >
                                  <Text
                                    style={[
                                      styles.scaleNumberText,
                                      isSelected && styles.scaleNumberTextActive,
                                    ]}
                                  >
                                    {i + 1}
                                  </Text>
                                </View>
                                <Text
                                  style={[
                                    styles.optionText,
                                    isSelected && styles.optionTextActive,
                                  ]}
                                >
                                  {opt}
                                </Text>
                                <Ionicons
                                  name={isSelected ? 'checkmark-circle' : 'chevron-forward'}
                                  size={18}
                                  color={isSelected ? COLORS.forest : COLORS.mutedText}
                                />
                              </Pressable>
                            );
                          })}
                        </View>
                      )}

                      {currentQuestion.response_type === 'yes_no' && (
                        <View style={styles.yesNoRow}>
                          {(currentQuestion.options || ['Yes', 'No']).map((opt: string) => {
                            const isSelected = selectedOption === opt;
                            return (
                              <Pressable
                                key={opt}
                                style={[
                                  styles.yesNoCard,
                                  isSelected && styles.yesNoCardActive,
                                ]}
                                disabled={submittingAnswer}
                                onPress={() => {
                                  setSelectedOption(opt);
                                  handleAnswerSubmit(opt);
                                }}
                              >
                                <Ionicons
                                  name={
                                    opt.toLowerCase().includes('yes')
                                      ? 'checkmark-circle-outline'
                                      : 'close-circle-outline'
                                  }
                                  size={24}
                                  color={isSelected ? COLORS.white : COLORS.deepForest}
                                />
                                <Text
                                  style={[
                                    styles.yesNoText,
                                    isSelected && styles.yesNoTextActive,
                                  ]}
                                >
                                  {opt}
                                </Text>
                              </Pressable>
                            );
                          })}
                        </View>
                      )}

                      {currentQuestion.response_type !== 'scale_1_5' &&
                        currentQuestion.response_type !== 'yes_no' &&
                        currentQuestion.response_type !== 'text' &&
                        currentQuestion.response_type !== 'optional_text' &&
                        currentQuestion.response_type !== 'optional_text_or_voice' && (
                          <View style={styles.optionsList}>
                            {(currentQuestion.options || ['Better', 'Worse', 'About the same']).map(
                              (opt: string) => {
                                const isSelected = selectedOption === opt;
                                return (
                                  <Pressable
                                    key={opt}
                                    style={[
                                      styles.choiceOptionRow,
                                      isSelected && styles.choiceOptionActive,
                                    ]}
                                    disabled={submittingAnswer}
                                    onPress={() => {
                                      setSelectedOption(opt);
                                      handleAnswerSubmit(opt);
                                    }}
                                  >
                                    <View
                                      style={[
                                        styles.radioCircle,
                                        isSelected && styles.radioCircleActive,
                                      ]}
                                    >
                                      {isSelected && <View style={styles.radioInner} />}
                                    </View>
                                    <Text
                                      style={[
                                        styles.optionText,
                                        isSelected && styles.optionTextActive,
                                      ]}
                                    >
                                      {opt}
                                    </Text>
                                  </Pressable>
                                );
                              }
                            )}
                          </View>
                        )}

                      {(currentQuestion.response_type === 'text' ||
                        currentQuestion.response_type === 'optional_text' ||
                        currentQuestion.response_type === 'optional_text_or_voice') && (
                        <View style={styles.textInputSection}>
                          <TextInput
                            style={styles.textInputBox}
                            placeholder="Share any details or context (optional)..."
                            placeholderTextColor={COLORS.mutedText}
                            multiline
                            numberOfLines={3}
                            value={customText}
                            onChangeText={setCustomText}
                          />
                          <View style={styles.textButtonRow}>
                            <Pressable
                              style={styles.textSubmitButton}
                              disabled={submittingAnswer}
                              onPress={() => handleAnswerSubmit()}
                            >
                              <Text style={styles.textSubmitText}>
                                {customText.trim() ? 'Submit' : 'Skip / No notes'}
                              </Text>
                            </Pressable>
                          </View>
                        </View>
                      )}
                    </ScrollView>

                    {submittingAnswer && (
                      <View style={styles.submittingOverlay}>
                        <ActivityIndicator size="small" color={COLORS.forest} />
                        <Text style={styles.submittingText}>Recording response...</Text>
                      </View>
                    )}
                  </>
                )}
              </View>
            )}

            {checkinStep === 'completed' && (
              <View style={styles.completedContent}>
                <View style={styles.completedIconWrap}>
                  <Ionicons name="checkmark-done" size={36} color={COLORS.forest} />
                </View>
                <Text style={styles.completedTitle}>Check-in Complete! 🌿</Text>
                <Text style={styles.completedSubtitle}>
                  {`Thank you for checking in. All ${answeredCount} responses have been securely stored in your patient profile and updated on your care dashboard.`}
                </Text>

                <View style={styles.completedBadge}>
                  <Ionicons name="shield-checkmark-outline" size={16} color={COLORS.forest} />
                  <Text style={styles.completedBadgeText}>
                    Clinical Risk Metrics Calculated & Synced
                  </Text>
                </View>

                <View style={styles.completedButtonRow}>
                  <Pressable
                    style={styles.primaryButton}
                    onPress={() => setShowCheckinModal(false)}
                  >
                    <Text style={styles.primaryButtonText}>Return to Home</Text>
                  </Pressable>

                  <Pressable
                    style={styles.secondaryButton}
                    onPress={() => {
                      setShowCheckinModal(false);
                      router.push('/voice');
                    }}
                  >
                    <Ionicons name="mic-outline" size={16} color={COLORS.deepForest} />
                    <Text style={styles.secondaryButtonText}>Optional: Voice Check-in</Text>
                  </Pressable>
                </View>
              </View>
            )}
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: COLORS.background,
  },

  content: {
    paddingHorizontal: 22,
    paddingTop: 55,
    paddingBottom: 50,
  },

  /* HEADER */

  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 24,
  },

  small: {
    fontFamily: 'Inter-Medium',
    fontSize: 8,
    letterSpacing: 2,
    color: COLORS.moss,
  },

  logo: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 30,
    color: COLORS.deepForest,
    marginTop: 1,
  },

  profileButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: COLORS.deepForest,
    alignItems: 'center',
    justifyContent: 'center',
  },

  profileLetter: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 22,
    color: COLORS.white,
  },

  /* HERO */

  hero: {
    height: 360,
    borderRadius: 30,
    overflow: 'hidden',
  },

  heroImage: {
    flex: 1,
    justifyContent: 'flex-end',
  },

  heroImageStyle: {
    resizeMode: 'cover',
  },

  heroOverlay: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: 0,
    bottom: 0,
    backgroundColor: 'rgba(28,45,37,0.28)',
  },

  heroContent: {
    padding: 25,
  },

  heroEyebrow: {
    fontFamily: 'Inter-Medium',
    fontSize: 8,
    letterSpacing: 2,
    color: COLORS.stone,
    marginBottom: 12,
  },

  heroTitle: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 42,
    lineHeight: 42,
    color: COLORS.white,
  },

  heroText: {
    fontFamily: 'Inter-Regular',
    fontSize: 11,
    color: COLORS.stone,
    marginTop: 12,
  },

  /* SECTIONS */

  section: {
    marginTop: 38,
  },

  sectionEyebrow: {
    fontFamily: 'Inter-Medium',
    fontSize: 8,
    letterSpacing: 2,
    color: COLORS.forest,
    marginBottom: 9,
  },

  sectionTitle: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 28,
    color: COLORS.deepForest,
  },

  /* ARRIVAL */

  arrivalRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 17,
  },

  arrival: {
    flex: 1,
    minHeight: 165,
    borderRadius: 23,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: 17,
  },

  arrivalIcon: {
    width: 43,
    height: 43,
    borderRadius: 22,
    backgroundColor: COLORS.mist,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 22,
  },

  arrivalTitle: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 22,
    color: COLORS.deepForest,
  },

  arrivalText: {
    fontFamily: 'Inter-Regular',
    fontSize: 10,
    lineHeight: 15,
    color: COLORS.mutedText,
    marginTop: 5,
  },

  /* LIST */

  list: {
    marginTop: 14,
    gap: 9,
  },

  listItem: {
    minHeight: 74,
    borderRadius: 20,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    paddingHorizontal: 15,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 13,
  },

  listIcon: {
    width: 39,
    height: 39,
    borderRadius: 20,
    backgroundColor: COLORS.mist,
    alignItems: 'center',
    justifyContent: 'center',
  },

  listCopy: {
    flex: 1,
  },

  listTitle: {
    fontFamily: 'Inter-Medium',
    fontSize: 12,
    color: COLORS.deepForest,
  },

  listText: {
    fontFamily: 'Inter-Regular',
    fontSize: 10,
    color: COLORS.mutedText,
    marginTop: 3,
  },

  /* SELF HELP FEATURE */

  selfHelpCard: {
    marginTop: 34,
    minHeight: 235,
    borderRadius: 27,
    backgroundColor: '#DDE8D2',
    padding: 22,
    overflow: 'hidden',
    flexDirection: 'row',
    alignItems: 'center',
  },

  selfHelpCopy: {
    flex: 1,
    zIndex: 2,
    paddingRight: 6,
  },

  selfHelpEyebrow: {
    fontFamily: 'Inter-Medium',
    fontSize: 8,
    letterSpacing: 1.8,
    color: COLORS.forest,
    marginBottom: 9,
  },

  selfHelpTitle: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 29,
    lineHeight: 31,
    color: COLORS.deepForest,
  },

  selfHelpText: {
    fontFamily: 'Inter-Regular',
    fontSize: 10,
    lineHeight: 15,
    color: COLORS.mutedText,
    marginTop: 9,
    maxWidth: 190,
  },

  selfHelpButton: {
    alignSelf: 'flex-start',
    marginTop: 17,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 20,
    backgroundColor: COLORS.surface,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
  },

  selfHelpButtonText: {
    fontFamily: 'Inter-Medium',
    fontSize: 10,
    color: COLORS.deepForest,
  },

  selfHelpIllustration: {
    width: 105,
    height: 190,
    marginLeft: -5,
    alignItems: 'center',
    justifyContent: 'center',
  },

  illustrationCircleLarge: {
    position: 'absolute',
    width: 125,
    height: 125,
    borderRadius: 63,
    backgroundColor: 'rgba(255,255,255,0.42)',
  },

  illustrationCircleSmall: {
    position: 'absolute',
    width: 76,
    height: 76,
    borderRadius: 38,
    backgroundColor: 'rgba(255,255,255,0.5)',
  },

  /* BOTTOM TOOLS */

  tools: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 30,
    paddingTop: 20,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },

  tool: {
    alignItems: 'center',
    gap: 7,
  },

  toolText: {
    fontFamily: 'Inter-Regular',
    fontSize: 8,
    color: COLORS.mutedText,
  },

  /* DAILY CHECK-IN POP-UP MODAL STYLES */
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(23, 28, 25, 0.65)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 18,
  },

  modalCard: {
    width: '100%',
    maxWidth: 480,
    backgroundColor: COLORS.surface,
    borderRadius: 28,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: 24,
    shadowColor: COLORS.black,
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.15,
    shadowRadius: 20,
    elevation: 8,
  },

  modalCloseButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: COLORS.surfaceWarm,
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'flex-end',
  },

  /* PROMPT VIEW */
  promptContent: {
    alignItems: 'center',
    paddingVertical: 6,
  },

  promptIconWrap: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: COLORS.mist,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
    marginTop: 4,
  },

  promptEyebrow: {
    fontFamily: 'Inter-Medium',
    fontSize: 9,
    letterSpacing: 2,
    color: COLORS.forest,
    marginBottom: 8,
    textAlign: 'center',
  },

  promptTitle: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 28,
    lineHeight: 32,
    color: COLORS.deepForest,
    textAlign: 'center',
    marginBottom: 10,
  },

  promptSubtitle: {
    fontFamily: 'Inter-Regular',
    fontSize: 12,
    lineHeight: 18,
    color: COLORS.mutedText,
    textAlign: 'center',
    marginBottom: 24,
    paddingHorizontal: 12,
  },

  promptButtonRow: {
    width: '100%',
    gap: 10,
  },

  primaryButton: {
    backgroundColor: COLORS.deepForest,
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 18,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },

  buttonDisabled: {
    opacity: 0.6,
  },

  primaryButtonText: {
    fontFamily: 'Inter-Medium',
    fontSize: 13,
    color: COLORS.white,
  },

  secondaryButton: {
    backgroundColor: COLORS.surfaceWarm,
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 18,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },

  secondaryButtonText: {
    fontFamily: 'Inter-Medium',
    fontSize: 12,
    color: COLORS.mutedText,
  },

  /* QUESTIONNAIRE VIEW */
  questionnaireContent: {
    minHeight: 320,
    maxHeight: 520,
  },

  loadingContainer: {
    paddingVertical: 40,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 14,
  },

  loadingText: {
    fontFamily: 'Inter-Regular',
    fontSize: 12,
    color: COLORS.mutedText,
  },

  questionnaireHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },

  progressInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },

  domainBadge: {
    backgroundColor: COLORS.mist,
    paddingHorizontal: 9,
    paddingVertical: 4,
    borderRadius: 12,
  },

  domainBadgeText: {
    fontFamily: 'Inter-Medium',
    fontSize: 9,
    letterSpacing: 1,
    color: COLORS.deepForest,
    textTransform: 'uppercase',
  },

  progressText: {
    fontFamily: 'Inter-Regular',
    fontSize: 11,
    color: COLORS.mutedText,
  },

  progressBarTrack: {
    height: 5,
    backgroundColor: COLORS.surfaceWarm,
    borderRadius: 3,
    overflow: 'hidden',
    marginBottom: 18,
  },

  progressBarFill: {
    height: '100%',
    backgroundColor: COLORS.forest,
    borderRadius: 3,
  },

  questionScroll: {
    maxHeight: 380,
  },

  questionTitle: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 22,
    lineHeight: 28,
    color: COLORS.deepForest,
    marginBottom: 18,
  },

  optionsList: {
    gap: 9,
  },

  /* SCALE OPTIONS */
  scaleOptionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderRadius: 16,
    backgroundColor: COLORS.surfaceWarm,
    borderWidth: 1,
    borderColor: COLORS.border,
  },

  scaleOptionActive: {
    backgroundColor: '#E4ECE2',
    borderColor: COLORS.forest,
  },

  scaleNumberCircle: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: COLORS.surface,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },

  scaleNumberCircleActive: {
    backgroundColor: COLORS.forest,
  },

  scaleNumberText: {
    fontFamily: 'Inter-Medium',
    fontSize: 11,
    color: COLORS.deepForest,
  },

  scaleNumberTextActive: {
    color: COLORS.white,
  },

  optionText: {
    flex: 1,
    fontFamily: 'Inter-Regular',
    fontSize: 12,
    color: COLORS.text,
  },

  optionTextActive: {
    fontFamily: 'Inter-Medium',
    color: COLORS.deepForest,
  },

  /* YES / NO */
  yesNoRow: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 6,
  },

  yesNoCard: {
    flex: 1,
    paddingVertical: 18,
    borderRadius: 18,
    backgroundColor: COLORS.surfaceWarm,
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },

  yesNoCardActive: {
    backgroundColor: COLORS.deepForest,
    borderColor: COLORS.deepForest,
  },

  yesNoText: {
    fontFamily: 'Inter-Medium',
    fontSize: 13,
    color: COLORS.deepForest,
  },

  yesNoTextActive: {
    color: COLORS.white,
  },

  /* MULTIPLE CHOICE RADIO */
  choiceOptionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderRadius: 16,
    backgroundColor: COLORS.surfaceWarm,
    borderWidth: 1,
    borderColor: COLORS.border,
    gap: 10,
  },

  choiceOptionActive: {
    backgroundColor: '#E4ECE2',
    borderColor: COLORS.forest,
  },

  radioCircle: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 1.5,
    borderColor: COLORS.mutedText,
    alignItems: 'center',
    justifyContent: 'center',
  },

  radioCircleActive: {
    borderColor: COLORS.forest,
  },

  radioInner: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: COLORS.forest,
  },

  /* TEXT INPUT */
  textInputSection: {
    marginTop: 6,
    gap: 12,
  },

  textInputBox: {
    backgroundColor: COLORS.surfaceWarm,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: 14,
    fontFamily: 'Inter-Regular',
    fontSize: 12,
    color: COLORS.text,
    minHeight: 80,
    textAlignVertical: 'top',
  },

  textButtonRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
  },

  textSubmitButton: {
    backgroundColor: COLORS.deepForest,
    paddingVertical: 10,
    paddingHorizontal: 18,
    borderRadius: 14,
  },

  textSubmitText: {
    fontFamily: 'Inter-Medium',
    fontSize: 11,
    color: COLORS.white,
  },

  submittingOverlay: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingTop: 12,
  },

  submittingText: {
    fontFamily: 'Inter-Regular',
    fontSize: 11,
    color: COLORS.forest,
  },

  /* COMPLETED VIEW */
  completedContent: {
    alignItems: 'center',
    paddingVertical: 14,
  },

  completedIconWrap: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#DCE8D2',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },

  completedTitle: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 26,
    lineHeight: 30,
    color: COLORS.deepForest,
    textAlign: 'center',
    marginBottom: 8,
  },

  completedSubtitle: {
    fontFamily: 'Inter-Regular',
    fontSize: 12,
    lineHeight: 18,
    color: COLORS.mutedText,
    textAlign: 'center',
    marginBottom: 16,
    paddingHorizontal: 10,
  },

  completedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: COLORS.mist,
    paddingVertical: 7,
    paddingHorizontal: 14,
    borderRadius: 14,
    marginBottom: 22,
  },

  completedBadgeText: {
    fontFamily: 'Inter-Medium',
    fontSize: 10,
    color: COLORS.deepForest,
  },

  completedButtonRow: {
    width: '100%',
    gap: 10,
  },
});