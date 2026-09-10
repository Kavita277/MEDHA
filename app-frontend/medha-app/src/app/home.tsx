import React from 'react';
import {
  ImageBackground,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../constants/colors';

const forestImage =
  'https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=1200&q=85';

export default function HomeScreen() {
  const router = useRouter();

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
              <Text style={styles.heroEyebrow}>
                A QUIET MOMENT
              </Text>

              <Text style={styles.heroTitle}>
                Take a breath.{'\n'}
                You're here.
              </Text>

              <Text style={styles.heroText}>
                Nothing needs to be solved all at once.
              </Text>
            </View>
          </ImageBackground>
        </View>


        {/* CHECK-IN */}

        <View style={styles.section}>
          <Text style={styles.sectionEyebrow}>
            ARRIVE
          </Text>

          <Text style={styles.sectionTitle}>
            How would you like to arrive?
          </Text>

          <View style={styles.arrivalRow}>

            <Pressable
              style={styles.arrival}
              onPress={() => router.push('/check-in')}
            >
              <View style={styles.arrivalIcon}>
                <Ionicons
                  name="sparkles-outline"
                  size={21}
                  color={COLORS.forest}
                />
              </View>

              <Text style={styles.arrivalTitle}>
                Check in
              </Text>

              <Text style={styles.arrivalText}>
                A few gentle questions
              </Text>
            </Pressable>


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

              <Text style={styles.arrivalTitle}>
                Speak
              </Text>

              <Text style={styles.arrivalText}>
                Say what you're feeling
              </Text>
            </Pressable>

          </View>
        </View>


        {/* CONTINUE EXPLORING */}

        <View style={styles.section}>
          <Text style={styles.sectionEyebrow}>
            YOUR SPACE
          </Text>

          <View style={styles.list}>

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
                  Start wherever your thoughts are.
                </Text>
              </View>

              <Ionicons
                name="arrow-forward"
                size={18}
                color={COLORS.mutedText}
              />
            </Pressable>


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
                  A few minutes of guided grounding.
                </Text>
              </View>

              <Ionicons
                name="arrow-forward"
                size={18}
                color={COLORS.mutedText}
              />
            </Pressable>


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
                  Write
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

          </View>
        </View>


        {/* INSIGHT */}

        <Pressable
          style={styles.insight}
          onPress={() => router.push('/insights')}
        >
          <View>
            <Text style={styles.insightEyebrow}>
              YOUR PATTERNS
            </Text>

            <Text style={styles.insightTitle}>
              See how you've been feeling.
            </Text>

            <Text style={styles.insightText}>
              Gentle reflections from your recent moments.
            </Text>
          </View>

          <View style={styles.insightArrow}>
            <Ionicons
              name="arrow-forward"
              size={18}
              color={COLORS.white}
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
    ...StyleSheet.absoluteFillObject,
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

  insight: {
    marginTop: 38,
    padding: 23,
    borderRadius: 25,
    backgroundColor: COLORS.deepForest,
    flexDirection: 'row',
    alignItems: 'center',
  },

  insightEyebrow: {
    fontFamily: 'Inter-Medium',
    fontSize: 8,
    letterSpacing: 1.8,
    color: COLORS.lichen,
    marginBottom: 9,
  },

  insightTitle: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 24,
    color: COLORS.white,
  },

  insightText: {
    fontFamily: 'Inter-Regular',
    fontSize: 10,
    color: COLORS.stone,
    marginTop: 6,
    maxWidth: 230,
    lineHeight: 15,
  },

  insightArrow: {
    marginLeft: 'auto',
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: 'rgba(255,255,255,0.12)',
    alignItems: 'center',
    justifyContent: 'center',
  },

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

});