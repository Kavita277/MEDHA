export const COLORS = {
  // MEDHA Redesign Palette (Visual Target)
  cream: '#FFF6EE',
  creamSecondary: '#FFEFE1',
  coral: '#FF7A59',
  coralDark: '#E8663F',
  peach: '#FFD9C4',
  peach2: '#FFC9AC',
  sage: '#7FA88A',
  sageSoft: '#DCEADD',
  blue: '#BFE3F5',
  blueDark: '#3E9CC9',
  blueSoft: '#E6F5FC',
  pink: '#FFD3E2',
  pinkDark: '#E8628E',
  pinkSoft: '#FFEEF4',
  green: '#D3ECD6',
  greenDark: '#4F9E68',
  greenSoft: '#EDF8EE',
  yellow: '#FFECB0',
  yellowDark: '#E8A93D',
  yellowSoft: '#FFF6E0',
  lavender: '#E3DCF7',
  lavenderDark: '#8A79D6',
  navy: '#181E2C',
  navyMuted: '#5B6478',
  navySoft: '#5B6478',
  charcoal: '#181E2C',
  obsidian: '#181E2C',
  midnightNavy: '#181E2C',
  porcelain: '#FAF9F6',
  canvas: '#FAF9F6',

  // Mood Calendar tokens
  moodYellow: '#FDE37E',
  moodCoral: '#FF8771',
  moodBlue: '#97CFF7',
  moodGreen: '#85D79B',
  moodPurple: '#B7A2F7',
  moodPeach: '#FFB088',
  moodNeutral: '#E8ECF2',

  // Atmospheric Grounding & Dark tokens
  twilightDark: '#0B0F19',
  twilightDeep: '#121726',
  twilightIndigo: '#1A2136',
  twilightPurple: '#222340',
  lotusGlow: '#FFA4B0',
  lotusPetal: '#FFB8C2',
  lotusCenter: '#FFEAA7',

  // Card & Border tokens
  cardBorder: 'rgba(0, 0, 0, 0.05)',
  cardBorderSubtle: 'rgba(0, 0, 0, 0.03)',

  // Glassmorphic tokens
  glass: 'rgba(255, 255, 255, 0.65)',
  glassBorder: 'rgba(255, 255, 255, 0.85)',
  glassOverlay: 'rgba(255, 255, 255, 0.40)',

  // Main environment & semantic mappings (updated for warm redesign)
  background: '#FAF9F6',
  surface: '#FFFFFF',
  surfaceWarm: '#FFEFE1',

  // Natural tones preserved for existing screens
  deepForest: '#28324A',
  forest: '#FF7A59',
  forestClassic: '#536B59',
  moss: '#78846D',
  lichen: '#A6AA91',
  stone: '#D4CDBD',
  sand: '#DDD4C3',
  wood: '#8A7058',
  clay: '#B7836D',

  // Atmospheric
  mist: '#DCE1D8',
  water: '#AABCB4',

  // Text
  text: '#28324A',
  mutedText: '#5B6478',
  subtleText: '#8E97A8',

  // Utility
  white: '#FFFFFF',
  black: '#171C19',
  border: 'rgba(255, 201, 172, 0.55)',
  borderLight: 'rgba(255, 255, 255, 0.75)',

  // Emotional states
  calm: '#BFE3F5',
  okay: '#D3ECD6',
  elevated: '#FFECB0',
  support: '#FFD3E2',
};

export type ColorName = keyof typeof COLORS;
