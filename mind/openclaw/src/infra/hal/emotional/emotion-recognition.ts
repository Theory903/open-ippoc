// mind/openclaw/src/infra/hal/emotional/emotion-recognition.ts
// @emotional - Brain-powered multi-modal emotion recognition and response adaptation

import { EventEmitter } from "events";

export interface EmotionSignal {
  source: "TEXT" | "AUDIO" | "VIDEO" | "BEHAVIOR" | "PHYSIOLOGICAL";
  emotion: EmotionType;
  intensity: number; // 0.0 to 1.0
  confidence: number; // 0.0 to 1.0
  timestamp: number;
  metadata?: Record<string, any>;
}

export type EmotionType =
  | "JOY"
  | "SADNESS"
  | "ANGER"
  | "FEAR"
  | "SURPRISE"
  | "DISGUST"
  | "EXCITEMENT"
  | "FRUSTRATION"
  | "CONFUSION"
  | "SATISFACTION"
  | "CURIOSITY"
  | "NEUTRAL";

export interface MultiModalInput {
  text?: string;
  audio?: AudioBuffer;
  video?: VideoFrame;
  behavioral?: BehavioralData;
  physiological?: PhysiologicalData;
}

export interface AudioBuffer {
  samples: Float32Array;
  sampleRate: number;
  channels: number;
}

export interface VideoFrame {
  width: number;
  height: number;
  data: Uint8Array;
  timestamp: number;
}

export interface BehavioralData {
  typingSpeed: number;
  responseTime: number;
  interactionFrequency: number;
  commandComplexity: number;
}

export interface PhysiologicalData {
  heartRate?: number;
  skinConductance?: number;
  eyeMovement?: EyeTrackingData;
}

export interface EyeTrackingData {
  fixationPoints: Point[];
  saccades: number;
  pupilDilation: number;
}

export interface Point {
  x: number;
  y: number;
  timestamp: number;
}

export interface EmotionState {
  primary: EmotionType;
  secondary?: EmotionType;
  intensity: number;
  confidence: number;
  signals: EmotionSignal[];
  temporalPattern: TemporalPattern;
}

export interface TemporalPattern {
  stability: number; // 0.0 to 1.0 - how consistent the emotion is
  volatility: number; // 0.0 to 1.0 - how rapidly it changes
  trend: "increasing" | "decreasing" | "stable";
}

export interface AdaptiveResponse {
  content: string;
  tone: ToneType;
  urgency: "low" | "medium" | "high";
  empathyLevel: number; // 0.0 to 1.0
  suggestedActions: string[];
}

export type ToneType =
  | "FORMAL"
  | "CASUAL"
  | "EMPATHETIC"
  | "DIRECT"
  | "ENCOURAGING"
  | "CALMING"
  | "PLAYFUL"
  | "PROFESSIONAL";

export class EmotionRecognition extends EventEmitter {
  private emotionHistory: Map<string, EmotionState[]> = new Map();
  private baselineProfiles: Map<string, EmotionBaseline> = new Map();
  private responseTemplates: Map<EmotionType, ResponseTemplate[]> = new Map();
  private brainAdapter: any = null; // Mock brain adapter - would connect to real IPPOC Brain

  constructor() {
    super();
    this.initializeBrainConnection();
    this.initializeResponseTemplates();
  }

  /**
   * Initialize connection to IPPOC Brain (mock implementation)
   */
  private initializeBrainConnection(): void {
    // In a real implementation, this would connect to the IPPOC Brain adapter
    // Following the pattern from brain/cortex/openclaw-cortex/src/ippoc-adapter.ts
    this.brainAdapter = {
      runReasoning: async (prompt: string) => {
        // Mock brain reasoning - in reality would call actual brain tools
        return `Brain analysis of: ${prompt.substring(0, 50)}...`;
      },
      invokeTool: async (envelope: any) => {
        // Mock tool invocation - in reality would use brain/core/tools/*
        return { success: true, output: { result: "Brain tool executed" } };
      },
    };
    console.log("🧠 Emotion recognition connected to IPPOC Brain simulation");
  }

