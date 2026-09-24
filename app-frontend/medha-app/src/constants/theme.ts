import { COLORS } from './colors';

export const SPACING = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
  xxxl: 32,
  huge: 48,
};

export const RADIUS = {
  small: 12,
  medium: 18,
  large: 24,
  card: 22,
  modal: 32,
  pill: 999,
};

export const SHADOW = {
  soft: {
    shadowColor: COLORS.coralDark,
    shadowOffset: {
      width: 0,
      height: 8,
    },
    shadowOpacity: 0.10,
    shadowRadius: 18,
    elevation: 3,
  },
  card: {
    shadowColor: COLORS.navy,
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.06,
    shadowRadius: 14,
    elevation: 2,
  },
  glow: {
    shadowColor: COLORS.coral,
    shadowOffset: {
      width: 0,
      height: 10,
    },
    shadowOpacity: 0.22,
    shadowRadius: 20,
    elevation: 5,
  },
  fab: {
    shadowColor: '#000000',
    shadowOffset: {
      width: 0,
      height: 8,
    },
    shadowOpacity: 0.30,
    shadowRadius: 16,
    elevation: 6,
  },
};

export const THEME = {
  colors: COLORS,
  spacing: SPACING,
  radius: RADIUS,
  shadow: SHADOW,
};

// Aliases for compatibility
export const Colors = {
  light: COLORS,
  dark: COLORS,
  ...COLORS,
};
export const Spacing = SPACING;
export const MaxContentWidth = 800;
