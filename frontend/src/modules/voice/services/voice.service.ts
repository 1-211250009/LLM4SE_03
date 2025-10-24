/**
 * 语音服务
 * 集成科大讯飞语音识别和语音合成
 */

import { VoiceConfig, ASRResult, TTSResult, VoiceCommand } from '../types/voice.types';

declare global {
  interface Window {
    IatRecorder: any;
    TtsPlayer: any;
  }
}

class VoiceService {
  private config: VoiceConfig;
  private isInitialized: boolean = false;
  private recorder: any = null;
  private player: any = null;

  constructor(config: VoiceConfig) {
    this.config = config;
  }

  /**
   * 初始化语音服务
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      // 动态加载科大讯飞SDK
      await this.loadXunfeiSDK();
      
      // 初始化语音识别
      this.recorder = new window.IatRecorder({
        appId: this.config.appId,
        apiKey: this.config.apiKey,
        apiSecret: this.config.apiSecret,
        language: this.config.language || 'zh_cn',
        accent: this.config.accent || 'mandarin'
      });

      // 初始化语音合成
      this.player = new window.TtsPlayer({
        appId: this.config.appId,
        apiKey: this.config.apiKey,
        apiSecret: this.config.apiSecret,
        voiceName: this.config.voiceName || 'xiaoyan',
        speed: this.config.speed || 50,
        volume: this.config.volume || 50,
        pitch: this.config.pitch || 50
      });

      this.isInitialized = true;
    } catch (error) {
      console.error('Voice service initialization failed:', error);
      throw new Error('语音服务初始化失败');
    }
  }

  /**
   * 加载科大讯飞SDK
   */
  private async loadXunfeiSDK(): Promise<void> {
    return new Promise((resolve, reject) => {
      // 检查是否已加载
      if (window.IatRecorder && window.TtsPlayer) {
        resolve();
        return;
      }

      // 加载语音识别SDK
      const asrScript = document.createElement('script');
      asrScript.src = 'https://web-voice.iflytek.com/iat_web_sdk.js';
      asrScript.onload = () => {
        // 加载语音合成SDK
        const ttsScript = document.createElement('script');
        ttsScript.src = 'https://web-voice.iflytek.com/tts_web_sdk.js';
        ttsScript.onload = () => resolve();
        ttsScript.onerror = () => reject(new Error('TTS SDK加载失败'));
        document.head.appendChild(ttsScript);
      };
      asrScript.onerror = () => reject(new Error('ASR SDK加载失败'));
      document.head.appendChild(asrScript);
    });
  }

  /**
   * 开始语音识别
   */
  async startRecognition(): Promise<void> {
    if (!this.isInitialized) {
      await this.initialize();
    }

    return new Promise((resolve, reject) => {
      this.recorder.start({
        onStart: () => {
          console.log('语音识别开始');
          resolve();
        },
        onError: (error: any) => {
          console.error('语音识别错误:', error);
          reject(error);
        }
      });
    });
  }

  /**
   * 停止语音识别
   */
  async stopRecognition(): Promise<void> {
    return new Promise((resolve) => {
      this.recorder.stop({
        onStop: () => {
          console.log('语音识别停止');
          resolve();
        }
      });
    });
  }

  /**
   * 监听语音识别结果
   */
  onRecognitionResult(callback: (result: ASRResult) => void): void {
    this.recorder.onResult = (result: any) => {
      callback({
        text: result.text || '',
        confidence: result.confidence || 0,
        isFinal: result.isFinal || false,
        timestamp: Date.now()
      });
    };
  }

  /**
   * 监听语音识别错误
   */
  onRecognitionError(callback: (error: string) => void): void {
    this.recorder.onError = (error: any) => {
      callback(error.message || '语音识别失败');
    };
  }

  /**
   * 语音合成
   */
  async synthesize(text: string): Promise<TTSResult> {
    if (!this.isInitialized) {
      await this.initialize();
    }

    return new Promise((resolve, reject) => {
      this.player.synthesize(text, {
        onSuccess: (audioBlob: Blob) => {
          resolve({
            audioBlob,
            duration: 0, // 需要计算
            text
          });
        },
        onError: (error: any) => {
          reject(error);
        }
      });
    });
  }

