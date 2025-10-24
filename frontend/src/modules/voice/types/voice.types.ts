/**
 * 语音模块类型定义
 */

export interface VoiceConfig {
  appId: string;
  apiKey: string;
  apiSecret: string;
  language?: string;
  accent?: string;
  voiceName?: string;
  speed?: number;
  volume?: number;
  pitch?: number;
}

export interface ASRResult {
  text: string;
  confidence: number;
  isFinal: boolean;
  timestamp: number;
}

export interface TTSResult {
  audioBlob: Blob;
  duration: number;
  text: string;
}

export interface VoiceRecorderState {
  isRecording: boolean;
  isPaused: boolean;
  duration: number;
  volume: number;
  error?: string;
}

export interface VoicePlayerState {
  isPlaying: boolean;
  isPaused: boolean;
  currentTime: number;
  duration: number;
  volume: number;
  error?: string;
}

export interface VoiceWaveData {
  frequency: number;
  amplitude: number;
  timestamp: number;
}

export interface VoiceCommand {
  type: 'plan_trip' | 'add_expense' | 'search_poi' | 'general';
  text: string;
  confidence: number;
  entities?: Record<string, any>;
}

export interface VoiceFeedback {
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
}
