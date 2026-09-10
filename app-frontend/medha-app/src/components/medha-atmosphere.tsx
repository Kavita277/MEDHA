import {
  ImageBackground,
  StyleSheet,
  View,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

interface MedhaAtmosphereProps {
  image?: string;
  children: React.ReactNode;
  overlay?: boolean;
}

export function MedhaAtmosphere({
  image,
  children,
  overlay = true,
}: MedhaAtmosphereProps) {
  if (!image) {
    return (
      <View style={styles.plain}>
        {children}
      </View>
    );
  }

  return (
    <ImageBackground
      source={{ uri: image }}
      style={styles.background}
      imageStyle={styles.image}
    >
      {overlay && (
        <LinearGradient
          colors={[
            'rgba(242,238,227,0.02)',
            'rgba(242,238,227,0.18)',
            'rgba(242,238,227,0.96)',
          ]}
          locations={[0, 0.45, 0.9]}
          style={StyleSheet.absoluteFill}
        />
      )}

      {children}
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  background: {
    flex: 1,
  },

  image: {
    resizeMode: 'cover',
  },

  plain: {
    flex: 1,
    backgroundColor: '#F2EEE3',
  },
});