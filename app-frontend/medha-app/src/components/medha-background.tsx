import React from 'react';
import { StyleSheet, View, ViewStyle } from 'react-native';
import Svg, { Circle, Defs, Ellipse, LinearGradient, Path, Stop } from 'react-native-svg';
import { COLORS } from '../constants/colors';

interface MedhaBackgroundProps {
  variant?: 'home' | 'calm' | 'warm' | 'minimal';
  style?: ViewStyle;
  children?: React.ReactNode;
}

export function MedhaBackground({
  variant = 'home',
  style,
  children,
}: MedhaBackgroundProps) {
  return (
    <View style={[styles.container, style]}>
      {/* Decorative SVG Shapes sitting behind content */}
      <View style={StyleSheet.absoluteFill} pointerEvents="none">
        <Svg
          width="100%"
          height="100%"
          viewBox="0 0 400 850"
          preserveAspectRatio="xMidYMid slice"
        >
          <Defs>
            <LinearGradient id="sunGlow" x1="0" y1="0" x2="1" y2="1">
              <Stop offset="0" stopColor={COLORS.yellow} stopOpacity="0.85" />
              <Stop offset="1" stopColor={COLORS.yellowSoft} stopOpacity="0.3" />
            </LinearGradient>
            <LinearGradient id="bottomBlob" x1="0" y1="0" x2="1" y2="1">
              <Stop offset="0" stopColor={COLORS.green} stopOpacity="0.55" />
              <Stop offset="1" stopColor={COLORS.greenSoft} stopOpacity="0.2" />
            </LinearGradient>
            <LinearGradient id="peachGlow" x1="0" y1="0" x2="1" y2="1">
              <Stop offset="0" stopColor={COLORS.peach} stopOpacity="0.6" />
              <Stop offset="1" stopColor={COLORS.creamSecondary} stopOpacity="0.1" />
            </LinearGradient>
          </Defs>

          {variant === 'home' && (
            <>
              {/* Soft sun / warm light at top right */}
              <Circle
                cx="330"
                cy="90"
                r="110"
                fill="url(#sunGlow)"
              />
              <Circle
                cx="330"
                cy="90"
                r="110"
                fill="none"
                stroke={COLORS.yellowDark}
                strokeWidth="1.5"
                opacity={0.3}
              />

              {/* Gentle floating organic circles */}
              <Circle cx="45" cy="180" r="18" fill={COLORS.pink} opacity={0.45} />
              <Circle cx="370" cy="380" r="12" fill={COLORS.lavender} opacity={0.6} />
              <Circle cx="25" cy="520" r="8" fill={COLORS.blue} opacity={0.5} />
              <Circle cx="355" cy="240" r="5" fill={COLORS.coral} opacity={0.3} />

              {/* Soft curved wave near middle */}
              <Path
                d="M-40 480 Q100 450 220 500 T440 470"
                stroke={COLORS.peach}
                strokeWidth="24"
                fill="none"
                strokeLinecap="round"
                opacity={0.25}
              />

              {/* Large calming green organic hill at bottom left */}
              <Ellipse
                cx="40"
                cy="780"
                rx="180"
                ry="150"
                fill="url(#bottomBlob)"
              />
              <Circle
                cx="360"
                cy="790"
                r="90"
                fill={COLORS.blueSoft}
                opacity={0.5}
              />
            </>
          )}

          {variant === 'calm' && (
            <>
              <Ellipse cx="200" cy="120" rx="220" ry="160" fill={COLORS.blueSoft} opacity={0.7} />
              <Circle cx="340" cy="80" r="50" fill="url(#sunGlow)" />
              <Ellipse cx="80" cy="740" rx="200" ry="160" fill={COLORS.sageSoft} opacity={0.5} />
            </>
          )}

          {variant === 'warm' && (
            <>
              <Circle cx="310" cy="110" r="120" fill="url(#peachGlow)" />
              <Circle cx="60" cy="720" r="140" fill={COLORS.yellowSoft} opacity={0.6} />
            </>
          )}
        </Svg>
      </View>

      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.cream,
  },
});
