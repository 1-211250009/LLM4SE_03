/**
 * 简单的语音识别Hook
 * 使用浏览器MediaRecorder API录制音频，调用后端API进行识别
 */

import { useState, useCallback, useRef } from 'react';
import { message } from 'antd';
import { useAuthStore } from '../store/auth.store';

interface UseSpeechRecognitionOptions {
  onResult?: (text: string) => void;
  onError?: (error: string) => void;
}

export function useSpeechRecognition(options: UseSpeechRecognitionOptions = {}) {
  const { onResult, onError } = options;
  const { accessToken } = useAuthStore();
  
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  // 开始录音
  const startRecording = useCallback(async () => {
    try {
      // 请求麦克风权限
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // 创建MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      // 收集音频数据
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      // 开始录制
      mediaRecorder.start();
      setIsRecording(true);
    } catch (error: any) {
      const errorMessage = error.message || '无法访问麦克风，请检查权限设置';
      message.error(errorMessage);
      onError?.(errorMessage);
      console.error('Start recording error:', error);
    }
  }, [onError]);

  // 停止录音并识别
  const stopRecording = useCallback(async () => {
    if (!mediaRecorderRef.current || !isRecording) {
      return;
    }

    return new Promise<void>((resolve) => {
      mediaRecorderRef.current!.onstop = async () => {
        setIsRecording(false);
        setIsProcessing(true);

        // 停止媒体流
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }

        try {
          // 将音频块合并为Blob
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          
          // 创建FormData
          const formData = new FormData();
          formData.append('audio_file', audioBlob, 'recording.webm');
          formData.append('language', 'zh_cn');

          // 调用后端API进行语音识别
          const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
          
          if (!accessToken) {
            throw new Error('未登录，请先登录');
          }
          
          const response = await fetch(`${baseUrl}/api/v1/voice/asr`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${accessToken}`
            },
            body: formData
          });

          if (!response.ok) {
            throw new Error('语音识别失败');
          }

          const data = await response.json();
          
          if (data.success && data.text) {
            onResult?.(data.text);
            message.success('语音识别成功');
          } else {
            throw new Error(data.detail || '识别结果为空');
          }
        } catch (error: any) {
          const errorMessage = error.message || '语音识别失败，请重试';
          message.error(errorMessage);
          onError?.(errorMessage);
          console.error('Speech recognition error:', error);
        } finally {
          setIsProcessing(false);
          audioChunksRef.current = [];
          resolve();
        }
      };

      // 停止录制
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
      }
    });
  }, [isRecording, onResult, onError]);

  // 切换录音状态
  const toggleRecording = useCallback(async () => {
    if (isRecording) {
      await stopRecording();
    } else {
      await startRecording();
    }
  }, [isRecording, startRecording, stopRecording]);

  return {
    isRecording,
    isProcessing,
    startRecording,
    stopRecording,
    toggleRecording
  };
}