  /**
   * Analyze emotion from multi-modal inputs
   */
  async analyzeEmotion(userId: string, input: MultiModalInput): Promise<EmotionState> {
    const signals: EmotionSignal[] = [];

    // Text sentiment analysis
    if (input.text) {
      signals.push(await this.analyzeTextSentiment(input.text));
    }

    // Audio prosody analysis
    if (input.audio) {
      signals.push(await this.analyzeAudioProsody(input.audio));
    }

    // Video facial expression analysis
    if (input.video) {
      signals.push(await this.analyzeFacialExpressions(input.video));
    }

    // Behavioral pattern analysis
    if (input.behavioral) {
      signals.push(await this.analyzeBehavioralPatterns(input.behavioral));
    }

    // Physiological signal analysis
    if (input.physiological) {
      signals.push(await this.analyzePhysiologicalSignals(input.physiological));
    }

    // Fuse all signals into unified emotion state
    const emotionState = this.fuseEmotionSignals(signals);

    // Update history
    this.updateEmotionHistory(userId, emotionState);

    // Detect emotional patterns
    const patterns = this.detectEmotionalPatterns(userId);

    // Emit events for monitoring
    this.emit("emotion_detected", { userId, emotionState, patterns });

    return {
      ...emotionState,
      temporalPattern: patterns,
    };
  }

  /**
   * Generate adaptive response based on emotional state
   */
  async generateAdaptiveResponse(
    userId: string,
    baseResponse: string,
    emotionState: EmotionState,
  ): Promise<AdaptiveResponse> {
    const primaryEmotion = emotionState.primary;
    const intensity = emotionState.intensity;

    // Select appropriate response template
    const template = this.selectResponseTemplate(primaryEmotion, intensity);

    // Adapt tone and content
    const adaptedContent = this.adaptContent(baseResponse, template, emotionState);
    const tone = this.determineTone(primaryEmotion, intensity);
    const urgency = this.determineUrgency(primaryEmotion, intensity);
    const empathyLevel = this.calculateEmpathyLevel(emotionState);

    // Generate suggested actions
    const suggestedActions = this.generateSuggestedActions(primaryEmotion, intensity);

    const response: AdaptiveResponse = {
      content: adaptedContent,
      tone,
      urgency,
      empathyLevel,
      suggestedActions,
    };

    this.emit("response_generated", { userId, emotionState, response });
    return response;
  }

  /**
   * Update user's emotional baseline profile
   */
  async updateUserBaseline(userId: string, emotionState: EmotionState): Promise<void> {
    const history = this.emotionHistory.get(userId) || [];

    if (history.length < 10) {
      // Need more data to establish baseline
      return;
    }

    // Calculate statistical baseline
    const baseline: EmotionBaseline = {
      averageIntensity: this.calculateAverage(history.map((e) => e.intensity)),
      dominantEmotions: this.getDominantEmotions(history),
      emotionalVariability: this.calculateVariability(history.map((e) => e.intensity)),
      typicalResponsePatterns: this.extractResponsePatterns(history),
    };

    this.baselineProfiles.set(userId, baseline);
    this.emit("baseline_updated", { userId, baseline });
  }

  /**
   * Detect emotional escalation or de-escalation
   */
  detectEmotionalEscalation(userId: string): "escalating" | "deescalating" | "stable" {
    const history = this.emotionHistory.get(userId) || [];
    if (history.length < 5) return "stable";

    const recent = history.slice(-5);
    const older = history.slice(-10, -5);

    const recentIntensity = this.calculateAverage(recent.map((e) => e.intensity));
    const olderIntensity = this.calculateAverage(older.map((e) => e.intensity));

    const change = recentIntensity - olderIntensity;

    if (change > 0.2) return "escalating";
    if (change < -0.2) return "deescalating";
    return "stable";
  }

  /**
   * Private helper methods
   */
  private async analyzeTextSentiment(text: string): Promise<EmotionSignal> {
    // Simplified sentiment analysis
    const lowerText = text.toLowerCase();

    let emotion: EmotionType = "NEUTRAL";
    let intensity = 0.5;

    // Joy indicators
    if (this.containsWords(lowerText, ["happy", "excited", "great", "awesome", "love"])) {
      emotion = "JOY";
      intensity = 0.8;
    }
    // Anger indicators
    else if (this.containsWords(lowerText, ["angry", "frustrated", "annoyed", "mad", "hate"])) {
      emotion = "ANGER";
      intensity = 0.7;
    }
    // Sadness indicators
    else if (this.containsWords(lowerText, ["sad", "depressed", "disappointed", "sorry"])) {
      emotion = "SADNESS";
      intensity = 0.6;
    }
    // Fear indicators
    else if (this.containsWords(lowerText, ["scared", "afraid", "worried", "concerned"])) {
      emotion = "FEAR";
      intensity = 0.7;
    }
    // Surprise indicators
    else if (this.containsWords(lowerText, ["surprised", "amazed", "wow", "unexpected"])) {
      emotion = "SURPRISE";
      intensity = 0.6;
    }

    return {
      source: "TEXT",
      emotion,
      intensity,
      confidence: 0.7,
      timestamp: Date.now(),
    };
  }

