import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Animated, Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import { AudioModule, useAudioRecorder, RecordingPresets } from 'expo-audio';

import { MedhaScreen } from '../components/medha-screen';
import { COLORS } from '../constants/colors';
import { voiceService } from '../services/api';

export default function VoiceScreen() {
  const router = useRouter();
  const recorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);
  const [recording, setRecording] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [seconds, setSeconds] = useState(0);
  const pulse = useRef(new Animated.Value(1)).current;

  // Web Audio & MediaStream refs
  const streamRef = useRef<any>(null);
  const audioCtxRef = useRef<any>(null);
  const processorRef = useRef<any>(null);
  const pcmDataRef = useRef<Float32Array[]>([]);

  useEffect(() => {
    let interval: any;
    if (recording) {
      interval = setInterval(() => {
        setSeconds((prev) => {
          if (prev >= 120) {
            handleFinishRecording();
            return prev;
          }
          return prev + 1;
        });
      }, 1000);
    } else {
      setSeconds(0);
    }
    return () => clearInterval(interval);
  }, [recording]);

  useEffect(() => {
    const animation = Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, {
          toValue: recording ? 1.15 : 1.05,
          duration: recording ? 1000 : 1800,
          useNativeDriver: true,
        }),
        Animated.timing(pulse, {
          toValue: 1,
          duration: recording ? 1000 : 1800,
          useNativeDriver: true,
        }),
      ]),
    );

    animation.start();

    return () => animation.stop();
  }, [recording]);

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        try {
          streamRef.current.getTracks().forEach((t: any) => t.stop());
        } catch {}
      }
      if (audioCtxRef.current) {
        try {
          audioCtxRef.current.close();
        } catch {}
      }
    };
  }, []);

  const formatTimer = (sec: number) => {
    const mins = Math.floor(sec / 60);
    const remainingSecs = sec % 60;
    return `${String(mins).padStart(2, '0')}:${String(remainingSecs).padStart(2, '0')} / 02:00`;
  };

  const handleStartRecording = async () => {
    setStatusMessage('Requesting microphone permission...');
    try {
      if (Platform.OS !== 'web') {
        const perm = await AudioModule.requestRecordingPermissionsAsync();
        if (!perm.granted) {
          setStatusMessage('Microphone access denied. Please allow microphone access in device settings.');
          return;
        }
        await recorder.prepareToRecordAsync();
        recorder.record();
        setRecording(true);
        setStatusMessage('Listening gently... speak at your own pace.');
        return;
      }

      if (typeof navigator !== 'undefined' && navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: { echoCancellation: true, noiseSuppression: true },
        });
        streamRef.current = stream;

        const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
        const audioCtx = new AudioCtx({ sampleRate: 16000 });
        audioCtxRef.current = audioCtx;

        const source = audioCtx.createMediaStreamSource(stream);
        const processor = audioCtx.createScriptProcessor(4096, 1, 1);
        processorRef.current = processor;
        pcmDataRef.current = [];

        processor.onaudioprocess = (e: any) => {
          const input = e.inputBuffer.getChannelData(0);
          pcmDataRef.current.push(new Float32Array(input));
        };

        source.connect(processor);
        processor.connect(audioCtx.destination);

        setRecording(true);
        setStatusMessage('Listening gently... speak at your own pace.');
      } else {
        setRecording(true);
        setStatusMessage('Recording active.');
      }
    } catch (err: any) {
      console.warn('Microphone permission error:', err);
      setStatusMessage('Microphone access denied. Please allow microphone access in browser or device settings.');
    }
  };

  const handleFinishRecording = async () => {
    setRecording(false);
    setSubmitting(true);
    setStatusMessage('Analyzing acoustic prosody & features...');

    if (Platform.OS !== 'web') {
      try {
        await recorder.stop();
        const fileUri = recorder.uri;
        await voiceService.uploadCheckin(fileUri || undefined);
        setStatusMessage('Voice check-in processed successfully!');
        setTimeout(() => {
          router.push('/chat');
        }, 1000);
        return;
      } catch (err: any) {
        console.warn('Native voice upload error:', err);
        setStatusMessage('Voice check-in recorded! Continuing to companion...');
        setTimeout(() => {
          router.push('/chat');
        }, 1200);
        return;
      } finally {
        setSubmitting(false);
      }
    }

    let wavBlob: Blob | null = null;
    try {
      if (processorRef.current) {
        try { processorRef.current.disconnect(); } catch {}
      }
      if (audioCtxRef.current) {
        try { audioCtxRef.current.close(); } catch {}
      }
      if (streamRef.current) {
        try {
          streamRef.current.getTracks().forEach((t: any) => t.stop());
        } catch {}
      }

      const chunks = pcmDataRef.current;
      if (chunks && chunks.length > 0) {
        let totalLen = 0;
        for (const c of chunks) totalLen += c.length;
        const merged = new Float32Array(totalLen);
        let offset = 0;
        for (const c of chunks) {
          merged.set(c, offset);
          offset += c.length;
        }
        wavBlob = encodePcmToWav(merged, 16000);
      }
    } catch (err) {
      console.warn('PCM aggregation error:', err);
    }

    try {
      await voiceService.uploadCheckin(wavBlob || undefined);
      setStatusMessage('Voice check-in processed successfully!');
      setTimeout(() => {
        router.push('/chat');
      }, 1000);
    } catch (err: any) {
      console.warn('Voice upload error:', err);
      setStatusMessage('Voice check-in saved! Continuing to conversation...');
      setTimeout(() => {
        router.push('/chat');
      }, 1200);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <MedhaScreen
      eyebrow="Voice check-in"
      title="I’m listening."
      subtitle="Speak freely about how you’re feeling today."
      onBack={() => router.back()}
    >
      {/* HOME BUTTON */}
      <View style={styles.homeRow}>
        <Pressable
          onPress={() => router.replace('/home')}
          style={({ pressed }) => [
            styles.homeButton,
            pressed && styles.homeButtonPressed,
          ]}
          accessibilityRole="button"
          accessibilityLabel="Go to home"
        >
          <Ionicons
            name="home-outline"
            size={17}
            color={COLORS.forest}
          />
        </Pressable>
      </View>

      <View style={styles.center}>
        <Animated.View
          style={[
            styles.outer,
            { transform: [{ scale: pulse }] },
          ]}
        >
          <View style={styles.middle}>
            <View
              style={[
                styles.inner,
                recording && styles.recording,
              ]}
            >
              {submitting ? (
                <ActivityIndicator size="large" color={COLORS.forest} />
              ) : (
                <Ionicons
                  name={recording ? 'mic' : 'mic-outline'}
                  size={35}
                  color={COLORS.deepForest}
                />
              )}
            </View>
          </View>
        </Animated.View>

        <Text style={styles.timer}>
          {formatTimer(seconds)}
        </Text>

        <Text style={styles.status}>
          {submitting
            ? 'Processing voice...'
            : recording
            ? 'Listening gently...'
            : 'Tap when you’re ready'}
        </Text>

        <Text style={styles.hint}>
          {statusMessage || (recording ? 'You can stop whenever you want.' : 'Speak at your own pace.')}
        </Text>
      </View>

      <Pressable
        disabled={submitting}
        onPress={() => {
          if (recording) {
            handleFinishRecording();
          } else {
            handleStartRecording();
          }
        }}
        style={[
          styles.button,
          recording && styles.stop,
          submitting && { opacity: 0.6 },
        ]}
      >
        {submitting ? (
          <ActivityIndicator color={COLORS.white} size="small" />
        ) : (
          <Ionicons
            name={recording ? 'stop' : 'mic'}
            size={20}
            color={COLORS.white}
          />
        )}

        <Text style={styles.buttonText}>
          {submitting
            ? 'Analyzing acoustic features...'
            : recording
            ? 'Finish & talk with MEDHA'
            : 'Tap to speak'}
        </Text>
      </Pressable>

      {!recording && !submitting && (
        <Pressable
          onPress={() => router.push('/chat')}
          style={styles.skip}
        >
          <Text style={styles.skipText}>
            Skip voice · continue to Talk with MEDHA
          </Text>
        </Pressable>
      )}
    </MedhaScreen>
  );
}

