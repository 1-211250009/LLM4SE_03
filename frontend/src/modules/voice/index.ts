/**
 * 语音模块导出
 */

// 类型
export * from './types/voice.types';

// 服务
export { default as VoiceService } from './services/voice.service';

// Hooks
export { useVoiceInput } from './hooks/useVoiceInput';
export { useVoiceOutput } from './hooks/useVoiceOutput';

// 组件
export { default as VoiceButton } from './components/VoiceButton';
export { default as VoiceWave } from './components/VoiceWave';