  private async analyzeAudioProsody(audio: AudioBuffer): Promise<EmotionSignal> {
    // Simplified prosody analysis
    const features = await this.extractAudioFeatures(audio);

    let emotion: EmotionType = "NEUTRAL";
    let intensity = 0.5;

    // High energy -> Excitement/Anger
    if (features.energy > 0.7 && features.pitchVariance > 0.5) {
      emotion = features.pitchMean > 0.6 ? "EXCITEMENT" : "ANGER";
      intensity = 0.8;
    }
    // Low energy -> Sadness/Tiredness
    else if (features.energy < 0.3 && features.speakingRate < 0.4) {
      emotion = "SADNESS";
      intensity = 0.6;
    }
    // High pitch variance -> Surprise/Fear
    else if (features.pitchVariance > 0.6) {
      emotion = "SURPRISE";
      intensity = 0.7;
    }

    return {
      source: "AUDIO",
      emotion,
      intensity,
      confidence: 0.65,
      timestamp: Date.now(),
      metadata: features,
    };
  }

  private async analyzeFacialExpressions(video: VideoFrame): Promise<EmotionSignal> {
    // Simplified facial expression analysis
    // In real implementation, this would use computer vision models

    // Simulate detection based on frame analysis
    const simulatedEmotion: EmotionType = this.simulateFacialEmotion(video);
    const intensity = Math.random() * 0.4 + 0.6; // 0.6-1.0

    return {
      source: "VIDEO",
      emotion: simulatedEmotion,
      intensity,
      confidence: 0.6,
      timestamp: Date.now(),
    };
  }

  private async analyzeBehavioralPatterns(behavior: BehavioralData): Promise<EmotionSignal> {
    let emotion: EmotionType = "NEUTRAL";
    let intensity = 0.3;

    // Fast typing + high complexity -> Frustration or Excitement
    if (behavior.typingSpeed > 80 && behavior.commandComplexity > 0.7) {
      emotion = behavior.responseTime < 1000 ? "EXCITEMENT" : "FRUSTRATION";
      intensity = 0.7;
    }
    // Slow responses -> Confusion or Sadness
    else if (behavior.responseTime > 5000) {
      emotion = "CONFUSION";
      intensity = 0.5;
    }
    // High interaction frequency -> Engagement/Curiosity
    else if (behavior.interactionFrequency > 10) {
      emotion = "CURIOSITY";
      intensity = 0.6;
    }

    return {
      source: "BEHAVIOR",
      emotion,
      intensity,
      confidence: 0.55,
      timestamp: Date.now(),
      metadata: behavior,
    };
  }

  private async analyzePhysiologicalSignals(physio: PhysiologicalData): Promise<EmotionSignal> {
    let emotion: EmotionType = "NEUTRAL";
    let intensity = 0.4;

    if (physio.heartRate && physio.heartRate > 100) {
      emotion = "EXCITEMENT";
      intensity = 0.7;
    } else if (physio.skinConductance && physio.skinConductance > 5) {
      emotion = "FEAR"; // STRESS not in EmotionType enum, using FEAR instead
      intensity = 0.6;
    }

    return {
      source: "PHYSIOLOGICAL",
      emotion,
      intensity,
      confidence: 0.75,
      timestamp: Date.now(),
      metadata: physio,
    };
  }

