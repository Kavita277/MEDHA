import React, { useMemo, useState } from 'react';
import {
  Alert,
  Linking,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { MedhaBottomNav } from '../components/medha-bottom-nav';
import { COLORS } from '../constants/colors';
import { RADIUS, SHADOW } from '../constants/theme';

/*
  MEDHA Self Help Library (Screen 18)
  Preserves:
  - All 7 clinical self-help modules
  - Category filtering
  - Step-by-step guides with progress tracking
  - Evidence/source links (WHO, NIMH, NHS, UNICEF, NIA)
  - Tele-MANAS pathway & emergency safety links
  - Medical disclaimer
*/

type Step = { id: string; title: string; body: string; tip?: string };
type Module = {
  id: string;
  title: string;
  subtitle: string;
  category: 'condition' | 'population';
  topic: 'anxiety' | 'sleep' | 'stress' | 'for-you';
  type: string;
  duration: string;
  icon: string;
  iconBg: string;
  color: string;
  borderColor: string;
  sourceIds: string[];
  steps: Step[];
};

const SOURCES = [
  { id: 'who-stress', org: 'WHO', title: 'Doing What Matters in Times of Stress', url: 'https://www.who.int/publications/i/item/9789240003927' },
  { id: 'who-depression', org: 'WHO', title: 'Step-by-Step self-help intervention', url: 'https://www.who.int/publications/i/item/B09738' },
  { id: 'nimh-anxiety', org: 'NIMH', title: 'Generalized Anxiety Disorder', url: 'https://www.nimh.nih.gov/health/publications/generalized-anxiety-disorder-gad' },
  { id: 'nhs-panic', org: 'NHS', title: 'Panic Disorder', url: 'https://www.nhs.uk/mental-health/conditions/panic-disorder/' },
  { id: 'unicef', org: 'UNICEF', title: 'Adolescent Mental Health Hub', url: 'https://www.unicef.org/adolescentmentalhealthhub/resources/adolescents' },
  { id: 'nia', org: 'NIA', title: 'Mental and Emotional Health', url: 'https://www.nia.nih.gov/health/mental-and-emotional-health' },
];

const MODULES: Module[] = [
  {
    id: 'anxiety',
    title: 'Managing Anxiety',
    subtitle: 'Gentle steps for moments when worry feels overwhelming.',
    category: 'condition',
    topic: 'anxiety',
    type: 'Guided Exercise',
    duration: '5 min',
    icon: '🌿',
    iconBg: COLORS.greenSoft,
    color: COLORS.white,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    sourceIds: ['who-stress', 'nimh-anxiety'],
    steps: [
      { id: 'a1', title: 'Pause for a moment', body: 'If you can, stop what you are doing for a moment. Sit somewhere comfortable and allow yourself a little space before deciding what to do next.' },
      { id: 'a2', title: 'Notice what is happening', body: 'Notice what you are feeling, what your body is doing, and what is happening around you. You do not need to solve everything immediately.' },
      { id: 'a3', title: 'Slow your breathing', body: 'Take a gentle breath in and allow the breath to leave slowly. Continue at a comfortable pace without forcing the breath.', tip: 'If focusing on breathing makes you uncomfortable, return your attention to your surroundings instead.' },
      { id: 'a4', title: 'Choose one small action', body: 'Ask yourself: what is one small thing I can do right now that is within my control? Keep the action simple.' },
      { id: 'a5', title: 'Reach out when needed', body: 'If this continues or becomes difficult to manage, consider speaking with a qualified health professional or someone you trust.' },
    ],
  },
  {
    id: 'panic',
    title: 'Better Sleep & Calming',
    subtitle: 'A simple audio guide for resting and settling an active mind.',
    category: 'condition',
    topic: 'sleep',
    type: 'Audio Guide',
    duration: '7 min',
    icon: '🌙',
    iconBg: COLORS.blueSoft,
    color: COLORS.white,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    sourceIds: ['nhs-panic'],
    steps: [
      { id: 'p1', title: 'Stay where you are if possible', body: 'If it is safe to do so, remain where you are and give yourself time for the intense feelings to settle.' },
      { id: 'p2', title: 'Breathe slowly', body: 'Try slow, gentle breathing. Avoid forcing very deep breaths. Let the breath become steady and comfortable.' },
      { id: 'p3', title: 'Remind yourself', body: 'Intense moments feel heavy, but remember that thoughts come and pass like ripples on water.' },
      { id: 'p4', title: 'Focus on something calming', body: 'Bring your attention toward something peaceful in your surroundings or another safe, calming image.' },
    ],
  },
  {
    id: 'low-mood',
    title: 'Positive Self-Talk',
    subtitle: 'Gentle cognitive reframing and small, kind activity planning.',
    category: 'condition',
    topic: 'stress',
    type: 'CBT Exercise',
    duration: '3 min',
    icon: '☀️',
    iconBg: COLORS.yellowSoft,
    color: COLORS.white,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    sourceIds: ['who-depression'],
    steps: [
      { id: 'd1', title: 'Start smaller than you think', body: 'When motivation is low, choose a task that feels realistically manageable rather than trying to change everything at once.' },
      { id: 'd2', title: 'Choose one meaningful activity', body: 'Pick one activity connected to something you value: personal care, a short walk, music, talking to someone, or another meaningful activity.' },
      { id: 'd3', title: 'Put it on your day', body: 'Choose a realistic time. Treat the activity as an appointment with yourself rather than waiting until you feel motivated.' },
      { id: 'd4', title: 'Notice what happened', body: 'Afterwards, briefly notice how you felt before and after the activity. Small changes are still worth noticing.' },
      { id: 'd5', title: 'Build gradually', body: 'If an activity feels manageable, you can gradually add another small activity. Progress does not have to happen all at once.' },
    ],
  },
  {
    id: 'stress',
    title: 'Building Resilience',
    subtitle: 'Ground yourself and return to what matters most.',
    category: 'condition',
    topic: 'stress',
    type: 'Daily Read',
    duration: '5 min',
    icon: '📖',
    iconBg: COLORS.greenSoft,
    color: COLORS.white,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    sourceIds: ['who-stress'],
    steps: [
      { id: 's1', title: 'Notice and name', body: 'Notice what thoughts, feelings or sensations are present. Naming what is happening can create a little distance from the experience.' },
      { id: 's2', title: 'Ground yourself', body: 'Bring your attention to your surroundings. Notice what you can see, hear or physically feel around you.' },
      { id: 's3', title: 'Make room for the feeling', body: 'Instead of immediately fighting the feeling, allow it to be present while you continue taking care of yourself.' },
      { id: 's4', title: 'Reconnect with what matters', body: 'Ask yourself what matters to you in this moment. Choose one small action that moves you in that direction.' },
      { id: 's5', title: 'Be kind to yourself', body: 'Speak to yourself with the same kindness you would offer someone you care about.' },
    ],
  },
  {
    id: 'adolescents',
    title: 'For Adolescents',
    subtitle: 'Tools for navigating emotions, school pressure, and friendships.',
    category: 'population',
    topic: 'for-you',
    type: 'Youth Guide',
    duration: '6 min',
    icon: '✨',
    iconBg: '#F3EFFF',
    color: COLORS.white,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    sourceIds: ['unicef'],
    steps: [
      { id: 'ad1', title: 'Name the emotion', body: 'Try putting a simple name to what you are feeling: worried, angry, lonely, overwhelmed, disappointed or something else.' },
      { id: 'ad2', title: 'Give yourself a pause', body: 'Before reacting, take a short pause. Slow breathing, stretching or noticing your surroundings can help you settle.' },
      { id: 'ad3', title: 'Think about your options', body: 'Ask: what is actually in my control? What is one safe and useful action I can take?' },
      { id: 'ad4', title: 'Talk to someone safe', body: 'Consider speaking with a trusted friend, parent, teacher, counsellor or another supportive adult.' },
      { id: 'ad5', title: 'Practice, don’t perfect', body: 'Emotional skills improve with practice. You do not have to handle every difficult moment perfectly.' },
    ],
  },
  {
    id: 'older-adults',
    title: 'For Older Adults',
    subtitle: 'Gentle routines for everyday connection, movement, and peace.',
    category: 'population',
    topic: 'for-you',
    type: 'Daily Routine',
    duration: '5 min',
    icon: '🍃',
    iconBg: COLORS.sageSoft,
    color: COLORS.white,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    sourceIds: ['nia'],
    steps: [
      { id: 'oa1', title: 'Start gently', body: 'Choose an activity appropriate for your abilities and current health. Even small amounts of movement can be a starting point.' },
      { id: 'oa2', title: 'Stay connected', body: 'Think of one person you would enjoy speaking with or one community activity that feels comfortable.' },
      { id: 'oa3', title: 'Do something meaningful', body: 'Gardening, walking, reading, music, helping others or another enjoyable activity can give structure and purpose to the day.' },
      { id: 'oa4', title: 'Keep a simple routine', body: 'Regular sleep, meals, movement and social contact can help create structure.' },
    ],
  },
  {
    id: 'caregivers',
    title: 'For Caregivers',
    subtitle: 'Protecting your own emotional wellbeing while caring for others.',
    category: 'population',
    topic: 'for-you',
    type: 'Self-Care',
    duration: '6 min',
    icon: '💛',
    iconBg: COLORS.creamSecondary,
    color: COLORS.white,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    sourceIds: ['nia'],
    steps: [
      { id: 'c1', title: 'Notice your own needs', body: 'Supporting someone else can be demanding. Take a moment to notice your own energy, emotions and needs.' },
      { id: 'c2', title: 'Accept small breaks', body: 'A short break, a conversation with someone you trust, or a few minutes doing something restorative can matter.' },
      { id: 'c3', title: 'Ask for practical help', body: 'Consider whether someone can help with a specific task rather than trying to manage everything yourself.' },
      { id: 'c4', title: 'Keep one thing for yourself', body: 'Protect a small activity that is meaningful or enjoyable to you.' },
      { id: 'c5', title: 'Seek support when needed', body: 'If stress, low mood or exhaustion is persistent or interfering with daily functioning, consider speaking with a health professional.' },
    ],
  },
];

type FilterCategory = 'all' | 'anxiety' | 'sleep' | 'stress' | 'for-you';

function ModuleGuideView({ module, onBack }: { module: Module; onBack: () => void }) {
  const [step, setStep] = useState(0);
  const current = module.steps[step];
  const progressPercent = Math.round(((step + 1) / module.steps.length) * 100);

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.guideScrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* TOP BAR */}
        <View style={styles.topBar}>
          <Pressable
            onPress={onBack}
            style={({ pressed }) => [
              styles.iconButton,
              pressed && styles.pressed,
            ]}
            hitSlop={12}
            accessibilityRole="button"
            accessibilityLabel="Back to library"
          >
            <Ionicons name="arrow-back" size={20} color={COLORS.navy} />
          </Pressable>

          <View style={styles.guideTypeBadge}>
            <Text style={styles.guideType}>{module.type.toUpperCase()}</Text>
          </View>
        </View>

        <Text style={styles.guideTitle}>{module.title}</Text>

        {/* PROGRESS BAR */}
        <View style={styles.progressRow}>
          <Text style={styles.progressLabel}>
            STEP {step + 1} OF {module.steps.length}
          </Text>
          <Text style={styles.progressLabel}>{progressPercent}%</Text>
        </View>
        <View style={styles.progressBarTrack}>
          <View style={[styles.progressBarFill, { width: `${progressPercent}%` }]} />
        </View>

        {/* ILLUSTRATION BANNER */}
        <View style={[styles.guideBanner, { backgroundColor: module.iconBg }]}>
          <Text style={styles.guideEmoji}>{module.icon}</Text>
          <View style={styles.stepCounterBadge}>
            <Text style={styles.stepCounterText}>Step {step + 1}</Text>
          </View>
        </View>

        {/* STEP CONTENT */}
        <Text style={styles.stepTitle}>{current.title}</Text>
        <Text style={styles.stepBody}>{current.body}</Text>

        {current.tip && (
          <View style={styles.tipCard}>
            <View style={styles.tipHeader}>
              <Ionicons name="bulb-outline" size={15} color={COLORS.yellowDark} />
              <Text style={styles.tipLabel}>GENTLE TIP</Text>
            </View>
            <Text style={styles.tipText}>{current.tip}</Text>
          </View>
        )}

        {/* STEP DOTS */}
        <View style={styles.dotsRow}>
          {module.steps.map((item, index) => (
            <View
              key={item.id}
              style={[
                styles.dot,
                index === step && styles.dotActive,
              ]}
            />
          ))}
        </View>

        {/* STEP NAVIGATION BUTTONS */}
        <View style={styles.navRow}>
          <Pressable
            disabled={step === 0}
            onPress={() => setStep((v) => v - 1)}
            style={({ pressed }) => [
              styles.navSecondaryButton,
              step === 0 && styles.navButtonDisabled,
              pressed && step > 0 && styles.pressed,
            ]}
            accessibilityRole="button"
            accessibilityLabel="Previous step"
          >
            <Text style={styles.navSecondaryText}>Previous</Text>
          </Pressable>

          <Pressable
            onPress={() => {
              if (step === module.steps.length - 1) {
                Alert.alert(
                  'Resource Completed',
                  'Small steps matter. You took intentional time for your wellbeing today.',
                  [{ text: 'Return to Library', onPress: onBack }]
                );
              } else {
                setStep((v) => v + 1);
              }
            }}
            style={({ pressed }) => [
              styles.navPrimaryButton,
              pressed && styles.pressed,
            ]}
            accessibilityRole="button"
            accessibilityLabel={step === module.steps.length - 1 ? 'Complete Guide' : 'Next step'}
          >
            <Text style={styles.navPrimaryText}>
              {step === module.steps.length - 1 ? 'Complete Guide' : 'Next Step'}
            </Text>
            <Ionicons
              name={step === module.steps.length - 1 ? 'checkmark-circle' : 'arrow-forward'}
              size={18}
              color={COLORS.white}
            />
          </Pressable>
        </View>

        {/* EVIDENCE & SOURCES (Fix TS2820 with open-outline) */}
        <View style={styles.sourcesCard}>
          <Text style={styles.sourcesHeader}>Evidence & Sources</Text>
          <Text style={styles.sourcesSub}>
            Grounded in public health publications and clinical guidelines.
          </Text>

          {module.sourceIds.map((id) => {
            const source = SOURCES.find((s) => s.id === id);
            if (!source) return null;

            return (
              <Pressable
                key={source.id}
                onPress={() => Linking.openURL(source.url)}
                style={({ pressed }) => [
                  styles.sourceLinkRow,
                  pressed && styles.pressed,
                ]}
                accessibilityRole="link"
                accessibilityLabel={`${source.org}: ${source.title}`}
              >
                <View style={styles.sourceIconWrap}>
                  <Ionicons name="open-outline" size={15} color={COLORS.coralDark} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.sourceOrg}>{source.org}</Text>
                  <Text style={styles.sourceTitle}>{source.title}</Text>
                </View>
              </Pressable>
            );
          })}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

