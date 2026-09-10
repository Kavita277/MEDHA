import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useState } from 'react';
import {
    ImageBackground,
    Pressable,
    ScrollView,
    StyleSheet,
    Text,
    View,
} from 'react-native';

import { COLORS } from '../constants/colors';

const options = [
  {
    title: 'Nature',
    image:
      'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?q=85&w=600&auto=format&fit=crop',
  },
  {
    title: 'Music',
    image:
      'https://images.unsplash.com/photo-1511379938547-c1f69419868d?q=85&w=600&auto=format&fit=crop',
  },
  {
    title: 'Warm Spaces',
    image:
      'https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?q=85&w=600&auto=format&fit=crop',
  },
  {
    title: 'Minimal',
    image:
      'https://images.unsplash.com/photo-1494438639946-1ebd1d20bf85?q=85&w=600&auto=format&fit=crop',
  },
  {
    title: 'Animals',
    image:
      'https://images.unsplash.com/photo-1552053831-71594a27632d?q=85&w=600&auto=format&fit=crop',
  },
  {
    title: 'Art',
    image:
      'https://images.unsplash.com/photo-1549490349-8643362247b5?q=85&w=600&auto=format&fit=crop',
  },
];

export default function PersonalizeScreen() {
  const [selected, setSelected] = useState<string[]>([]);

  function toggle(title: string) {
    setSelected((current) =>
      current.includes(title)
        ? current.filter((item) => item !== title)
        : [...current, title]
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.content}
      >
        <Pressable
          onPress={() => router.back()}
          style={styles.back}
        >
          <Ionicons
            name="arrow-back"
            size={19}
            color={COLORS.deepForest}
          />
        </Pressable>

        <Text style={styles.title}>
          What soothes you{'\n'}the most?
        </Text>

        <Text style={styles.subtitle}>
          Select a few to personalise your space.
        </Text>

        <View style={styles.grid}>
          {options.map((option) => {
            const active = selected.includes(option.title);

            return (
              <Pressable
                key={option.title}
                onPress={() => toggle(option.title)}
                style={[
                  styles.card,
                  active && styles.cardActive,
                ]}
              >
                <ImageBackground
                  source={{ uri: option.image }}
                  style={styles.image}
                  imageStyle={styles.imageRadius}
                >
                  <View style={styles.overlay} />

                  <View style={styles.cardBottom}>
                    <Text style={styles.cardTitle}>
                      {option.title}
                    </Text>
                  </View>

                  {active && (
                    <View style={styles.check}>
                      <Ionicons
                        name="checkmark"
                        size={15}
                        color="#FFFFFF"
                      />
                    </View>
                  )}
                </ImageBackground>
              </Pressable>
            );
          })}
        </View>

        <Pressable
          onPress={() => router.replace('/home')}
          style={styles.button}
        >
          <Text style={styles.buttonText}>
            Continue
          </Text>
        </Pressable>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },

  content: {
    paddingHorizontal: 22,
    paddingTop: 55,
    paddingBottom: 35,
  },

  back: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    marginBottom: 25,
  },

  title: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 37,
    lineHeight: 38,
    color: COLORS.deepForest,
  },

  subtitle: {
    fontFamily: 'Inter-Regular',
    fontSize: 13,
    color: COLORS.mutedText,
    marginTop: 9,
    marginBottom: 23,
  },

  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    rowGap: 12,
  },

  card: {
    width: '48.5%',
    height: 145,
    borderRadius: 19,
    overflow: 'hidden',
  },

  cardActive: {
    borderWidth: 2,
    borderColor: COLORS.forest,
  },

  image: {
    flex: 1,
  },

  imageRadius: {
    borderRadius: 18,
  },

  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(28,39,31,0.30)',
  },

  cardBottom: {
    position: 'absolute',
    left: 15,
    bottom: 14,
  },

  cardTitle: {
    color: '#FFFFFF',
    fontFamily: 'Inter-Medium',
    fontSize: 12,
  },

  check: {
    position: 'absolute',
    top: 10,
    right: 10,
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: COLORS.forest,
    alignItems: 'center',
    justifyContent: 'center',
  },

  button: {
    height: 50,
    borderRadius: 25,
    backgroundColor: COLORS.forest,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 25,
  },

  buttonText: {
    fontFamily: 'Inter-Medium',
    fontSize: 13,
    color: COLORS.white,
  },
});