  private fuseEmotionSignals(signals: EmotionSignal[]): EmotionState {
    if (signals.length === 0) {
      return {
        primary: "NEUTRAL",
        intensity: 0.1,
        confidence: 1.0,
        signals: [],
        temporalPattern: { stability: 0.5, volatility: 0.5, trend: "stable" },
      };
    }

    // Weighted fusion based on source reliability
    const weights: Record<string, number> = {
      TEXT: 0.3,
      AUDIO: 0.4,
      VIDEO: 0.2,
      BEHAVIOR: 0.05,
      PHYSIOLOGICAL: 0.05,
    };

    // Calculate weighted averages
    let weightedEmotion: Record<EmotionType, number> = {} as any;
    let totalWeight = 0;
    let totalConfidence = 0;
    let totalIntensity = 0;

    for (const signal of signals) {
      const weight = weights[signal.source] || 0.1;
      const weightedValue = signal.intensity * signal.confidence * weight;

      weightedEmotion[signal.emotion] = (weightedEmotion[signal.emotion] || 0) + weightedValue;
      totalWeight += weight;
      totalConfidence += signal.confidence * weight;
      totalIntensity += signal.intensity * weight;
    }

    // Find primary emotion
    let primaryEmotion: EmotionType = "NEUTRAL";
    let maxWeightedValue = 0;

    for (const [emotion, value] of Object.entries(weightedEmotion)) {
      if (value > maxWeightedValue) {
        maxWeightedValue = value;
        primaryEmotion = emotion as EmotionType;
      }
    }

    return {
      primary: primaryEmotion,
      intensity: totalIntensity / totalWeight,
      confidence: totalConfidence / totalWeight,
      signals,
      temporalPattern: { stability: 0.5, volatility: 0.5, trend: "stable" },
    };
  }

  private detectEmotionalPatterns(userId: string): TemporalPattern {
    const history = this.emotionHistory.get(userId) || [];
    if (history.length < 3) {
      return { stability: 0.5, volatility: 0.5, trend: "stable" };
    }

    const recent = history.slice(-10);
    const intensities = recent.map((e) => e.intensity);

    const stability = 1 - this.calculateVariability(recent.map((e) => e.intensity));
    const volatility = this.calculateVolatility(intensities);
    const trend = this.calculateTrend(intensities);

    return { stability, volatility, trend };
  }

  private selectResponseTemplate(emotion: EmotionType, intensity: number): ResponseTemplate {
    const templates = this.responseTemplates.get(emotion) || [];
    if (templates.length === 0) {
      return this.getDefaultTemplate();
    }

    // Select based on intensity
    const suitable = templates.filter(
      (t) => intensity >= t.minIntensity && intensity <= t.maxIntensity,
    );

    return suitable.length > 0 ? suitable[0] : templates[0];
  }

  private adaptContent(
    baseContent: string,
    template: ResponseTemplate,
    emotionState: EmotionState,
  ): string {
    let adapted = baseContent;

    // Apply empathy modifiers
    if (emotionState.intensity > 0.7) {
      adapted = `I can sense you're feeling quite strongly about this. ${adapted}`;
    }

    // Apply template-specific adaptations
    if (template.modifiers) {
      for (const modifier of template.modifiers) {
        adapted = modifier(adapted, emotionState);
      }
    }

    return adapted;
  }

  private determineTone(emotion: EmotionType, intensity: number): ToneType {
    if (emotion === "ANGER" || emotion === "FRUSTRATION") {
      return intensity > 0.7 ? "CALMING" : "EMPATHETIC";
    }
    if (emotion === "SADNESS") {
      return "EMPATHETIC";
    }
    if (emotion === "EXCITEMENT" || emotion === "JOY") {
      return "PLAYFUL";
    }
    if (emotion === "CONFUSION") {
      return "DIRECT";
    }
    return "PROFESSIONAL";
  }

  private determineUrgency(emotion: EmotionType, intensity: number): "low" | "medium" | "high" {
    if (intensity > 0.8) return "high";
    if (intensity > 0.5) return "medium";
    return "low";
  }

  private calculateEmpathyLevel(emotionState: EmotionState): number {
    // Higher empathy for negative emotions and high intensity
    const baseEmpathy = 0.5;
    const emotionWeight =
      emotionState.primary.includes("SADNESS") ||
      emotionState.primary.includes("FEAR") ||
      emotionState.primary.includes("FRUSTRATION")
        ? 0.3
        : 0;
    const intensityWeight = emotionState.intensity * 0.2;

    return Math.min(1.0, baseEmpathy + emotionWeight + intensityWeight);
  }

  private generateSuggestedActions(emotion: EmotionType, intensity: number): string[] {
    const actions: string[] = [];

    if (emotion === "FRUSTRATION" && intensity > 0.6) {
      actions.push("Take a brief break", "Break down the problem into smaller steps");
    }
    if (emotion === "CONFUSION") {
      actions.push("Ask clarifying questions", "Request examples or demonstrations");
    }
    if (emotion === "EXCITEMENT") {
      actions.push("Channel this energy into productive action", "Set specific goals");
    }

    return actions;
  }