export default function SelfHelpScreen() {
  const router = useRouter();
  const [filter, setFilter] = useState<FilterCategory>('all');
  const [selectedModule, setSelectedModule] = useState<Module | null>(null);

  const filteredModules = useMemo(() => {
    if (filter === 'all') return MODULES;
    return MODULES.filter((m) => m.topic === filter);
  }, [filter]);

  if (selectedModule) {
    return (
      <ModuleGuideView
        module={selectedModule}
        onBack={() => setSelectedModule(null)}
      />
    );
  }

  const FILTERS: { id: FilterCategory; label: string }[] = [
    { id: 'all', label: 'All' },
    { id: 'anxiety', label: 'Anxiety' },
    { id: 'sleep', label: 'Sleep' },
    { id: 'stress', label: 'Stress' },
    { id: 'for-you', label: 'For You' },
  ];

  return (
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
              onPress={() => router.push('/mood-calendar')}
              style={({ pressed }) => [
                styles.calendarBadge,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Mood Calendar"
            >
              <Ionicons name="calendar-outline" size={14} color={COLORS.coralDark} />
              <Text style={styles.calendarBadgeText}>Mood Calendar</Text>
            </Pressable>
          </View>

          {/* SCREEN TITLE */}
          <View style={styles.header}>
            <Text style={styles.title}>Self-Care Resources</Text>
            <Text style={styles.subtitle}>
              Evidence-grounded guides and practical coping exercises.
            </Text>
          </View>

          {/* HORIZONTAL CATEGORY FILTER PILLS */}
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.filtersScroll}
          >
            {FILTERS.map((item) => {
              const active = filter === item.id;
              return (
                <Pressable
                  key={item.id}
                  onPress={() => setFilter(item.id)}
                  style={({ pressed }) => [
                    styles.filterChip,
                    active && styles.filterChipActive,
                    pressed && styles.pressed,
                  ]}
                  accessibilityRole="button"
                  accessibilityState={{ selected: active }}
                >
                  <Text
                    style={[
                      styles.filterText,
                      active && styles.filterTextActive,
                    ]}
                  >
                    {item.label}
                  </Text>
                </Pressable>
              );
            })}
          </ScrollView>

          {/* RESOURCE CARD LIST MATCHING REFERENCE SCREEN 18 */}
          <View style={styles.resourceList}>
            {filteredModules.map((item) => (
              <Pressable
                key={item.id}
                onPress={() => setSelectedModule(item)}
                style={({ pressed }) => [
                  styles.resourceCard,
                  pressed && styles.pressed,
                ]}
                accessibilityRole="button"
                accessibilityLabel={`${item.title}, ${item.type}, ${item.duration}`}
              >
                {/* Pastel Squircle Icon Badge */}
                <View style={[styles.resourceIconBadge, { backgroundColor: item.iconBg }]}>
                  <Text style={styles.resourceEmoji}>{item.icon}</Text>
                </View>

                {/* Resource Info */}
                <View style={styles.resourceInfo}>
                  <Text style={styles.resourceTitle}>{item.title}</Text>
                  <Text style={styles.resourceSubtitle}>
                    {item.type} • {item.duration}
                  </Text>
                </View>

                {/* Chevron */}
                <View style={styles.chevronWrap}>
                  <Ionicons name="chevron-forward" size={18} color={COLORS.navyMuted} />
                </View>
              </Pressable>
            ))}
          </View>

          {/* TELE-MANAS & CLINICAL SAFETY CARD */}
          <View style={styles.teleManasCard}>
            <View style={styles.teleManasIconWrap}>
              <Ionicons name="call" size={18} color={COLORS.coralDark} />
            </View>
            <View style={styles.teleManasTextWrap}>
              <Text style={styles.teleManasTitle}>Need immediate human support?</Text>
              <Text style={styles.teleManasSub}>
                Self-help is educational. If you feel overwhelmed, connect with Tele-MANAS free 24/7.
              </Text>
              <Pressable
                onPress={() => Linking.openURL('tel:14416')}
                style={({ pressed }) => [
                  styles.teleManasBtn,
                  pressed && styles.pressed,
                ]}
                accessibilityRole="button"
                accessibilityLabel="Call Tele-MANAS toll-free 14416"
              >
                <Text style={styles.teleManasBtnText}>Call Tele-MANAS · 14416</Text>
                <Ionicons name="arrow-forward" size={14} color={COLORS.white} />
              </Pressable>
            </View>
          </View>

          {/* MEDICAL DISCLAIMER */}
          <Text style={styles.disclaimerText}>
            MEDHA resources are informed by published public health materials and do not provide medical diagnosis or substitute professional treatment.
          </Text>
        </ScrollView>

        {/* FLOATING BOTTOM NAVIGATION */}
        <MedhaBottomNav activeTab="explore" />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: COLORS.porcelain,
  },
  container: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 20,
    paddingTop: 8,
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
  calendarBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: RADIUS.pill,
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    ...SHADOW.subtle,
  },
  calendarBadgeText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 12,
    color: COLORS.navy,
  },

  /* HEADER */
  header: {
    marginTop: 12,
    marginBottom: 16,
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
    color: COLORS.navyMuted,
    marginTop: 4,
  },

  /* CATEGORY FILTERS */
  filtersScroll: {
    flexDirection: 'row',
    gap: 8,
    paddingBottom: 14,
  },
  filterChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: RADIUS.pill,
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    ...SHADOW.subtle,
  },
  filterChipActive: {
    backgroundColor: COLORS.navy,
    borderColor: COLORS.navy,
  },
  filterText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 13,
    color: COLORS.navyMuted,
  },
  filterTextActive: {
    color: COLORS.white,
    fontFamily: 'Fredoka-Medium',
  },

  /* RESOURCE LIST */
  resourceList: {
    gap: 12,
    marginTop: 4,
  },
  resourceCard: {
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.card,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    ...SHADOW.subtle,
  },
  resourceIconBadge: {
    width: 48,
    height: 48,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  resourceEmoji: {
    fontSize: 22,
  },
  resourceInfo: {
    flex: 1,
  },
  resourceTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 16,
    lineHeight: 20,
    color: COLORS.navy,
  },
  resourceSubtitle: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    lineHeight: 16,
    color: COLORS.navyMuted,
    marginTop: 3,
  },
  chevronWrap: {
    width: 28,
    height: 28,
    alignItems: 'center',
    justifyContent: 'center',
  },

  /* TELE-MANAS CARD */
  teleManasCard: {
    marginTop: 22,
    backgroundColor: COLORS.creamSecondary,
    borderRadius: RADIUS.card,
    borderWidth: 1,
    borderColor: COLORS.peach,
    padding: 16,
    flexDirection: 'row',
    gap: 12,
    ...SHADOW.subtle,
  },
  teleManasIconWrap: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: 'rgba(255, 122, 89, 0.15)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  teleManasTextWrap: {
    flex: 1,
  },
  teleManasTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 15,
    color: COLORS.navy,
  },
  teleManasSub: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    lineHeight: 17,
    color: COLORS.navyMuted,
    marginTop: 4,
  },
  teleManasBtn: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: COLORS.coral,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: RADIUS.pill,
    marginTop: 10,
  },
  teleManasBtnText: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 12,
    color: COLORS.white,
  },

  disclaimerText: {
    fontFamily: 'Nunito-Regular',
    fontSize: 10,
    lineHeight: 15,
    textAlign: 'center',
    color: COLORS.subtleText,
    marginTop: 18,
    marginBottom: 10,
    paddingHorizontal: 14,
  },

  /* GUIDE VIEW */
  guideScrollContent: {
    flexGrow: 1,
    paddingHorizontal: 20,
    paddingTop: 8,
    paddingBottom: 40,
  },
  guideTypeBadge: {
    backgroundColor: COLORS.white,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: RADIUS.pill,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
  },
  guideType: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1.1,
    color: COLORS.coralDark,
  },
  guideTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 26,
    lineHeight: 32,
    color: COLORS.navy,
    marginTop: 12,
  },
  progressRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 14,
  },
  progressLabel: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1.1,
    color: COLORS.navyMuted,
  },
  progressBarTrack: {
    height: 6,
    borderRadius: 3,
    backgroundColor: 'rgba(0, 0, 0, 0.06)',
    overflow: 'hidden',
    marginTop: 6,
  },
  progressBarFill: {
    height: '100%',
    borderRadius: 3,
    backgroundColor: COLORS.navy,
  },
  guideBanner: {
    height: 160,
    borderRadius: RADIUS.card,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    marginTop: 18,
    alignItems: 'center',
    justifyContent: 'center',
    ...SHADOW.subtle,
  },
  guideEmoji: {
    fontSize: 48,
  },
  stepCounterBadge: {
    position: 'absolute',
    top: 12,
    left: 14,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  stepCounterText: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 11,
    color: COLORS.navy,
  },
  stepTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 20,
    lineHeight: 26,
    color: COLORS.navy,
    marginTop: 20,
  },
  stepBody: {
    fontFamily: 'Nunito-Regular',
    fontSize: 14,
    lineHeight: 22,
    color: COLORS.navy,
    marginTop: 8,
  },
  tipCard: {
    backgroundColor: COLORS.yellowSoft,
    borderRadius: RADIUS.card,
    borderWidth: 1,
    borderColor: COLORS.yellow,
    padding: 14,
    marginTop: 16,
  },
  tipHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 4,
  },
  tipLabel: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1.2,
    color: COLORS.yellowDark,
  },
  tipText: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    lineHeight: 18,
    color: COLORS.navy,
  },
  dotsRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 6,
    marginVertical: 20,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: 'rgba(0, 0, 0, 0.15)',
  },
  dotActive: {
    width: 20,
    backgroundColor: COLORS.navy,
  },
  navRow: {
    flexDirection: 'row',
    gap: 12,
    alignItems: 'center',
  },
  navSecondaryButton: {
    flex: 1,
    height: 50,
    borderRadius: RADIUS.pill,
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.08)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  navSecondaryText: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 14,
    color: COLORS.navy,
  },
  navPrimaryButton: {
    flex: 2,
    height: 50,
    borderRadius: RADIUS.pill,
    backgroundColor: COLORS.navy,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    ...SHADOW.dock,
  },
  navPrimaryText: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 14,
    color: COLORS.white,
  },
  navButtonDisabled: {
    opacity: 0.4,
  },
  sourcesCard: {
    marginTop: 26,
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.card,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    padding: 16,
    ...SHADOW.subtle,
  },
  sourcesHeader: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 15,
    color: COLORS.navy,
  },
  sourcesSub: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    color: COLORS.navyMuted,
    marginTop: 2,
    marginBottom: 12,
  },
  sourceLinkRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingVertical: 8,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0, 0, 0, 0.04)',
  },
  sourceIconWrap: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: COLORS.creamSecondary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sourceOrg: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1,
    color: COLORS.coralDark,
  },
  sourceTitle: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    color: COLORS.navy,
  },

  pressed: {
    transform: [{ scale: 0.97 }],
    opacity: 0.88,
  },
});
