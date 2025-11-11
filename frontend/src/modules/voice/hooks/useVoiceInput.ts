/**
 * 语音输入Hook
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { VoiceRecorderState, ASRResult, VoiceCommand } from '../types/voice.types';
import VoiceService from '../services/voice.service';

interface UseVoiceInputOptions {
  onResult?: (result: ASRResult) => void;
  onCommand?: (command: VoiceCommand) => void;
  onError?: (error: string) => void;
  autoStart?: boolean;
  continuous?: boolean;
}

export function useVoiceInput(options: UseVoiceInputOptions = {}) {
  const {
    onResult,
    onCommand,
    onError,
    autoStart = false,
    continuous = false
  } = options;

  const [state, setState] = useState<VoiceRecorderState>({
    isRecording: false,
    isPaused: false,
    duration: 0,
    volume: 0,
    error: undefined
  });

  const [results, setResults] = useState<ASRResult[]>([]);
  const [currentText, setCurrentText] = useState<string>('');

  const voiceServiceRef = useRef<VoiceService | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number>(0);

  // 初始化语音服务
  useEffect(() => {
    const initVoiceService = async () => {
      try {
        // 检查是否启用语音功能
        const voiceEnabled = import.meta.env.VITE_ENABLE_VOICE === 'true';
        
        if (!voiceEnabled) {
          console.warn('语音功能未启用。请在.env文件中设置VITE_ENABLE_VOICE=true并配置科大讯飞API密钥。');
          setState(prev => ({ 
            ...prev, 
            error: '语音功能未启用。请联系管理员配置语音服务。'
          }));
          return;
        }
        
        // 从环境变量或配置中获取科大讯飞配置
        const config = {
          appId: import.meta.env.VITE_XUNFEI_APP_ID || '',
          apiKey: import.meta.env.VITE_XUNFEI_API_KEY || '',
          apiSecret: import.meta.env.VITE_XUNFEI_API_SECRET || '',
          language: 'zh_cn',
          accent: 'mandarin'
        };
        
        // 检查配置是否完整
        if (!config.appId || !config.apiKey || !config.apiSecret) {
          console.warn('科大讯飞配置不完整。请在.env文件中配置VITE_XUNFEI_*环境变量。');
          setState(prev => ({ 
            ...prev, 
            error: '语音服务配置不完整。请配置科大讯飞API密钥。'
          }));
          return;
        }

        voiceServiceRef.current = new VoiceService(config);
        await voiceServiceRef.current.initialize();

        // 设置事件监听
        voiceServiceRef.current.onRecognitionResult((result) => {
          setCurrentText(result.text);
          setResults(prev => [...prev, result]);
          onResult?.(result);

          // 解析命令
          if (result.isFinal) {
            const command = voiceServiceRef.current!.parseCommand(result.text);
            onCommand?.(command);
          }
        });

        voiceServiceRef.current.onRecognitionError((error) => {
          setState(prev => ({ ...prev, error }));
          onError?.(error);
        });

        if (autoStart) {
          startRecording();
        }
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
    };
  }, []);

  // 开始录音
  const startRecording = useCallback(async () => {
    if (!voiceServiceRef.current || state.isRecording) return;

    try {
      setState(prev => ({ 
        ...prev, 
        isRecording: true, 
        isPaused: false, 
        error: undefined,
        duration: 0
      }));

      startTimeRef.current = Date.now();
      
      // 开始录音
      await voiceServiceRef.current.startRecognition();

      // 开始计时
      intervalRef.current = setInterval(() => {
        setState(prev => ({
          ...prev,
          duration: Date.now() - startTimeRef.current
        }));
      }, 100);

    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        isRecording: false, 
        error: error instanceof Error ? error.message : '开始录音失败' 
      }));
      onError?.(error instanceof Error ? error.message : '开始录音失败');
    }
  }, [state.isRecording, onError]);

  // 停止录音
  const stopRecording = useCallback(async () => {
    if (!voiceServiceRef.current || !state.isRecording) return;

    try {
      await voiceServiceRef.current.stopRecognition();
      
      setState(prev => ({ 
        ...prev, 
        isRecording: false,
        isPaused: false
      }));

      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }

      // 如果不是连续模式，清空结果
      if (!continuous) {
        setResults([]);
        setCurrentText('');
      }

    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : '停止录音失败' 
      }));
      onError?.(error instanceof Error ? error.message : '停止录音失败');
    }
  }, [state.isRecording, continuous, onError]);

  // 暂停录音
  const pauseRecording = useCallback(() => {
    if (!state.isRecording || state.isPaused) return;
    
    setState(prev => ({ ...prev, isPaused: true }));
    
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, [state.isRecording, state.isPaused]);

  // 恢复录音
  const resumeRecording = useCallback(() => {
    if (!state.isRecording || !state.isPaused) return;
    
    setState(prev => ({ ...prev, isPaused: false }));
    
    startTimeRef.current = Date.now() - state.duration;
    intervalRef.current = setInterval(() => {
      setState(prev => ({
        ...prev,
        duration: Date.now() - startTimeRef.current
      }));
    }, 100);
  }, [state.isRecording, state.isPaused, state.duration]);

  // 清空结果
  const clearResults = useCallback(() => {
    setResults([]);
    setCurrentText('');
  }, []);

  // 获取最终文本
  const getFinalText = useCallback(() => {
    return results
      .filter(result => result.isFinal)
      .map(result => result.text)
      .join('');
  }, [results]);

  return {
    state,
    results,
    currentText,
    finalText: getFinalText(),
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    clearResults,
    isInitialized: !!voiceServiceRef.current
  };
}
