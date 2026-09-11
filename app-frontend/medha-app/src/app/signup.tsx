import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import {
    Pressable,
    ScrollView,
    StyleSheet,
    Text,
    TextInput,
    View,
} from 'react-native';

import { COLORS } from '../constants/colors';

export default function SignupScreen() {
  return (
    <View style={styles.container}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
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
          Create your account
        </Text>

        <Text style={styles.subtitle}>
          Your journey to a calmer you begins here.
        </Text>

        {/* SOCIAL LOGIN */}

        <Pressable style={styles.socialButton}>
          <Text style={styles.google}>G</Text>
          <Text style={styles.socialText}>
            Continue with Google
          </Text>
        </Pressable>

        <Pressable style={styles.socialButton}>
          <Text style={styles.apple}>●</Text>
          <Text style={styles.socialText}>
            Continue with Apple
          </Text>
        </Pressable>

        <View style={styles.orRow}>
          <View style={styles.orLine} />
          <Text style={styles.orText}>or</Text>
          <View style={styles.orLine} />
        </View>

        {/* FORM */}

        <TextInput
          placeholder="Name"
          placeholderTextColor="#8A8A82"
          style={styles.input}
        />

        <TextInput
          placeholder="Mobile Number"
          placeholderTextColor="#8A8A82"
          keyboardType="phone-pad"
          style={styles.input}
        />

        <View style={styles.passwordContainer}>
          <TextInput
            placeholder="Password"
            placeholderTextColor="#8A8A82"
            secureTextEntry
            style={styles.passwordInput}
          />

          <Ionicons
            name="eye-outline"
            size={18}
            color="#777970"
          />
        </View>

        <Pressable
          onPress={() => router.replace('/personalize')}
          style={({ pressed }) => [
            styles.createButton,
            pressed && styles.pressed,
          ]}
        >
          <Text style={styles.createText}>
            Create Account
          </Text>
        </Pressable>

        <Text style={styles.terms}>
          By creating an account, you agree to our{'\n'}
          <Text style={styles.termsBold}>
            Terms & Privacy Policy.
          </Text>
        </Text>
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
    paddingHorizontal: 23,
    paddingTop: 55,
    paddingBottom: 35,
  },

  back: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 28,
  },

  title: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 37,
    lineHeight: 40,
    color: COLORS.deepForest,
  },

  subtitle: {
    fontFamily: 'Inter-Regular',
    fontSize: 13,
    lineHeight: 20,
    color: COLORS.mutedText,
    marginTop: 8,
    marginBottom: 27,
  },

  socialButton: {
    height: 47,
    borderRadius: 13,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 10,
  },

  google: {
    fontSize: 18,
    fontWeight: '600',
    marginRight: 10,
  },

  apple: {
    fontSize: 15,
    marginRight: 10,
    color: COLORS.text,
  },

  socialText: {
    fontFamily: 'Inter-Medium',
    fontSize: 12,
    color: COLORS.text,
  },

  orRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 20,
  },

  orLine: {
    flex: 1,
    height: 1,
    backgroundColor: COLORS.border,
  },

  orText: {
    fontFamily: 'Inter-Regular',
    fontSize: 11,
    color: COLORS.mutedText,
    marginHorizontal: 12,
  },

  input: {
    height: 48,
    borderRadius: 13,
    borderWidth: 1,
    borderColor: COLORS.border,
    backgroundColor: COLORS.surface,
    paddingHorizontal: 16,
    fontFamily: 'Inter-Regular',
    fontSize: 12,
    color: COLORS.text,
    marginBottom: 10,
  },

  passwordContainer: {
    height: 48,
    borderRadius: 13,
    borderWidth: 1,
    borderColor: COLORS.border,
    backgroundColor: COLORS.surface,
    flexDirection: 'row',
    alignItems: 'center',
    paddingRight: 15,
    marginBottom: 17,
  },

  passwordInput: {
    flex: 1,
    paddingHorizontal: 16,
    fontFamily: 'Inter-Regular',
    fontSize: 12,
    color: COLORS.text,
  },

  createButton: {
    height: 49,
    borderRadius: 25,
    backgroundColor: COLORS.forest,
    alignItems: 'center',
    justifyContent: 'center',
  },

  createText: {
    fontFamily: 'Inter-Medium',
    color: COLORS.white,
    fontSize: 13,
  },

  pressed: {
    opacity: 0.75,
    transform: [{ scale: 0.98 }],
  },

  terms: {
    textAlign: 'center',
    color: COLORS.mutedText,
    fontFamily: 'Inter-Regular',
    fontSize: 9,
    lineHeight: 14,
    marginTop: 17,
  },

  termsBold: {
    color: COLORS.text,
  },
});