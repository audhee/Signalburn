import { Ionicons } from "@expo/vector-icons";
import * as Speech from "expo-speech";
import { useCallback, useEffect, useRef, useState } from "react";
import {
    Image,
    Platform,
    StyleSheet,
    Text,
    TouchableOpacity,
    View,
} from "react-native";
import Animated, {
    Easing,
    cancelAnimation,
    interpolate,
    useAnimatedStyle,
    useSharedValue,
    withRepeat,
    withSequence,
    withTiming,
} from "react-native-reanimated";
import { SafeAreaView } from "react-native-safe-area-context";

const DOCTOR_IMG = require("../assets/images/doctor.png");

type AppState = "idle" | "listening" | "thinking" | "speaking";

type FirstAidResponse = {
  title: string;
  detail: string;
};

const SCENARIOS = [
  "bleeding",
  "burn",
  "choking",
  "cpr",
  "fainting",
  "eye_injury",
  "fracture",
] as const;

const FALLBACK_RESPONSE: FirstAidResponse = {
  title: "Stay calm and check breathing",
  detail: "Speak gently. Keep them still until professional help arrives.",
};

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function Index() {
  const [appState, setAppState] = useState<AppState>("idle");
  const [response, setResponse] = useState<FirstAidResponse>(FALLBACK_RESPONSE);
  const scenarioIdxRef = useRef<number>(0);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);
  const abortRef = useRef<AbortController | null>(null);

  // shared values
  const avatarScale = useSharedValue(1);
  const glowOpacity = useSharedValue(0.3);
  const ringRotate = useSharedValue(0);
  const wave1 = useSharedValue(0);
  const wave2 = useSharedValue(0);
  const wave3 = useSharedValue(0);
  const wave4 = useSharedValue(0);
  const wave5 = useSharedValue(0);
  const progressX = useSharedValue(-1);

  const clearTimers = useCallback(() => {
    timersRef.current.forEach((t) => clearTimeout(t));
    timersRef.current = [];
  }, []);

  const speakResponse = useCallback((r: FirstAidResponse) => {
    Speech.stop();
    const text = `${r.title}. ${r.detail}`;
    Speech.speak(text, {
      rate: 0.85,
      pitch: 1.0,
      language: "en-US",
    });
  }, []);

  const stopAllAnimations = useCallback(() => {
    cancelAnimation(avatarScale);
    cancelAnimation(glowOpacity);
    cancelAnimation(ringRotate);
    cancelAnimation(wave1);
    cancelAnimation(wave2);
    cancelAnimation(wave3);
    cancelAnimation(wave4);
    cancelAnimation(wave5);
    cancelAnimation(progressX);
    avatarScale.value = withTiming(1, { duration: 300 });
    glowOpacity.value = withTiming(0.3, { duration: 300 });
    wave1.value = withTiming(0, { duration: 200 });
    wave2.value = withTiming(0, { duration: 200 });
    wave3.value = withTiming(0, { duration: 200 });
    wave4.value = withTiming(0, { duration: 200 });
    wave5.value = withTiming(0, { duration: 200 });
  }, [
    avatarScale,
    glowOpacity,
    ringRotate,
    wave1,
    wave2,
    wave3,
    wave4,
    wave5,
    progressX,
  ]);

  // Animation orchestration based on state
  useEffect(() => {
    stopAllAnimations();
    if (appState === "listening") {
      glowOpacity.value = withRepeat(
        withSequence(
          withTiming(0.95, { duration: 900, easing: Easing.inOut(Easing.ease) }),
          withTiming(0.4, { duration: 900, easing: Easing.inOut(Easing.ease) })
        ),
        -1,
        false
      );
      avatarScale.value = withRepeat(
        withSequence(
          withTiming(1.04, { duration: 900 }),
          withTiming(1, { duration: 900 })
        ),
        -1,
        false
      );
      ringRotate.value = withRepeat(
        withTiming(360, { duration: 8000, easing: Easing.linear }),
        -1,
        false
      );
    } else if (appState === "thinking") {
      glowOpacity.value = withRepeat(
        withSequence(
          withTiming(0.7, { duration: 700 }),
          withTiming(0.3, { duration: 700 })
        ),
        -1,
        false
      );
      progressX.value = withRepeat(
        withTiming(1, { duration: 1400, easing: Easing.inOut(Easing.ease) }),
        -1,
        false
      );
    } else if (appState === "speaking") {
      glowOpacity.value = withRepeat(
        withSequence(
          withTiming(0.85, { duration: 600 }),
          withTiming(0.45, { duration: 600 })
        ),
        -1,
        false
      );
      const startWave = (sv: typeof wave1, delay: number) => {
        sv.value = withRepeat(
          withSequence(
            withTiming(1, { duration: 350 + delay, easing: Easing.inOut(Easing.ease) }),
            withTiming(0, { duration: 350 + delay, easing: Easing.inOut(Easing.ease) })
          ),
          -1,
          false
        );
      };
      startWave(wave1, 0);
      startWave(wave2, 80);
      startWave(wave3, 160);
      startWave(wave4, 100);
      startWave(wave5, 60);
    } else {
      // idle - subtle teal glow
      glowOpacity.value = withRepeat(
        withSequence(
          withTiming(0.55, { duration: 1800 }),
          withTiming(0.3, { duration: 1800 })
        ),
        -1,
        false
      );
    }
  }, [appState, avatarScale, glowOpacity, ringRotate, wave1, wave2, wave3, wave4, wave5, progressX, stopAllAnimations]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearTimers();
      Speech.stop();
    };
  }, [clearTimers]);

  const startFlow = useCallback(() => {
    Speech.stop();
    clearTimers();
    abortRef.current?.abort();

    setAppState("listening");

    // Pick next scenario in cycle
    const scenario = SCENARIOS[scenarioIdxRef.current % SCENARIOS.length];
    scenarioIdxRef.current += 1;

    // Fire LLM call in parallel with the listening animation
    const ac = new AbortController();
    abortRef.current = ac;
    const llmPromise: Promise<FirstAidResponse> = fetch(
      `${BACKEND_URL}/api/first-aid`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario }),
        signal: ac.signal,
      }
    )
      .then(async (r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const data = await r.json();
        return { title: data.title, detail: data.detail };
      })
      .catch((err) => {
        console.warn("first-aid api failed", err);
        return FALLBACK_RESPONSE;
      });

    const t1 = setTimeout(() => {
      setAppState("thinking");
      const t2 = setTimeout(async () => {
        const next = await llmPromise;
        if (ac.signal.aborted) return;
        setResponse(next);
        setAppState("speaking");
        speakResponse(next);
      }, 2000);
      timersRef.current.push(t2);
    }, 2000);
    timersRef.current.push(t1);
  }, [clearTimers, speakResponse]);

  const handleNo = useCallback(() => {
    Speech.stop();
    clearTimers();
    abortRef.current?.abort();
    setAppState("idle");
  }, [clearTimers]);

  const handleRepeat = useCallback(() => {
    if (appState === "speaking") {
      speakResponse(response);
    } else {
      // From idle, speak last response again
      speakResponse(response);
      setAppState("speaking");
    }
  }, [appState, response, speakResponse]);

  const handleNext = useCallback(() => {
    Speech.stop();
    clearTimers();
    setAppState("idle");
  }, [clearTimers]);

  // Animated styles
  const avatarStyle = useAnimatedStyle(() => ({
    transform: [{ scale: avatarScale.value }],
  }));
  const glowStyle = useAnimatedStyle(() => ({
    opacity: glowOpacity.value,
  }));
  const ringStyle = useAnimatedStyle(() => ({
    transform: [{ rotate: `${ringRotate.value}deg` }],
  }));
  const progressStyle = useAnimatedStyle(() => ({
    transform: [
      {
        translateX: interpolate(progressX.value, [-1, 1], [-180, 180]),
      },
    ],
  }));

  const bar1Style = useAnimatedStyle(() => ({
    height: interpolate(wave1.value, [0, 1], [8, 30]),
    opacity: interpolate(wave1.value, [0, 1], [0.5, 1]),
  }));
  const bar2Style = useAnimatedStyle(() => ({
    height: interpolate(wave2.value, [0, 1], [14, 36]),
    opacity: interpolate(wave2.value, [0, 1], [0.5, 1]),
  }));
  const bar3Style = useAnimatedStyle(() => ({
    height: interpolate(wave3.value, [0, 1], [22, 44]),
    opacity: interpolate(wave3.value, [0, 1], [0.5, 1]),
  }));
  const bar4Style = useAnimatedStyle(() => ({
    height: interpolate(wave4.value, [0, 1], [16, 38]),
    opacity: interpolate(wave4.value, [0, 1], [0.5, 1]),
  }));
  const bar5Style = useAnimatedStyle(() => ({
    height: interpolate(wave5.value, [0, 1], [10, 32]),
    opacity: interpolate(wave5.value, [0, 1], [0.5, 1]),
  }));

  // Glow color by state
  const glowColor =
    appState === "listening"
      ? "#3FE0C5"
      : appState === "thinking"
      ? "#5B8CFF"
      : appState === "speaking"
      ? "#5B8CFF"
      : "#3FE0C5";

  return (
    <View style={styles.root} testID="emergency-assistant-root">
      {/* Background gradient layers */}
      <View style={styles.bgBase} />
      <View style={styles.bgGlowTop} />
      <View style={styles.bgGlowBottom} />

      <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
        {/* Top status bar */}
        <View style={styles.topBar}>
          {appState === "thinking" ? (
            <View style={styles.connectedPill} testID="status-connected">
              <View style={[styles.statusDot, { backgroundColor: "#3FE0C5" }]} />
              <Text style={styles.connectedText}>CONNECTED</Text>
            </View>
          ) : appState === "listening" ? (
            <View style={styles.listeningPill} testID="status-listening">
              <View style={[styles.statusDot, { backgroundColor: "#3FE0C5" }]} />
              <Text style={styles.connectedText}>Listening...</Text>
            </View>
          ) : (
            <Text style={styles.title} testID="screen-title">
              EMERGENCY ASSISTANT
            </Text>
          )}
        </View>

        {/* Avatar area */}
        <View style={styles.avatarWrap}>
          <Animated.View
            style={[
              styles.glow,
              { shadowColor: glowColor, backgroundColor: glowColor + "22" },
              glowStyle,
            ]}
          />

          {appState === "listening" && (
            <Animated.View
              style={[styles.tickRingContainer, ringStyle]}
              pointerEvents="none"
            >
              {Array.from({ length: 60 }).map((_, i) => (
                <View
                  key={i}
                  style={[
                    styles.tick,
                    {
                      transform: [
                        { rotate: `${i * 6}deg` },
                        { translateY: -150 },
                      ],
                      opacity: i % 2 === 0 ? 0.9 : 0.3,
                      backgroundColor:
                        i % 6 === 0 ? "#FFD96A" : "#3FE0C5",
                    },
                  ]}
                />
              ))}
            </Animated.View>
          )}

          <Animated.View style={[styles.avatarOuter, avatarStyle]}>
            <View
              style={[
                styles.avatarBorder,
                { borderColor: glowColor + "AA" },
              ]}
            >
              <Image
                source={DOCTOR_IMG}
                style={styles.avatar}
                testID="doctor-avatar"
              />
            </View>
          </Animated.View>
        </View>

        {/* Text + state-specific content */}
        <View style={styles.contentArea}>
          {appState === "idle" && (
            <View style={styles.centerCol} testID="state-idle">
              <Text style={styles.headline}>I&apos;m here to help</Text>
              <Text style={styles.subtle}>stay calm</Text>
              <View style={styles.micOffWrap}>
                <Ionicons name="mic-off" size={42} color="#8593A8" />
                <Text style={styles.micOffText}>Microphone off</Text>
              </View>
            </View>
          )}

          {appState === "listening" && (
            <View style={styles.centerCol} testID="state-listening">
              <Text style={styles.headline}>I&apos;m listening...</Text>
              <Text style={styles.subtle}>Please describe the emergency</Text>
              <View style={styles.micOnWrap}>
                <View style={styles.micOnCircle}>
                  <Ionicons name="mic" size={28} color="#fff" />
                </View>
              </View>
            </View>
          )}

          {appState === "thinking" && (
            <View style={styles.centerCol} testID="state-thinking">
              <Text style={styles.headlineLg}>Analyzing situation...</Text>
              <Text style={styles.subtle}>Please wait</Text>
              <View style={styles.progressTrack}>
                <Animated.View style={[styles.progressBar, progressStyle]} />
              </View>
              <Text style={styles.processingText}>Processing</Text>
            </View>
          )}

          {appState === "speaking" && (
            <View style={styles.centerCol} testID="state-speaking">
              <Text style={styles.aiSpeakingTag}>AI IS SPEAKING</Text>
              <Text style={styles.responseTitle}>{response.title}</Text>
              <Text style={styles.responseDetail}>{response.detail}</Text>
              <View style={styles.waveRow}>
                <Animated.View style={[styles.waveBar, bar1Style]} />
                <Animated.View style={[styles.waveBar, bar2Style]} />
                <Animated.View style={[styles.waveBar, bar3Style]} />
                <Animated.View style={[styles.waveBar, bar4Style]} />
                <Animated.View style={[styles.waveBar, bar5Style]} />
              </View>
            </View>
          )}
        </View>

        {/* Buttons */}
        <View style={styles.buttonsArea}>
          {appState === "speaking" ? (
            <View style={styles.speakingButtons}>
              <TouchableOpacity
                style={styles.repeatDarkBtn}
                onPress={handleRepeat}
                testID="btn-repeat-speaking"
                activeOpacity={0.8}
              >
                <Ionicons name="refresh" size={16} color="#fff" />
                <Text style={styles.repeatDarkText}>Repeat</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.nextBtn}
                onPress={handleNext}
                testID="btn-next"
                activeOpacity={0.85}
              >
                <Text style={styles.nextText}>Next</Text>
                <Ionicons name="arrow-forward" size={16} color="#fff" />
              </TouchableOpacity>
            </View>
          ) : appState === "thinking" ? (
            <View style={styles.thinkingPill} />
          ) : (
            <View style={styles.idleButtons}>
              <TouchableOpacity
                style={[styles.actionBtn, styles.yesBtn]}
                onPress={startFlow}
                testID="btn-yes"
                activeOpacity={0.85}
              >
                <Ionicons name="checkmark" size={18} color="#fff" />
                <Text style={styles.actionText}>Yes</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.actionBtn, styles.noBtn]}
                onPress={handleNo}
                testID="btn-no"
                activeOpacity={0.85}
              >
                <Ionicons name="close" size={18} color="#fff" />
                <Text style={styles.actionText}>No</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.actionBtn, styles.repeatBtn]}
                onPress={handleRepeat}
                testID="btn-repeat"
                activeOpacity={0.85}
              >
                <Ionicons name="refresh" size={18} color="#fff" />
                <Text style={styles.actionText}>Repeat</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: "#04060D",
  },
  bgBase: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "#06091A",
  },
  bgGlowTop: {
    position: "absolute",
    top: -120,
    left: -80,
    width: 380,
    height: 380,
    borderRadius: 190,
    backgroundColor: "#0E2A4A",
    opacity: 0.55,
    ...Platform.select({
      web: { filter: "blur(60px)" as any },
    }),
  },
  bgGlowBottom: {
    position: "absolute",
    bottom: -160,
    right: -80,
    width: 420,
    height: 420,
    borderRadius: 210,
    backgroundColor: "#0A3D3A",
    opacity: 0.4,
    ...Platform.select({
      web: { filter: "blur(80px)" as any },
    }),
  },
  safe: {
    flex: 1,
    paddingHorizontal: 20,
  },
  topBar: {
    height: 44,
    alignItems: "center",
    justifyContent: "center",
    flexDirection: "row",
    marginTop: 8,
  },
  title: {
    color: "#D8DEEA",
    fontSize: 13,
    letterSpacing: 4,
    fontWeight: "600",
  },
  connectedPill: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    backgroundColor: "rgba(63,224,197,0.12)",
    borderWidth: 1,
    borderColor: "rgba(63,224,197,0.3)",
  },
  listeningPill: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    backgroundColor: "rgba(63,224,197,0.12)",
    borderWidth: 1,
    borderColor: "rgba(63,224,197,0.3)",
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  connectedText: {
    color: "#3FE0C5",
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 1.5,
  },
  avatarWrap: {
    height: 340,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 10,
  },
  glow: {
    position: "absolute",
    width: 300,
    height: 300,
    borderRadius: 150,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 1,
    shadowRadius: 60,
    elevation: 40,
  },
  tickRingContainer: {
    position: "absolute",
    width: 320,
    height: 320,
    alignItems: "center",
    justifyContent: "center",
  },
  tick: {
    position: "absolute",
    width: 2,
    height: 14,
    borderRadius: 1,
  },
  avatarOuter: {
    width: 240,
    height: 240,
    alignItems: "center",
    justifyContent: "center",
  },
  avatarBorder: {
    width: 230,
    height: 230,
    borderRadius: 115,
    borderWidth: 3,
    overflow: "hidden",
    backgroundColor: "#0c1320",
  },
  avatar: {
    width: "100%",
    height: "100%",
    resizeMode: "cover",
  },
  contentArea: {
    flex: 1,
    alignItems: "center",
    justifyContent: "flex-start",
    paddingTop: 8,
  },
  centerCol: {
    alignItems: "center",
    justifyContent: "flex-start",
    width: "100%",
  },
  headline: {
    color: "#fff",
    fontSize: 26,
    fontWeight: "700",
    marginBottom: 6,
    textAlign: "center",
  },
  headlineLg: {
    color: "#fff",
    fontSize: 28,
    fontWeight: "700",
    marginBottom: 8,
    textAlign: "center",
  },
  subtle: {
    color: "#8FA0BD",
    fontSize: 14,
    marginBottom: 18,
    textAlign: "center",
  },
  micOffWrap: {
    alignItems: "center",
    marginTop: 6,
  },
  micOffText: {
    color: "#8FA0BD",
    fontSize: 12,
    marginTop: 8,
  },
  micOnWrap: {
    alignItems: "center",
    marginTop: 4,
  },
  micOnCircle: {
    width: 64,
    height: 64,
    borderRadius: 14,
    backgroundColor: "#1A8FE3",
    alignItems: "center",
    justifyContent: "center",
    shadowColor: "#1A8FE3",
    shadowOpacity: 0.6,
    shadowRadius: 18,
    shadowOffset: { width: 0, height: 0 },
    elevation: 8,
  },
  progressTrack: {
    width: 180,
    height: 3,
    backgroundColor: "rgba(255,255,255,0.08)",
    borderRadius: 2,
    overflow: "hidden",
    marginTop: 8,
    marginBottom: 16,
  },
  progressBar: {
    width: 80,
    height: 3,
    borderRadius: 2,
    backgroundColor: "#5B8CFF",
  },
  processingText: {
    color: "#fff",
    fontSize: 18,
    fontWeight: "700",
    letterSpacing: 1,
  },
  aiSpeakingTag: {
    color: "#5B8CFF",
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 2,
    marginBottom: 12,
  },
  responseTitle: {
    color: "#fff",
    fontSize: 22,
    fontWeight: "700",
    textAlign: "center",
    paddingHorizontal: 20,
    marginBottom: 10,
    lineHeight: 28,
  },
  responseDetail: {
    color: "#9FB0CC",
    fontSize: 13,
    textAlign: "center",
    paddingHorizontal: 30,
    marginBottom: 18,
  },
  waveRow: {
    flexDirection: "row",
    alignItems: "center",
    height: 36,
    gap: 5,
  },
  waveBar: {
    width: 4,
    backgroundColor: "#5B8CFF",
    borderRadius: 2,
  },
  buttonsArea: {
    paddingBottom: 12,
    paddingTop: 6,
  },
  idleButtons: {
    flexDirection: "row",
    justifyContent: "center",
    gap: 10,
  },
  actionBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 18,
    paddingVertical: 14,
    borderRadius: 14,
    minWidth: 96,
    gap: 6,
  },
  actionText: {
    color: "#fff",
    fontSize: 14,
    fontWeight: "600",
  },
  yesBtn: {
    backgroundColor: "#1A6BE3",
  },
  noBtn: {
    backgroundColor: "#2A2F3D",
  },
  repeatBtn: {
    backgroundColor: "#1FB672",
  },
  thinkingPill: {
    height: 4,
    width: 80,
    backgroundColor: "rgba(255,255,255,0.18)",
    borderRadius: 2,
    alignSelf: "center",
    marginBottom: 12,
  },
  speakingButtons: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingHorizontal: 4,
  },
  repeatDarkBtn: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 18,
    paddingVertical: 12,
    borderRadius: 12,
    backgroundColor: "#1A1F2E",
    gap: 6,
  },
  repeatDarkText: {
    color: "#fff",
    fontSize: 14,
    fontWeight: "500",
  },
  nextBtn: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 26,
    paddingVertical: 12,
    borderRadius: 12,
    backgroundColor: "#1A6BE3",
    gap: 6,
  },
  nextText: {
    color: "#fff",
    fontSize: 14,
    fontWeight: "600",
  },
});

