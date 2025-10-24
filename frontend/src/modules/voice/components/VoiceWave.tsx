/**
 * 语音波形组件
 */

import React, { useEffect, useRef, useState } from 'react';
import './VoiceWave.css';

interface VoiceWaveProps {
  isActive: boolean;
  volume?: number;
  frequency?: number;
  size?: 'small' | 'medium' | 'large';
  color?: string;
  className?: string;
  style?: React.CSSProperties;
}

const VoiceWave: React.FC<VoiceWaveProps> = ({
  isActive,
  volume = 0.5,
  frequency = 0.1,
  size = 'medium',
  color = '#1890ff',
  className = '',
  style
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  // 更新画布尺寸
  useEffect(() => {
    const updateDimensions = () => {
      if (canvasRef.current) {
        const rect = canvasRef.current.getBoundingClientRect();
        setDimensions({ width: rect.width, height: rect.height });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // 绘制波形
  useEffect(() => {
    if (!isActive || !canvasRef.current || dimensions.width === 0) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = dimensions.width * window.devicePixelRatio;
    canvas.height = dimensions.height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    let time = 0;
    const bars = 20;
    const barWidth = dimensions.width / bars;
    const maxHeight = dimensions.height * 0.8;

    const draw = () => {
      ctx.clearRect(0, 0, dimensions.width, dimensions.height);
      
      for (let i = 0; i < bars; i++) {
        const x = i * barWidth + barWidth / 2;
        const barHeight = Math.sin(time + i * frequency) * volume * maxHeight;
        const height = Math.abs(barHeight);
        
        // 创建渐变
        const gradient = ctx.createLinearGradient(0, dimensions.height, 0, dimensions.height - height);
        gradient.addColorStop(0, color);
        gradient.addColorStop(1, `${color}80`);
        
        ctx.fillStyle = gradient;
        ctx.fillRect(
          x - barWidth / 4,
          dimensions.height - height,
          barWidth / 2,
          height
        );
      }
      
      time += 0.1;
      animationRef.current = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isActive, volume, frequency, dimensions, color]);

  const getSizeClass = () => {
    switch (size) {
      case 'small':
        return 'voice-wave-small';
      case 'large':
        return 'voice-wave-large';
      default:
        return 'voice-wave-medium';
    }
  };

  return (
    <div 
      className={`voice-wave-container ${getSizeClass()} ${className}`}
      style={style}
    >
      <canvas
        ref={canvasRef}
        className="voice-wave-canvas"
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
};

export default VoiceWave;