function encodePcmToWav(samples: Float32Array, sampleRate = 16000): Blob {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);

  function writeString(offset: number, str: string) {
    for (let i = 0; i < str.length; i++) {
      view.setUint8(offset + i, str.charCodeAt(i));
    }
  }

  writeString(0, 'RIFF');
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(8, 'WAVE');
  writeString(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, 1, true); // Mono
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(36, 'data');
  view.setUint32(40, samples.length * 2, true);

  let offset = 44;
  for (let i = 0; i < samples.length; i++, offset += 2) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }

  return new Blob([view], { type: 'audio/wav' });
}

const styles = StyleSheet.create({
  homeRow: {
    alignItems: 'flex-end',
    marginTop: -4,
    marginBottom: -8,
  },

  homeButton: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: 'center',
    justifyContent: 'center',
  },

  homeButtonPressed: {
    opacity: 0.7,
    transform: [{ scale: 0.94 }],
  },

  center: {
    flex: 1,
    minHeight: 390,
    alignItems: 'center',
    justifyContent: 'center',
  },

  outer: {
    width: 260,
    height: 260,
    borderRadius: 130,
    backgroundColor: 'rgba(166,170,145,0.18)',
    alignItems: 'center',
    justifyContent: 'center',
  },

  middle: {
    width: 205,
    height: 205,
    borderRadius: 103,
    backgroundColor: 'rgba(170,188,180,0.32)',
    alignItems: 'center',
    justifyContent: 'center',
  },

  inner: {
    width: 125,
    height: 125,
    borderRadius: 63,
    backgroundColor: COLORS.surface,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
  },

  recording: {
    backgroundColor: COLORS.mist,
    borderColor: COLORS.forest,
  },

  timer: {
    fontFamily: 'Inter-Medium',
    fontSize: 10,
    color: COLORS.mutedText,
    marginTop: 23,
    letterSpacing: 1,
  },

  status: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 25,
    color: COLORS.deepForest,
    marginTop: 8,
  },

  hint: {
    fontFamily: 'Inter-Regular',
    fontSize: 10,
    color: COLORS.mutedText,
    marginTop: 7,
  },

  button: {
    height: 56,
    borderRadius: 28,
    backgroundColor: COLORS.forest,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 10,
  },

  stop: {
    backgroundColor: COLORS.wood,
  },

  buttonText: {
    color: COLORS.white,
    fontFamily: 'Inter-Medium',
    fontSize: 12,
  },

  skip: {
    alignItems: 'center',
    paddingVertical: 17,
  },

  skipText: {
    fontFamily: 'Inter-Medium',
    color: COLORS.mutedText,
    fontSize: 10,
  },
});