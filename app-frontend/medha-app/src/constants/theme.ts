import { COLORS } from './colors';

export const SPACING = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 28,
  xxxl: 36,
  huge: 48,
};

export const RADIUS = {
  small: 10,
  medium: 16,
  large: 22,
  pill: 999,
};

export const SHADOW = {
  soft: {
    shadowColor: '#283A31',
    shadowOffset: {
      width: 0,
      height: 8,
    },
    shadowOpacity: 0.08,
    shadowRadius: 20,
    elevation: 4,
  },
};

export const THEME = {
  colors: COLORS,
  spacing: SPACING,
  radius: RADIUS,
  shadow: SHADOW,
};