  /**
   * 播放语音
   */
  async play(audioBlob: Blob): Promise<void> {
    return new Promise((resolve, reject) => {
      const audio = new Audio();
      audio.src = URL.createObjectURL(audioBlob);
      
      audio.onloadeddata = () => {
        audio.play().then(() => {
          resolve();
        }).catch(reject);
      };
      
      audio.onerror = reject;
    });
  }

  /**
   * 停止播放
   */
  stop(): void {
    if (this.player) {
      this.player.stop();
    }
  }

  /**
   * 解析语音命令
   */
  parseCommand(text: string): VoiceCommand {
    const lowerText = text.toLowerCase();
    
    // 行程规划命令
    if (lowerText.includes('规划') || lowerText.includes('行程') || lowerText.includes('旅游')) {
      return {
        type: 'plan_trip',
        text,
        confidence: 0.9,
        entities: this.extractTripEntities(text)
      };
    }
    
    // 费用记录命令
    if (lowerText.includes('花费') || lowerText.includes('费用') || lowerText.includes('花钱')) {
      return {
        type: 'add_expense',
        text,
        confidence: 0.9,
        entities: this.extractExpenseEntities(text)
      };
    }
    
    // POI搜索命令
    if (lowerText.includes('搜索') || lowerText.includes('查找') || lowerText.includes('附近')) {
      return {
        type: 'search_poi',
        text,
        confidence: 0.9,
        entities: this.extractPOIEntities(text)
      };
    }
    
    // 通用命令
    return {
      type: 'general',
      text,
      confidence: 0.7
    };
  }

  /**
   * 提取行程相关实体
   */
  private extractTripEntities(text: string): Record<string, any> {
    const entities: Record<string, any> = {};
    
    // 提取地点
    const locationRegex = /(?:去|到|在)([^，。！？\s]+)/g;
    const locations = [];
    let match;
    while ((match = locationRegex.exec(text)) !== null) {
      locations.push(match[1]);
    }
    if (locations.length > 0) {
      entities.locations = locations;
    }
    
    // 提取时间
    const timeRegex = /(\d+)(?:天|日)/g;
    const timeMatch = timeRegex.exec(text);
    if (timeMatch) {
      entities.duration = parseInt(timeMatch[1]);
    }
    
    // 提取预算
    const budgetRegex = /(\d+)(?:万|千|元)/g;
    const budgetMatch = budgetRegex.exec(text);
    if (budgetMatch) {
      entities.budget = parseInt(budgetMatch[1]);
    }
    
    return entities;
  }

  /**
   * 提取费用相关实体
   */
  private extractExpenseEntities(text: string): Record<string, any> {
    const entities: Record<string, any> = {};
    
    // 提取金额
    const amountRegex = /(\d+(?:\.\d+)?)(?:元|块|块钱)/g;
    const amountMatch = amountRegex.exec(text);
    if (amountMatch) {
      entities.amount = parseFloat(amountMatch[1]);
    }
    
    // 提取类别
    const categories = ['交通', '住宿', '餐饮', '门票', '购物', '其他'];
    for (const category of categories) {
      if (text.includes(category)) {
        entities.category = category;
        break;
      }
    }
    
    return entities;
  }

  /**
   * 提取POI相关实体
   */
  private extractPOIEntities(text: string): Record<string, any> {
    const entities: Record<string, any> = {};
    
    // 提取关键词
    const keywordRegex = /(?:搜索|查找|附近)([^，。！？\s]+)/g;
    const keywordMatch = keywordRegex.exec(text);
    if (keywordMatch) {
      entities.keyword = keywordMatch[1];
    }
    
    // 提取类别
    const categories = ['景点', '餐厅', '酒店', '商场', '医院', '银行'];
    for (const category of categories) {
      if (text.includes(category)) {
        entities.category = category;
        break;
      }
    }
    
    return entities;
  }

  /**
   * 销毁服务
   */
  destroy(): void {
    if (this.recorder) {
      this.recorder.destroy();
    }
    if (this.player) {
      this.player.destroy();
    }
    this.isInitialized = false;
  }
}

export default VoiceService;
