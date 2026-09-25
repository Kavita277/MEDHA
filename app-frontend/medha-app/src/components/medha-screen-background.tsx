import React from 'react';
import { Image, StyleSheet, View } from 'react-native';

const BG_IMAGE = require('../../assets/images/medha-bg.png');

export function MedhaScreenBackground() {
  return (
    <View pointerEvents="none" style={styles.container} aria-hidden={true}>
      <Image
        source={BG_IMAGE}
        style={styles.bgImage}
        resizeMode="cover"
        accessibilityElementsHidden={true}
        importantForAccessibility="no-hide-descendants"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: -1,
  },
  bgImage: {
    width: '100%',
    height: '100%',
  },
});
