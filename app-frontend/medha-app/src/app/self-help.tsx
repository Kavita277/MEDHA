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

import { MedhaBackground } from '../components/medha-background';
import { MedhaButton } from '../components/medha-button';
import { COLORS } from '../constants/colors';
import { RADIUS, SHADOW } from '../constants/theme';

/*
  MEDHA Self Help
  Source intent preserved:
  - educational/supportive content
  - no diagnosis
  - no medication advice
  - not a replacement for professional care
  - evidence/source links
  - Tele-MANAS pathway
*/

type Step = { id: string; title: string; body: string; tip?: string };
type Module = {
  id: string;
  title: string;
  subtitle: string;
  category: 'condition' | 'population';
  type: string;
  duration: string;
  icon: string;
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
    type: 'Anxiety',
    duration: '5 min',
    icon: '🌿',
    color: COLORS.greenSoft,
    borderColor: COLORS.green,
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
    title: 'During a Panic Episode',
    subtitle: 'A simple guide for getting through an intense moment.',
    category: 'condition',
    type: 'Panic',
    duration: '4 min',
    icon: '🌊',
    color: COLORS.blueSoft,
    borderColor: COLORS.blue,
    sourceIds: ['nhs-panic'],
    steps: [
      { id: 'p1', title: 'Stay where you are if possible', body: 'If it is safe to do so, remain where you are and give yourself time for the intense feelings to settle.' },
      { id: 'p2', title: 'Breathe slowly', body: 'Try slow, gentle breathing. Avoid forcing very deep breaths. Let the breath become steady and comfortable.' },
      { id: 'p3', title: 'Remind yourself', body: 'A panic episode can feel frightening. Remind yourself that intense sensations can pass.' },
      { id: 'p4', title: 'Focus on something calming', body: 'Bring your attention toward something peaceful in your surroundings or another safe, calming image.' },
    ],
  },
  {
    id: 'low-mood',
    title: 'Taking the First Small Step',
    subtitle: 'Gentle activity planning when everything feels difficult.',
    category: 'condition',
    type: 'Low mood',
    duration: '7 min',
    icon: '☀️',
    color: COLORS.yellowSoft,
    borderColor: COLORS.yellow,
    sourceIds: ['who-depression'],
    steps: [
      { id: 'd1', title: 'Start smaller than you think', body: 'When motivation is low, choose a task that feels realistically manageable rather than trying to change everything at once.' },
      { id: 'd2', title: 'Choose one meaningful activity', body: 'Pick one activity connected to something you value: personal care, a short walk, music, talking to someone, studying for a few minutes, or another meaningful activity.' },
      { id: 'd3', title: 'Put it on your day', body: 'Choose a realistic time. Treat the activity as an appointment with yourself rather than waiting until you feel motivated.' },
      { id: 'd4', title: 'Notice what happened', body: 'Afterwards, briefly notice how you felt before and after the activity. Small changes are still worth noticing.' },
      { id: 'd5', title: 'Build gradually', body: 'If an activity feels manageable, you can gradually add another small activity. Progress does not have to happen all at once.' },
    ],
  },
  {
    id: 'stress',
    title: 'When Stress Feels Too Much',
    subtitle: 'Ground yourself and return to what matters.',
    category: 'condition',
    type: 'Stress',
    duration: '5 min',
    icon: '🌸',
    color: COLORS.pinkSoft,
    borderColor: COLORS.pink,
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
    subtitle: 'Tools for emotions, stress, friendships and confidence.',
    category: 'population',
    type: 'Adolescents',
    duration: '6 min',
    icon: '✨',
    color: '#F3EFFF',
    borderColor: COLORS.lavender,
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
    subtitle: 'Small routines for connection, movement and wellbeing.',
    category: 'population',
    type: 'Older adults',
    duration: '5 min',
    icon: '🍃',
    color: COLORS.sageSoft,
    borderColor: COLORS.sage,
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
    subtitle: 'Protecting your own wellbeing while supporting someone else.',
    category: 'population',
    type: 'Caregivers',
    duration: '6 min',
    icon: '💛',
    color: COLORS.creamSecondary,
    borderColor: COLORS.peach,
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

function Guide({ module, onBack }: { module: Module; onBack: () => void }) {
  const [step, setStep] = useState(0);
  const current = module.steps[step];
  const progressPercent = Math.round(((step + 1) / module.steps.length) * 100);

  return (
    <MedhaBackground variant="calm">
      <SafeAreaView style={styles.screen}>
        <ScrollView contentContainerStyle={styles.guideContent} showsVerticalScrollIndicator={false}>
          {/* TOP BAR */}
          <View style={styles.guideTopBar}>
            <Pressable
              onPress={onBack}
              style={({ pressed }) => [
                styles.iconButton,
                pressed && styles.pressed,
              ]}
              hitSlop={12}
              accessibilityRole="button"
              accessibilityLabel="Back to self-help modules"
            >
              <Ionicons name="arrow-back" size={20} color={COLORS.navy} />
            </Pressable>

            <View style={styles.guideTypeBadge}>
              <Text style={styles.guideType}>{module.type.toUpperCase()}</Text>
            </View>
          </View>

          <Text style={styles.guideTitle}>{module.title}</Text>

          {/* PROGRESS */}
          <View style={styles.progressTop}>
            <Text style={styles.progressLabel}>STEP {step + 1} OF {module.steps.length}</Text>
            <Text style={styles.progressLabel}>{progressPercent}%</Text>
          </View>
          <View style={styles.track}>
            <View style={[styles.fill, { width: `${progressPercent}%` }]} />
          </View>

          {/* ILLUSTRATION BANNER */}
          <View style={[styles.illustrationBanner, { backgroundColor: module.color, borderColor: module.borderColor }]}>
            <View style={styles.softCircle} />
            <Text style={styles.bigEmoji}>{module.icon}</Text>
            <View style={styles.stepBadge}>
              <Text style={styles.stepBadgeText}>Step {step + 1}</Text>
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

          {/* DOTS */}
          <View style={styles.dots}>
            {module.steps.map((item, index) => (
              <View
                key={item.id}
                style={[
                  styles.dot,
                  index === step && styles.activeDot,
                ]}
              />
            ))}
          </View>

          {/* STEP NAVIGATION */}
          <View style={styles.navRow}>
            <View style={{ flex: 1 }}>
              <MedhaButton
                title="Back"
                variant="soft"
                size="md"
                disabled={step === 0}
                onPress={() => setStep((value) => value - 1)}
              />
            </View>

            <View style={{ flex: 2 }}>
              <MedhaButton
                title={step === module.steps.length - 1 ? 'Complete Guide' : 'Next step'}
                variant="coral"
                size="md"
                icon={step === module.steps.length - 1 ? 'checkmark-circle' : 'arrow-forward'}
                iconPosition="right"
                onPress={() => {
                  if (step === module.steps.length - 1) {
                    Alert.alert('Nice work', 'Small steps count. You took time for yourself today.', [
                      { text: 'Done', onPress: onBack },
                    ]);
                  } else {
                    setStep((value) => value + 1);
                  }
                }}
              />
            </View>
          </View>

          <Text style={styles.swipeNote}>Move through the guide at your own pace.</Text>

          {/* EVIDENCE & SOURCES (Fix TS2820 by using open-outline) */}
          <View style={styles.sources}>
            <Text style={styles.sourcesTitle}>Evidence & Sources</Text>
            <Text style={styles.sourcesSub}>
              Grounded in recommendations from recognized public health bodies.
            </Text>

            {module.sourceIds.map((id) => {
              const source = SOURCES.find((item) => item.id === id);
              if (!source) return null;

              return (
                <Pressable
                  key={source.id}
                  style={({ pressed }) => [
                    styles.sourceRow,
                    pressed && styles.pressed,
                  ]}
                  onPress={() => Linking.openURL(source.url)}
                  accessibilityRole="link"
                >
                  <View style={styles.sourceIcon}>
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
    </MedhaBackground>
  );
}

export default function SelfHelpScreen() {
  const router = useRouter();
  const [filter, setFilter] = useState<'all' | 'condition' | 'population'>('all');
  const [selected, setSelected] = useState<Module | null>(null);

  const filtered = useMemo(
    () => (filter === 'all' ? MODULES : MODULES.filter((item) => item.category === filter)),
    [filter]
  );

  if (selected) {
    return <Guide module={selected} onBack={() => setSelected(null)} />;
  }

  return (
    <MedhaBackground variant="calm">
      <SafeAreaView style={styles.screen}>
        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.content}
          keyboardShouldPersistTaps="handled"
        >
          {/* HEADER */}
          <Pressable
            onPress={() => router.back()}
            style={({ pressed }) => [
              styles.iconButton,
              pressed && styles.pressed,
            ]}
            hitSlop={12}
            accessibilityRole="button"
            accessibilityLabel="Back to Home"
          >
            <Ionicons name="arrow-back" size={20} color={COLORS.navy} />
          </Pressable>

          <View style={styles.header}>
            <Text style={styles.eyebrow}>YOUR WELLBEING</Text>
            <Text style={styles.heroTitle}>
              {'Small steps.\nA calmer moment.'}
            </Text>
            <Text style={styles.heroText}>
              Explore simple, evidence-informed guides for difficult moments and everyday wellbeing.
            </Text>
          </View>

          {/* CATEGORY FILTER PILLS */}
          <View style={styles.filters}>
            {[
              { id: 'all' as const, label: 'All Guides' },
              { id: 'condition' as const, label: 'Difficult Moments' },
              { id: 'population' as const, label: 'For You' },
            ].map((item) => {
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
                  <Text style={[styles.filterText, active && styles.filterTextActive]}>
                    {item.label}
                  </Text>
                </Pressable>
              );
            })}
          </View>

          {/* MODULE GRID */}
          <Text style={styles.sectionTitle}>Guides for difficult moments</Text>

          <View style={styles.grid}>
            {filtered.map((module) => (
              <Pressable
                key={module.id}
                onPress={() => setSelected(module)}
                style={({ pressed }) => [
                  styles.moduleCard,
                  { backgroundColor: module.color, borderColor: module.borderColor },
                  pressed && styles.pressed,
                ]}
                accessibilityRole="button"
                accessibilityLabel={`${module.title}, duration ${module.duration}`}
              >
                <View style={styles.cardIcon}>
                  <Text style={styles.cardEmoji}>{module.icon}</Text>
                </View>

                <Text style={styles.cardTitle}>{module.title}</Text>
                <Text style={styles.cardText}>{module.subtitle}</Text>

                <View style={styles.cardFooter}>
                  <View style={styles.durationBadge}>
                    <Ionicons name="time-outline" size={11} color={COLORS.navyMuted} />
                    <Text style={styles.durationText}>{module.duration}</Text>
                  </View>

                  <View style={styles.arrowCircle}>
                    <Ionicons name="arrow-forward" size={14} color={COLORS.coralDark} />
                  </View>
                </View>
              </Pressable>
            ))}
          </View>

          {/* TELE-MANAS & EMERGENCY SUPPORT CARD */}
          <View style={styles.supportCard}>
            <View style={styles.supportIconWrap}>
              <Ionicons name="heart" size={20} color={COLORS.coralDark} />
            </View>

            <Text style={styles.supportTitle}>Need more support?</Text>
            <Text style={styles.supportText}>
              Self-help can be useful, but it does not replace professional care. If you are struggling significantly or feel unsafe, reach out for qualified support.
            </Text>

            <Pressable
              onPress={() => Linking.openURL('https://www.dghs.mohfw.gov.in/national-mental-health-programme.php')}
              style={({ pressed }) => [
                styles.teleManasButton,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Contact Tele-MANAS helpline 14416"
            >
              <Ionicons name="call" size={15} color={COLORS.white} />
              <Text style={styles.teleManasText}>Tele-MANAS · 14416</Text>
            </Pressable>
          </View>

          {/* DISCLAIMER */}
          <Text style={styles.disclaimer}>
            MEDHA self-help content is educational and should not be used to diagnose a mental health condition or replace professional medical care.
          </Text>
        </ScrollView>
      </SafeAreaView>
    </MedhaBackground>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
  },
  content: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 40,
  },
  guideContent: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 45,
  },

  iconButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.95)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
    ...SHADOW.card,
  },

  header: {
    marginBottom: 18,
  },
  eyebrow: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1.5,
    color: COLORS.coralDark,
    textTransform: 'uppercase',
  },
  heroTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 28,
    lineHeight: 34,
    color: COLORS.navy,
    marginTop: 6,
  },
  heroText: {
    fontFamily: 'Nunito-Regular',
    fontSize: 13,
    lineHeight: 19,
    color: COLORS.navyMuted,
    marginTop: 8,
    maxWidth: 320,
  },

  /* FILTERS */
  filters: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 10,
    marginBottom: 20,
  },
  filterChip: {
    paddingHorizontal: 16,
    paddingVertical: 9,
    borderRadius: RADIUS.pill,
    backgroundColor: 'rgba(255, 255, 255, 0.8)',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.95)',
    ...SHADOW.card,
  },
  filterChipActive: {
    backgroundColor: COLORS.charcoal,
    borderColor: COLORS.charcoal,
  },
  filterText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 12,
    color: COLORS.navyMuted,
  },
  filterTextActive: {
    color: COLORS.white,
    fontFamily: 'Fredoka-Medium',
  },

  sectionTitle: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 18,
    color: COLORS.navy,
    marginBottom: 14,
  },

  /* MODULE GRID */
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  moduleCard: {
    width: '48%',
    minHeight: 200,
    borderRadius: RADIUS.card,
    borderWidth: 1.5,
    padding: 16,
    ...SHADOW.card,
  },
  cardIcon: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: 'rgba(255, 255, 255, 0.7)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  cardEmoji: {
    fontSize: 20,
  },
  cardTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 16,
    lineHeight: 20,
    color: COLORS.navy,
  },
  cardText: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    lineHeight: 16,
    color: COLORS.navyMuted,
    marginTop: 6,
  },
  cardFooter: {
    marginTop: 'auto',
    paddingTop: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  durationBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.65)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  durationText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 10,
    color: COLORS.navyMuted,
  },
  arrowCircle: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: COLORS.white,
    alignItems: 'center',
    justifyContent: 'center',
    ...SHADOW.card,
  },

  /* SUPPORT / TELE-MANAS CARD */
  supportCard: {
    marginTop: 30,
    padding: 20,
    borderRadius: RADIUS.card + 4,
    backgroundColor: COLORS.creamSecondary,
    borderWidth: 1.5,
    borderColor: COLORS.peach,
    ...SHADOW.soft,
  },
  supportIconWrap: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255, 122, 89, 0.15)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 10,
  },
  supportTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 19,
    color: COLORS.navy,
  },
  supportText: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    lineHeight: 18,
    color: COLORS.navyMuted,
    marginTop: 6,
  },
  teleManasButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    alignSelf: 'flex-start',
    marginTop: 14,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: RADIUS.pill,
    backgroundColor: COLORS.coral,
    ...SHADOW.glow,
  },
  teleManasText: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 13,
    color: COLORS.white,
  },

  disclaimer: {
    fontFamily: 'Nunito-Regular',
    fontSize: 10,
    lineHeight: 15,
    textAlign: 'center',
    color: COLORS.subtleText,
    marginTop: 22,
    paddingHorizontal: 10,
  },

  /* GUIDE VIEW */
  guideTopBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  guideTypeBadge: {
    backgroundColor: COLORS.creamSecondary,
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: RADIUS.pill,
    borderWidth: 1,
    borderColor: COLORS.peach,
  },
  guideType: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1.2,
    color: COLORS.coralDark,
  },
  guideTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 26,
    lineHeight: 32,
    color: COLORS.navy,
    marginTop: 6,
  },
  progressTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 16,
  },
  progressLabel: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1.1,
    color: COLORS.navyMuted,
  },
  track: {
    height: 6,
    borderRadius: 3,
    backgroundColor: 'rgba(0, 0, 0, 0.08)',
    overflow: 'hidden',
    marginTop: 8,
  },
  fill: {
    height: '100%',
    borderRadius: 3,
    backgroundColor: COLORS.coral,
  },

  illustrationBanner: {
    height: 180,
    borderRadius: RADIUS.card + 4,
    borderWidth: 1.5,
    marginTop: 20,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
    ...SHADOW.card,
  },
  softCircle: {
    position: 'absolute',
    width: 220,
    height: 220,
    borderRadius: 110,
    backgroundColor: 'rgba(255, 255, 255, 0.4)',
  },
  bigEmoji: {
    fontSize: 54,
  },
  stepBadge: {
    position: 'absolute',
    top: 14,
    left: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.75)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 10,
  },
  stepBadgeText: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 11,
    color: COLORS.navy,
  },

  stepTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 22,
    lineHeight: 28,
    color: COLORS.navy,
    marginTop: 22,
  },
  stepBody: {
    fontFamily: 'Nunito-Regular',
    fontSize: 14,
    lineHeight: 22,
    color: COLORS.navyMuted,
    marginTop: 8,
  },
  tipCard: {
    marginTop: 16,
    padding: 14,
    borderRadius: RADIUS.medium,
    backgroundColor: COLORS.yellowSoft,
    borderWidth: 1.5,
    borderColor: COLORS.yellow,
    ...SHADOW.card,
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
    fontFamily: 'Nunito-SemiBold',
    fontSize: 12,
    lineHeight: 17,
    color: COLORS.navy,
  },
  dots: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 6,
    marginTop: 24,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: COLORS.peach2,
  },
  activeDot: {
    width: 18,
    borderRadius: 4,
    backgroundColor: COLORS.coral,
  },
  navRow: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 20,
  },
  swipeNote: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    textAlign: 'center',
    color: COLORS.navyMuted,
    marginTop: 12,
  },

  /* SOURCES */
  sources: {
    marginTop: 30,
    paddingTop: 18,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  sourcesTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 17,
    color: COLORS.navy,
  },
  sourcesSub: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    color: COLORS.navyMuted,
    marginTop: 2,
    marginBottom: 10,
  },
  sourceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.borderLight,
    gap: 10,
  },
  sourceIcon: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: COLORS.creamSecondary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sourceOrg: {
    fontFamily: 'Nunito-Bold',
    fontSize: 9,
    letterSpacing: 0.8,
    color: COLORS.coralDark,
  },
  sourceTitle: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    color: COLORS.navy,
    marginTop: 1,
  },

  pressed: {
    transform: [{ scale: 0.97 }],
    opacity: 0.88,
  },
});
