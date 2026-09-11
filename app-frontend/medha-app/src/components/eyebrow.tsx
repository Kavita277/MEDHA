import { StyleSheet, Text } from 'react-native';

import { COLORS } from '../constants/colors';

interface EyebrowProps {
  children: string;
}

export function Eyebrow({ children }: EyebrowProps) {
  return (
    <Text style={styles.text}>
      {children.toUpperCase()}
    </Text>
  );
}

const styles = StyleSheet.create({
  text: {
    fontFamily: 'Inter-Medium',
    fontSize: 9,
    letterSpacing: 2,
    color: COLORS.forest,
  },
});