  // Utility methods
  private containsWords(text: string, words: string[]): boolean {
    return words.some((word) => text.includes(word));
  }

  private calculateAverage(numbers: number[]): number {
    return numbers.reduce((a, b) => a + b, 0) / numbers.length;
  }

  private calculateVariability(numbers: number[]): number {
    const mean = this.calculateAverage(numbers);
    const variance =
      numbers.reduce((sum, num) => sum + Math.pow(num - mean, 2), 0) / numbers.length;
    return Math.sqrt(variance);
  }

  private calculateVolatility(numbers: number[]): number {
    if (numbers.length < 2) return 0;
    const changes = [];
    for (let i = 1; i < numbers.length; i++) {
      changes.push(Math.abs(numbers[i] - numbers[i - 1]));
    }
    return this.calculateAverage(changes);
  }

  private calculateTrend(numbers: number[]): "increasing" | "decreasing" | "stable" {
    if (numbers.length < 2) return "stable";
    const firstHalf = this.calculateAverage(numbers.slice(0, Math.floor(numbers.length / 2)));
    const secondHalf = this.calculateAverage(numbers.slice(Math.floor(numbers.length / 2)));

    const diff = secondHalf - firstHalf;
    if (diff > 0.1) return "increasing";
    if (diff < -0.1) return "decreasing";
    return "stable";
  }

  private async extractAudioFeatures(audio: AudioBuffer): Promise<any> {
    // Simplified audio feature extraction
    return {
      energy: Math.random(),
      pitchMean: Math.random(),
      pitchVariance: Math.random(),
      speakingRate: Math.random(),
    };
  }

  private simulateFacialEmotion(video: VideoFrame): EmotionType {
    // Simulate facial emotion detection
    const emotions: EmotionType[] = ["JOY", "SADNESS", "ANGER", "SURPRISE", "NEUTRAL"];
    return emotions[Math.floor(Math.random() * emotions.length)];
  }

  private updateEmotionHistory(userId: string, emotionState: EmotionState): void {
    if (!this.emotionHistory.has(userId)) {
      this.emotionHistory.set(userId, []);
    }

    const history = this.emotionHistory.get(userId)!;
    history.push(emotionState);

    // Keep only last 100 entries
    if (history.length > 100) {
      history.splice(0, history.length - 100);
    }
  }

  private initializeResponseTemplates(): void {
    // Initialize response templates for different emotions
    this.responseTemplates.set("FRUSTRATION", [
      {
        minIntensity: 0.6,
        maxIntensity: 1.0,
        modifiers: [
          (text: string) => `I understand this is frustrating. ${text}`,
          (text: string) => `${text} Let's break this down into manageable steps.`,
        ],
      },
    ]);

    this.responseTemplates.set("CONFUSION", [
      {
        minIntensity: 0.5,
        maxIntensity: 1.0,
        modifiers: [
          (text: string) => `I can see this might be confusing. ${text}`,
          (text: string) => `${text} Would you like me to explain this differently?`,
        ],
      },
    ]);
  }

  private getDefaultTemplate(): ResponseTemplate {
    return {
      minIntensity: 0,
      maxIntensity: 1,
      modifiers: [],
    };
  }

  private getDominantEmotions(history: EmotionState[]): EmotionType[] {
    const emotionCounts: Record<EmotionType, number> = {} as any;

    for (const state of history) {
      emotionCounts[state.primary] = (emotionCounts[state.primary] || 0) + 1;
    }

    return Object.entries(emotionCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 3)
      .map(([emotion]) => emotion as EmotionType);
  }

  private extractResponsePatterns(history: EmotionState[]): string[] {
    // Simplified pattern extraction
    return ["responsive", "deliberative", "exploratory"];
  }
}

interface ResponseTemplate {
  minIntensity: number;
  maxIntensity: number;
  modifiers: Array<(text: string, emotion: EmotionState) => string>;
}

interface EmotionBaseline {
  averageIntensity: number;
  dominantEmotions: EmotionType[];
  emotionalVariability: number;
  typicalResponsePatterns: string[];
}

// Singleton instance
let emotionRecognition: EmotionRecognition | null = null;

export function getEmotionRecognition(): EmotionRecognition {
  if (!emotionRecognition) {
    emotionRecognition = new EmotionRecognition();
  }
  return emotionRecognition;
}
