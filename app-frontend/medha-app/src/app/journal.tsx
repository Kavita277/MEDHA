import React, { useState } from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { MedhaScreen } from '../components/medha-screen';
import { COLORS } from '../constants/colors';

export default function JournalScreen() {
  const router = useRouter();
  const [text, setText] = useState('');

  return (
    <MedhaScreen
      eyebrow="Journal"
      title="Leave something here."
      subtitle="A private space for thoughts that don't need an audience."
      onBack={() => router.back()}
      scroll={false}
    >
      <View style={styles.paper}>
        <Text style={styles.date}>TODAY · A QUIET PAGE</Text>

        <TextInput
          multiline
          value={text}
          onChangeText={setText}
          placeholder="What’s moving through your mind?"
          placeholderTextColor={COLORS.subtleText}
          style={styles.input}
          textAlignVertical="top"
        />

        <View style={styles.line} />

        <Text style={styles.prompt}>
          You could write about what happened, what you felt, or absolutely nothing in particular.
        </Text>
      </View>

      <Pressable
        onPress={() => router.push('/home')}
        style={styles.save}
      >
        <Text style={styles.saveText}>Close this page</Text>
      </Pressable>
    </MedhaScreen>
  );
}

const styles = StyleSheet.create({
  paper: {
    flex: 1,
    backgroundColor: COLORS.surface,
    borderRadius: 4,
    padding: 24,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: COLORS.border,
  },

  date: {
    fontFamily: 'Inter-Medium',
    fontSize: 9,
    letterSpacing: 1.7,
    color: COLORS.moss,
    marginBottom: 22,
  },

  input: {
    flex: 1,
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 22,
    lineHeight: 30,
    color: COLORS.deepForest,
  },

  line: {
    height: 1,
    backgroundColor: COLORS.border,
    marginTop: 20,
  },

  prompt: {
    fontFamily: 'Inter-Regular',
    fontSize: 10,
    lineHeight: 16,
    color: COLORS.subtleText,
    marginTop: 16,
  },

  save: {
    height: 52,
    borderRadius: 26,
    backgroundColor: COLORS.forest,
    alignItems: 'center',
    justifyContent: 'center',
  },

  saveText: {
    fontFamily: 'Inter-Medium',
    fontSize: 13,
    color: COLORS.white,
  },
});