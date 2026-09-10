import { StyleSheet, Text, View } from 'react-native';

import { COLORS } from '../constants/colors';

interface MedhaLogoProps {
  light?: boolean;
}

export function MedhaLogo({
  light = false,
}: MedhaLogoProps) {
  return (
    <View style={styles.container}>
      <Text
        style={[
          styles.logo,
          light && styles.lightLogo,
        ]}
      >
        MEDHA
      </Text>

      <Text
        style={[
          styles.tagline,
          light && styles.lightTagline,
        ]}
      >
        MIND  ·  BALANCE  ·  CLARITY
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
  },

  logo: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 29,
    letterSpacing: 7,
    color: COLORS.deepForest,
  },

  tagline: {
    fontFamily: 'Inter-Regular',
    fontSize: 6,
    letterSpacing: 1.7,
    color: COLORS.mutedText,
    marginTop: 3,
  },

  lightLogo: {
    color: COLORS.white,
  },

  lightTagline: {
    color: 'rgba(255,255,255,0.75)',
  },
});