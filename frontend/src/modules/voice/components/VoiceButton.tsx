/**
 * 语音按钮组件
 */

import React, { useState, useRef, useEffect } from 'react';
import { Button, Tooltip, message } from 'antd';
import { 
  AudioOutlined, 
  StopOutlined, 
  PauseOutlined, 
  PlayCircleOutlined 
} from '@ant-design/icons';
import { useVoiceInput } from '../hooks/useVoiceInput';
import { VoiceCommand } from '../types/voice.types';
import './VoiceButton.css';

interface VoiceButtonProps {
  onResult?: (text: string) => void;
  onCommand?: (command: VoiceCommand) => void;
  onError?: (error: string) => void;
  disabled?: boolean;
  size?: 'small' | 'middle' | 'large';
  type?: 'primary' | 'default' | 'dashed' | 'link' | 'text';
  continuous?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

const VoiceButton: React.FC<VoiceButtonProps> = ({
  onResult,
  onCommand,
  onError,
  disabled = false,
  size = 'middle',
  type = 'primary',
  continuous = false,
  className = '',
  style
}) => {
  const [isPressed, setIsPressed] = useState(false);
  const [showWave, setShowWave] = useState(false);
  const waveRef = useRef<HTMLDivElement>(null);

  const {
    state,
    currentText,
    finalText,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    clearResults,
    isInitialized
  } = useVoiceInput({
    onResult: (result) => {
      onResult?.(result.text);
    },
    onCommand: (command) => {
      onCommand?.(command);
    },
    onError: (error) => {
      message.error(error);
      onError?.(error);
    },
    continuous
  });

  // 处理鼠标按下
  const handleMouseDown = () => {
    if (disabled || !isInitialized || state.isRecording) return;
    
    setIsPressed(true);
    setShowWave(true);
    startRecording();
  };

  // 处理鼠标释放
  const handleMouseUp = () => {
    if (!isPressed) return;
    
    setIsPressed(false);
    setShowWave(false);
    stopRecording();
  };

  // 处理鼠标离开
  const handleMouseLeave = () => {
    if (isPressed) {
      handleMouseUp();
    }
  };

  // 处理点击（用于暂停/恢复）
  const handleClick = () => {
    if (disabled || !isInitialized) return;

    if (state.isRecording) {
      if (state.isPaused) {
        resumeRecording();
      } else {
        pauseRecording();
      }
    } else {
      // 如果不在录音，开始录音
      handleMouseDown();
    }
  };

  // 生成波形动画
  useEffect(() => {
    if (!showWave || !waveRef.current) return;

    const waveContainer = waveRef.current;
    const bars = waveContainer.querySelectorAll('.voice-wave-bar');
    
    const animate = () => {
      bars.forEach((bar, index) => {
        const height = Math.random() * 100;
        (bar as HTMLElement).style.height = `${height}%`;
      });
    };

    const interval = setInterval(animate, 100);
    return () => clearInterval(interval);
  }, [showWave]);

  // 获取按钮状态
  const getButtonState = () => {
    if (state.error) return 'error';
    if (state.isRecording) {
      return state.isPaused ? 'paused' : 'recording';
    }
    return 'idle';
  };

  // 获取按钮图标
  const getButtonIcon = () => {
    const state = getButtonState();
    switch (state) {
      case 'recording':
        return <StopOutlined />;
      case 'paused':
        return <PlayCircleOutlined />;
      case 'error':
        return <AudioOutlined />;
      default:
        return <AudioOutlined />;
    }
  };

  // 获取按钮文本
  const getButtonText = () => {
    const state = getButtonState();
    switch (state) {
      case 'recording':
        return '录音中...';
      case 'paused':
        return '已暂停';
      case 'error':
        return '语音识别';
      default:
        return '按住说话';
    }
  };

  // 获取按钮类型
  const getButtonType = () => {
    const state = getButtonState();
    switch (state) {
      case 'recording':
        return 'primary';
      case 'paused':
        return 'default';
      case 'error':
        return 'dashed';
      default:
        return type;
    }
  };

  const buttonState = getButtonState();
  const isDisabled = disabled || !isInitialized || state.error;

  return (
    <div className={`voice-button-container ${className}`} style={style}>
      <Tooltip title={isInitialized ? '按住说话或点击录音' : '语音服务未初始化'}>
        <Button
          type={getButtonType() as any}
          size={size}
          disabled={isDisabled}
          onMouseDown={handleMouseDown}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseLeave}
          onClick={handleClick}
          className={`voice-button ${buttonState} ${isPressed ? 'pressed' : ''}`}
          icon={getButtonIcon()}
        >
          {getButtonText()}
        </Button>
      </Tooltip>

      {/* 波形动画 */}
      {showWave && (
        <div ref={waveRef} className="voice-wave">
          {Array.from({ length: 5 }, (_, i) => (
            <div key={i} className="voice-wave-bar" />
          ))}
        </div>
      )}

      {/* 识别结果显示 */}
      {currentText && (
        <div className="voice-result">
          <div className="voice-result-text">
            {currentText}
          </div>
          {finalText && (
            <div className="voice-final-text">
              最终结果: {finalText}
            </div>
          )}
        </div>
      )}

      {/* 错误提示 */}
      {state.error && (
        <div className="voice-error">
          {state.error}
        </div>
      )}
    </div>
  );
};

export default VoiceButton;
