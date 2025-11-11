/**
 * 语音输出Hook
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { VoicePlayerState, TTSResult } from '../types/voice.types';
import VoiceService from '../services/voice.service';

interface UseVoiceOutputOptions {
  onStart?: () => void;
  onEnd?: () => void;
  onError?: (error: string) => void;
  autoPlay?: boolean;
}

export function useVoiceOutput(options: UseVoiceOutputOptions = {}) {
  const {
    onStart,
    onEnd,
    onError,
    autoPlay = false
  } = options;

  const [state, setState] = useState<VoicePlayerState>({
    isPlaying: false,
    isPaused: false,
    currentTime: 0,
    duration: 0,
    volume: 1,
    error: undefined
  });

  const [queue, setQueue] = useState<string[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  const voiceServiceRef = useRef<VoiceService | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // 初始化语音服务
  useEffect(() => {
    const initVoiceService = async () => {
      try {
        const config = {
          appId: import.meta.env.VITE_XUNFEI_APP_ID || '',
          apiKey: import.meta.env.VITE_XUNFEI_API_KEY || '',
          apiSecret: import.meta.env.VITE_XUNFEI_API_SECRET || '',
          voiceName: 'xiaoyan',
          speed: 50,
          volume: 50,
          pitch: 50
        };

        voiceServiceRef.current = new VoiceService(config);
        await voiceServiceRef.current.initialize();
      } catch (error) {
        setState(prev => ({ 
          ...prev, 
          error: error instanceof Error ? error.message : '语音服务初始化失败' 
        }));
        onError?.(error instanceof Error ? error.message : '语音服务初始化失败');
      }
    };

    initVoiceService();

    return () => {
      if (voiceServiceRef.current) {
        voiceServiceRef.current.destroy();
      }
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, [onError]);

  // 播放音频
  const playAudio = useCallback(async (audioBlob: Blob) => {
    return new Promise<void>((resolve, reject) => {
      const audio = new Audio();
      audio.src = URL.createObjectURL(audioBlob);
      
      audio.onloadedmetadata = () => {
        setState(prev => ({ 
          ...prev, 
          duration: audio.duration * 1000 // 转换为毫秒
        }));
      };

      audio.onplay = () => {
        setState(prev => ({ 
          ...prev, 
          isPlaying: true, 
          isPaused: false,
          error: undefined
        }));
        onStart?.();

        // 开始计时
        intervalRef.current = setInterval(() => {
          setState(prev => ({
            ...prev,
            currentTime: audio.currentTime * 1000
          }));
        }, 100);
      };

      audio.onended = () => {
        setState(prev => ({ 
          ...prev, 
          isPlaying: false, 
          isPaused: false,
          currentTime: 0
        }));
        onEnd?.();

        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }

        // 清理音频对象
        URL.revokeObjectURL(audio.src);
        resolve();
      };

      audio.onerror = (error) => {
        setState(prev => ({ 
          ...prev, 
          error: '音频播放失败',
          isPlaying: false
        }));
        onError?.('音频播放失败');
        reject(error);
      };

      audioRef.current = audio;
      audio.play().catch(reject);
    });
  }, [onStart, onEnd, onError]);

  // 合成并播放文本
  const speak = useCallback(async (text: string) => {
    if (!voiceServiceRef.current || !text.trim()) return;

    try {
      setIsProcessing(true);
      setState(prev => ({ ...prev, error: undefined }));

      const result: TTSResult = await voiceServiceRef.current.synthesize(text);
      await playAudio(result.audioBlob);

    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : '语音合成失败' 
      }));
      onError?.(error instanceof Error ? error.message : '语音合成失败');
    } finally {
      setIsProcessing(false);
    }
  }, [playAudio, onError]);

  // 添加到播放队列
  const addToQueue = useCallback((text: string) => {
    setQueue(prev => [...prev, text]);
  }, []);

  // 播放队列
  const playQueue = useCallback(async () => {
    if (queue.length === 0 || state.isPlaying || isProcessing) return;

    const nextText = queue[0];
    setQueue(prev => prev.slice(1));
    
    await speak(nextText);
    
    // 继续播放队列中的下一个
    if (queue.length > 1) {
      setTimeout(() => playQueue(), 100);
    }
  }, [queue, state.isPlaying, isProcessing, speak]);

  // 自动播放队列
  useEffect(() => {
    if (autoPlay && queue.length > 0 && !state.isPlaying && !isProcessing) {
      playQueue();
    }
  }, [autoPlay, queue, state.isPlaying, isProcessing, playQueue]);

  // 停止播放
  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    
    setState(prev => ({ 
      ...prev, 
      isPlaying: false, 
      isPaused: false,
      currentTime: 0
    }));

    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  // 暂停播放
  const pause = useCallback(() => {
    if (audioRef.current && state.isPlaying) {
      audioRef.current.pause();
      setState(prev => ({ ...prev, isPaused: true }));
    }
  }, [state.isPlaying]);

  // 恢复播放
  const resume = useCallback(() => {
    if (audioRef.current && state.isPaused) {
      audioRef.current.play();
      setState(prev => ({ ...prev, isPaused: false }));
    }
  }, [state.isPaused]);

  // 清空队列
  const clearQueue = useCallback(() => {
    setQueue([]);
  }, []);

  // 设置音量
  const setVolume = useCallback((volume: number) => {
    if (audioRef.current) {
      audioRef.current.volume = Math.max(0, Math.min(1, volume));
      setState(prev => ({ ...prev, volume }));
    }
  }, []);

  return {
    state,
    queue,
    isProcessing,
    speak,
    addToQueue,
    playQueue,
    stop,
    pause,
    resume,
    clearQueue,
    setVolume,
    isInitialized: !!voiceServiceRef.current
  };
}
