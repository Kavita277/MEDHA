import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useMemo, useState } from 'react';
import { Alert, Linking, Pressable, SafeAreaView, ScrollView, StyleSheet, Text, View } from 'react-native';
import { COLORS } from '../constants/colors';

/*
  MEDHA Self Help
  Adapted from Abby's supplied self-help prototype.

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
  id: string; title: string; subtitle: string;
  category: 'condition' | 'population';
  type: string; duration: string; icon: string;
  color: string; sourceIds: string[]; steps: Step[];
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
    id: 'anxiety', title: 'Managing Anxiety', subtitle: 'Gentle steps for moments when worry feels overwhelming.',
    category: 'condition', type: 'Anxiety', duration: '5 min', icon: '◌', color: '#DCE8D1',
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
    id: 'panic', title: 'During a Panic Episode', subtitle: 'A simple guide for getting through an intense moment.',
    category: 'condition', type: 'Panic', duration: '4 min', icon: '○', color: '#E8DED5',
    sourceIds: ['nhs-panic'],
    steps: [
      { id: 'p1', title: 'Stay where you are if possible', body: 'If it is safe to do so, remain where you are and give yourself time for the intense feelings to settle.' },
      { id: 'p2', title: 'Breathe slowly', body: 'Try slow, gentle breathing. Avoid forcing very deep breaths. Let the breath become steady and comfortable.' },
      { id: 'p3', title: 'Remind yourself', body: 'A panic episode can feel frightening. Remind yourself that intense sensations can pass.' },
      { id: 'p4', title: 'Focus on something calming', body: 'Bring your attention toward something peaceful in your surroundings or another safe, calming image.' },
    ],
  },
  {
    id: 'low-mood', title: 'Taking the First Small Step', subtitle: 'Gentle activity planning when everything feels difficult.',
    category: 'condition', type: 'Low mood', duration: '7 min', icon: '☀', color: '#EEE5C9',
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
    id: 'stress', title: 'When Stress Feels Too Much', subtitle: 'Ground yourself and return to what matters.',
    category: 'condition', type: 'Stress', duration: '5 min', icon: '♡', color: '#DCE7D6',
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
    id: 'adolescents', title: 'For Adolescents', subtitle: 'Tools for emotions, stress, friendships and confidence.',
    category: 'population', type: 'Adolescents', duration: '6 min', icon: '✦', color: '#E7DDD2',
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
    id: 'older-adults', title: 'For Older Adults', subtitle: 'Small routines for connection, movement and wellbeing.',
    category: 'population', type: 'Older adults', duration: '5 min', icon: '○', color: '#DDE5D3',
    sourceIds: ['nia'],
    steps: [
      { id: 'oa1', title: 'Start gently', body: 'Choose an activity appropriate for your abilities and current health. Even small amounts of movement can be a starting point.' },
      { id: 'oa2', title: 'Stay connected', body: 'Think of one person you would enjoy speaking with or one community activity that feels comfortable.' },
      { id: 'oa3', title: 'Do something meaningful', body: 'Gardening, walking, reading, music, helping others or another enjoyable activity can give structure and purpose to the day.' },
      { id: 'oa4', title: 'Keep a simple routine', body: 'Regular sleep, meals, movement and social contact can help create structure.' },
    ],
  },
  {
    id: 'caregivers', title: 'For Caregivers', subtitle: 'Protecting your own wellbeing while supporting someone else.',
    category: 'population', type: 'Caregivers', duration: '6 min', icon: '♡', color: '#E8DDD4',
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

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.guide}>
        <Pressable onPress={onBack} style={styles.back}><Ionicons name="arrow-back" size={19} color={COLORS.deepForest} /></Pressable>
        <Text style={styles.guideType}>{module.type.toUpperCase()}</Text>
        <Text style={styles.guideTitle}>{module.title}</Text>
        <View style={styles.progressTop}>
          <Text style={styles.progressLabel}>STEP {step + 1} OF {module.steps.length}</Text>
          <Text style={styles.progressLabel}>{Math.round(((step + 1) / module.steps.length) * 100)}%</Text>
        </View>
        <View style={styles.track}><View style={[styles.fill, { width: `${((step + 1) / module.steps.length) * 100}%` }]} /></View>

        <View style={[styles.illustration, { backgroundColor: module.color }]}>
          <View style={styles.softCircle} />
          <Text style={styles.bigIcon}>{module.icon}</Text>
          <Text style={styles.stepNumber}>{step + 1}</Text>
        </View>

        <Text style={styles.stepTitle}>{current.title}</Text>
        <Text style={styles.stepBody}>{current.body}</Text>
        {current.tip && <View style={styles.tip}><Text style={styles.tipLabel}>GENTLE TIP</Text><Text style={styles.tipText}>{current.tip}</Text></View>}

        <View style={styles.dots}>
          {module.steps.map((item, index) => <View key={item.id} style={[styles.dot, index === step && styles.activeDot]} />)}
        </View>

        <View style={styles.nav}>
          <Pressable disabled={step === 0} onPress={() => setStep((value) => value - 1)} style={[styles.secondary, step === 0 && { opacity: 0.35 }]}>
            <Text style={styles.secondaryText}>Back</Text>
          </Pressable>
          <Pressable onPress={() => step === module.steps.length - 1 ? Alert.alert('Nice work', 'Small steps count.', [{ text: 'Done', onPress: onBack }]) : setStep((value) => value + 1)} style={styles.primary}>
            <Text style={styles.primaryText}>{step === module.steps.length - 1 ? 'Complete' : 'Next step'}</Text>
          </Pressable>
        </View>

        <Text style={styles.swipeNote}>Move through the guide at your own pace.</Text>

        <View style={styles.sources}>
          <Text style={styles.sourcesTitle}>Evidence & sources</Text>
          {module.sourceIds.map((id) => {
            const source = SOURCES.find((item) => item.id === id);
            if (!source) return null;
            return (
              <Pressable key={source.id} style={styles.sourceRow} onPress={() => Linking.openURL(source.url)}>
<<<<<<< HEAD
                <View style={styles.sourceIcon}><Ionicons name="arrow-up-right" size={14} color={COLORS.forest} /></View>
=======
                <View style={styles.sourceIcon}><Ionicons name="open-outline" size={14} color={COLORS.forest} /></View>
>>>>>>> 40e4450e4d451d2bd31862d1ee53d8149e4a204c
                <View style={{ flex: 1 }}><Text style={styles.sourceOrg}>{source.org}</Text><Text style={styles.sourceTitle}>{source.title}</Text></View>
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
  const [filter, setFilter] = useState<'all' | 'condition' | 'population'>('all');
  const [selected, setSelected] = useState<Module | null>(null);
  const filtered = useMemo(() => filter === 'all' ? MODULES : MODULES.filter((item) => item.category === filter), [filter]);

  if (selected) return <Guide module={selected} onBack={() => setSelected(null)} />;

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
        <Pressable onPress={() => router.back()} style={styles.back}><Ionicons name="arrow-back" size={19} color={COLORS.deepForest} /></Pressable>
        <Text style={styles.eyebrow}>YOUR WELLBEING</Text>
        <Text style={styles.heroTitle}>
        {'Small steps.\nA calmer moment.'}
         </Text>
        <Text style={styles.heroText}>Explore simple, evidence-informed guides for difficult moments and everyday wellbeing.</Text>

        <View style={styles.filters}>
          {[
            { id: 'all' as const, label: 'All' },
            { id: 'condition' as const, label: 'Conditions' },
            { id: 'population' as const, label: 'For You' },
          ].map((item) => (
            <Pressable key={item.id} onPress={() => setFilter(item.id)} style={[styles.filter, filter === item.id && styles.filterActive]}>
              <Text style={[styles.filterText, filter === item.id && styles.filterTextActive]}>{item.label}</Text>
            </Pressable>
          ))}
        </View>

        <Text style={styles.sectionTitle}>Guides for difficult moments</Text>
        <View style={styles.grid}>
          {filtered.map((module) => (
            <Pressable key={module.id} onPress={() => setSelected(module)} style={[styles.card, { backgroundColor: module.color }]}>
              <View style={styles.cardIcon}><Text style={styles.cardIconText}>{module.icon}</Text></View>
              <Text style={styles.cardTitle}>{module.title}</Text>
              <Text style={styles.cardText}>{module.subtitle}</Text>
              <View style={styles.cardFooter}><Text style={styles.duration}>{module.duration}</Text><View style={styles.arrow}><Ionicons name="arrow-forward" size={15} color={COLORS.forest} /></View></View>
            </Pressable>
          ))}
        </View>

        <View style={styles.support}>
          <Text style={styles.supportTitle}>Need more support?</Text>
          <Text style={styles.supportText}>Self-help can be useful, but it does not replace professional care. If you are struggling significantly or feel unsafe, reach out for professional or emergency support.</Text>
          <Pressable onPress={() => Linking.openURL('https://www.dghs.mohfw.gov.in/national-mental-health-programme.php')} style={styles.supportButton}>
            <Text style={styles.supportButtonText}>Tele-MANAS · 14416</Text>
          </Pressable>
        </View>

        <Text style={styles.disclaimer}>MEDHA self-help content is educational and should not be used to diagnose a mental health condition or replace professional medical care.</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#F8F5EC' },
  content: { padding: 22, paddingTop: 50, paddingBottom: 42 },
  guide: { padding: 22, paddingTop: 50, paddingBottom: 45 },
  back: { width: 40, height: 40, justifyContent: 'center', marginBottom: 12 },
  eyebrow: { fontFamily: 'Inter-Medium', fontSize: 8, letterSpacing: 1.8, color: COLORS.forest, marginTop: 5 },
  heroTitle: { fontFamily: 'CormorantGaramond-Regular', fontSize: 38, lineHeight: 39, color: COLORS.deepForest, marginTop: 10 },
  heroText: { fontFamily: 'Inter-Regular', fontSize: 11, lineHeight: 17, color: COLORS.mutedText, marginTop: 11, maxWidth: 330 },
  filters: { flexDirection: 'row', gap: 8, marginTop: 22 },
  filter: { paddingHorizontal: 16, paddingVertical: 9, borderRadius: 18, backgroundColor: COLORS.surfaceWarm },
  filterActive: { backgroundColor: COLORS.forest },
  filterText: { fontFamily: 'Inter-Medium', fontSize: 10, color: COLORS.mutedText },
  filterTextActive: { color: COLORS.white },
  sectionTitle: { fontFamily: 'CormorantGaramond-Regular', fontSize: 25, color: COLORS.deepForest, marginTop: 30, marginBottom: 13 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', gap: 10 },
  card: { width: '48.2%', minHeight: 205, borderRadius: 23, padding: 17 },
  cardIcon: { width: 48, height: 48, borderRadius: 24, backgroundColor: 'rgba(255,255,255,0.52)', alignItems: 'center', justifyContent: 'center', marginBottom: 15 },
  cardIconText: { fontSize: 22, color: COLORS.forest },
  cardTitle: { fontFamily: 'CormorantGaramond-Regular', fontSize: 21, lineHeight: 23, color: COLORS.deepForest },
  cardText: { fontFamily: 'Inter-Regular', fontSize: 9, lineHeight: 14, color: '#667064', marginTop: 6 },
  cardFooter: { marginTop: 'auto', paddingTop: 13, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  duration: { fontFamily: 'Inter-Regular', fontSize: 9, color: COLORS.mutedText },
  arrow: { width: 29, height: 29, borderRadius: 15, backgroundColor: COLORS.surface, alignItems: 'center', justifyContent: 'center' },
  support: { marginTop: 28, padding: 20, borderRadius: 23, backgroundColor: '#EADFD7' },
  supportTitle: { fontFamily: 'CormorantGaramond-Regular', fontSize: 23, color: '#3D342F' },
  supportText: { fontFamily: 'Inter-Regular', fontSize: 10, lineHeight: 16, color: '#665B55', marginTop: 5 },
  supportButton: { alignSelf: 'flex-start', marginTop: 14, paddingHorizontal: 15, paddingVertical: 10, borderRadius: 18, backgroundColor: COLORS.forest },
  supportButtonText: { fontFamily: 'Inter-Medium', fontSize: 10, color: COLORS.white },
  disclaimer: { fontFamily: 'Inter-Regular', fontSize: 8, lineHeight: 13, textAlign: 'center', color: COLORS.subtleText, marginTop: 20 },
  guideType: { fontFamily: 'Inter-Medium', fontSize: 8, letterSpacing: 1.6, color: COLORS.moss },
  guideTitle: { fontFamily: 'CormorantGaramond-Regular', fontSize: 32, lineHeight: 34, color: COLORS.deepForest, marginTop: 6 },
  progressTop: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 22 },
  progressLabel: { fontFamily: 'Inter-Medium', fontSize: 8, letterSpacing: 1.1, color: COLORS.mutedText },
  track: { height: 5, borderRadius: 3, backgroundColor: COLORS.stone, overflow: 'hidden', marginTop: 8 },
  fill: { height: '100%', borderRadius: 3, backgroundColor: COLORS.forest },
  illustration: { height: 230, borderRadius: 28, marginTop: 22, alignItems: 'center', justifyContent: 'center', overflow: 'hidden' },
  softCircle: { position: 'absolute', width: 210, height: 210, borderRadius: 105, backgroundColor: 'rgba(255,255,255,0.36)' },
  bigIcon: { fontSize: 60, color: COLORS.forest },
  stepNumber: { position: 'absolute', top: 18, left: 19, fontFamily: 'Inter-Medium', fontSize: 10, color: COLORS.mutedText },
  stepTitle: { fontFamily: 'CormorantGaramond-Regular', fontSize: 28, lineHeight: 32, color: COLORS.deepForest, marginTop: 24 },
  stepBody: { fontFamily: 'Inter-Regular', fontSize: 12, lineHeight: 19, color: COLORS.mutedText, marginTop: 8 },
  tip: { marginTop: 14, padding: 14, borderRadius: 17, backgroundColor: COLORS.mist },
  tipLabel: { fontFamily: 'Inter-Medium', fontSize: 8, letterSpacing: 1.3, color: COLORS.forest },
  tipText: { fontFamily: 'Inter-Regular', fontSize: 10, lineHeight: 15, color: COLORS.mutedText, marginTop: 4 },
  dots: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 5, marginTop: 20 },
  dot: { width: 6, height: 6, borderRadius: 3, backgroundColor: COLORS.stone },
  activeDot: { width: 18, backgroundColor: COLORS.forest },
  nav: { flexDirection: 'row', gap: 9, marginTop: 16 },
  secondary: { flex: 1, height: 51, borderRadius: 26, backgroundColor: COLORS.surfaceWarm, alignItems: 'center', justifyContent: 'center' },
  secondaryText: { fontFamily: 'Inter-Medium', fontSize: 11, color: COLORS.mutedText },
  primary: { flex: 2, height: 51, borderRadius: 26, backgroundColor: COLORS.forest, alignItems: 'center', justifyContent: 'center' },
  primaryText: { fontFamily: 'Inter-Medium', fontSize: 11, color: COLORS.white },
  swipeNote: { fontFamily: 'Inter-Regular', fontSize: 9, textAlign: 'center', color: COLORS.subtleText, marginTop: 10 },
  sources: { marginTop: 25 },
  sourcesTitle: { fontFamily: 'CormorantGaramond-Regular', fontSize: 21, color: COLORS.deepForest, marginBottom: 7 },
  sourceRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 9, borderBottomWidth: 1, borderBottomColor: COLORS.border, gap: 9 },
  sourceIcon: { width: 30, height: 30, borderRadius: 15, backgroundColor: COLORS.mist, alignItems: 'center', justifyContent: 'center' },
  sourceOrg: { fontFamily: 'Inter-Medium', fontSize: 8, letterSpacing: 0.7, color: COLORS.moss },
  sourceTitle: { fontFamily: 'Inter-Regular', fontSize: 10, color: COLORS.text, marginTop: 2 },
});
