/**
 * AI创建行程助手组件
 * 通过对话方式收集行程信息并创建行程
 */

import React, { useState, useCallback, useRef } from 'react';
import { Modal, Input, Button, Card, Space, Typography, message } from 'antd';
import { RobotOutlined, SendOutlined, AudioOutlined } from '@ant-design/icons';
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition';
import { ApiService } from '../../services/api.service';
import MarkdownRenderer from '../common/MarkdownRenderer';

const { Text } = Typography;

interface TripAIAssistantProps {
  onTripCreated?: (tripId: string) => void;
}

interface AIMessage {
  role: 'user' | 'assistant';
  content: string;
  pendingAction?: {
    id?: string;
    function_name: string;
    arguments: string; // JSON字符串
  };
}

interface AIQueryResponse {
  response: string;
  action_performed: boolean;
  pending_action?: {
    id?: string;
    function_name: string;
    arguments: string;
  };
}

const TripAIAssistant: React.FC<TripAIAssistantProps> = ({ onTripCreated }) => {
  const [visible, setVisible] = useState(false);
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const requestInProgressRef = useRef(false); // 防止重复请求
  
  // 语音识别
  const { isRecording, isProcessing, toggleRecording } = useSpeechRecognition({
    onResult: (text) => {
      setInput(prev => prev + (prev ? ' ' : '') + text);
    },
    onError: (error) => {
      console.error('Speech recognition error:', error);
    }
  });

  // 发送AI查询的通用函数
  const sendAIQuery = useCallback(async (query: string, conversationHistory: Array<{role: string, content: string}>) => {
    // 防止重复请求
    if (requestInProgressRef.current) {
      console.warn('已有请求在处理中，忽略重复请求');
      return;
    }

    requestInProgressRef.current = true;
    setLoading(true);

    try {
      console.log('发送AI查询:', { query, historyLength: conversationHistory.length });

      const data = await ApiService.post<AIQueryResponse>('/trips/ai/query', {
        query: query,
        conversation_history: conversationHistory
      }, {
        timeout: 60000
      });

      if (!data) {
        throw new Error('AI响应格式错误');
      }

      // 添加助手回复
      if (data.pending_action) {
        const content = data.response || '我已经收集到所有必要信息，准备为您创建行程。请确认以下信息：';
        setMessages(prev => [...prev, { 
          role: 'assistant' as const, 
          content: content,
          pendingAction: data.pending_action
        }]);
      } else {
        if (!data.response || data.response.trim() === '') {
          throw new Error('AI响应内容为空');
        }
        setMessages(prev => [...prev, { 
          role: 'assistant' as const, 
          content: data.response 
        }]);
      }
    } catch (error: any) {
      console.error('AI query failed:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'AI查询失败';
      message.error(errorMessage);
      setMessages(prev => [...prev, { 
        role: 'assistant' as const, 
        content: errorMessage || '抱歉，AI助手暂时无法响应，请稍后再试。' 
      }]);
    } finally {
      setLoading(false);
      requestInProgressRef.current = false;
    }
  }, []);

  // 用户发送查询
  const handleQuery = useCallback(async (query?: string) => {
    const userMessage = query || input.trim();
    if (!userMessage) return;

    // 防止重复请求
    if (loading || requestInProgressRef.current) {
      console.warn('已有请求在处理中，忽略重复请求');
      return;
    }

    const currentInput = userMessage;
    setInput('');

    // 添加用户消息
    setMessages(prev => {
      const newMessages = [...prev, { role: 'user' as const, content: currentInput }];
      
      // 构建对话历史（只包含role和content，排除pendingAction）
      const conversationHistory = prev
        .filter(msg => !msg.pendingAction)
        .map(msg => ({
          role: msg.role,
          content: msg.content
        }));

      // 发送AI查询
      sendAIQuery(currentInput, conversationHistory);
      
      return newMessages;
    });
  }, [input, loading, sendAIQuery]);

  // 打开助手
  const handleOpen = useCallback(() => {
    setVisible(true);
    setMessages([]);
    setInput('');
    requestInProgressRef.current = false;
    
    // 发送初始问候（延迟确保状态已更新）
    setTimeout(() => {
      if (!requestInProgressRef.current) {
        const initialMessage = '你好，我想创建一个新的行程';
        setMessages([{ role: 'user' as const, content: initialMessage }]);
        sendAIQuery(initialMessage, []);
      }
    }, 100);
  }, [sendAIQuery]);

  // 关闭助手
  const handleClose = useCallback(() => {
    setVisible(false);
    setMessages([]);
    setInput('');
    requestInProgressRef.current = false;
  }, []);

  // 执行待确认的操作
  const handleExecuteAction = useCallback(async (action: any) => {
    if (requestInProgressRef.current) {
      console.warn('已有请求在处理中，忽略重复请求');
      return;
    }

    requestInProgressRef.current = true;
    setLoading(true);
    
    try {
      const result = await ApiService.post<{success: boolean, message: string, data?: any}>('/trips/ai/execute', {
        function_name: action.function_name,
        arguments: action.arguments
      }, {
        timeout: 60000
      });

      message.success(result.message || '操作执行成功');
      
      // 更新消息，移除待确认操作
      setMessages(prev => prev.map((msg) => {
        if (msg.pendingAction && msg.pendingAction.id === action.id) {
          return {
            ...msg,
            pendingAction: undefined,
            content: msg.content + '\n\n✅ ' + (result.message || '行程创建成功')
          };
        }
        return msg;
      }));

      // 如果创建成功，调用回调
      if (result.data && result.data.id && onTripCreated) {
        onTripCreated(result.data.id);
      }

      // 关闭对话框
      setTimeout(() => {
        handleClose();
      }, 1500);
    } catch (error: any) {
      console.error('Execute action failed:', error);
      const errorMessage = error.response?.data?.detail || error.message || '执行操作失败';
      message.error(errorMessage);
    } finally {
      setLoading(false);
      requestInProgressRef.current = false;
    }
  }, [onTripCreated, handleClose]);

  // 取消操作
  const handleCancelAction = useCallback((index: number) => {
    setMessages(prev => prev.map((msg, idx) => {
      if (idx === index && msg.pendingAction) {
        return {
          ...msg,
          pendingAction: undefined,
          content: msg.content + '\n\n❌ 操作已取消'
        };
      }
      return msg;
    }));
  }, []);

  // 格式化操作详情
  const formatActionDetails = (action: any) => {
    try {
      const args = JSON.parse(action.arguments);
      const details: string[] = [];
      
      if (args.title) details.push(`标题: ${args.title}`);
      if (args.destination) details.push(`目的地: ${args.destination}`);
      if (args.start_date) details.push(`开始日期: ${args.start_date}`);
      if (args.end_date) details.push(`结束日期: ${args.end_date}`);
      if (args.duration_days) details.push(`行程天数: ${args.duration_days}天`);
      if (args.budget_total) details.push(`总预算: ¥${args.budget_total}`);
      if (args.traveler_count) details.push(`同行人数: ${args.traveler_count}人`);
      if (args.currency) details.push(`货币单位: ${args.currency}`);
      if (args.status) details.push(`状态: ${args.status}`);
      if (args.tags && args.tags.length > 0) details.push(`标签: ${args.tags.join(', ')}`);
      if (args.description) details.push(`描述: ${args.description}`);
      
      return details.join('\n');
    } catch (e) {
      return action.arguments;
    }
  };

  return (
    <>
      <Button
        type="primary"
        icon={<RobotOutlined />}
        onClick={handleOpen}
        size="middle"
      >
        AI创建行程助手
      </Button>

      <Modal
        title={
          <Space>
            <RobotOutlined />
            <span>AI创建行程助手</span>
          </Space>
        }
        open={visible}
        onCancel={handleClose}
        footer={null}
        width={800}
        style={{ top: 20 }}
      >
        <div style={{ 
          display: 'flex', 
          flexDirection: 'column', 
          height: '600px',
          maxHeight: '70vh'
        }}>
          {/* 聊天区域 */}
          <div style={{ 
            flex: 1, 
            overflowY: 'auto', 
            padding: '16px',
            background: '#f5f5f5',
            borderRadius: '8px',
            marginBottom: '16px'
          }}>
            {messages.length === 0 ? (
              <div style={{ textAlign: 'center', color: '#999', padding: '40px' }}>
                <RobotOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                <Text type="secondary">开始对话，我将帮助您创建行程</Text>
              </div>
            ) : (
              messages.map((msg, index) => (
                <div key={index} style={{ marginBottom: '16px' }}>
                  <div style={{ 
                    fontWeight: 'bold', 
                    marginBottom: '4px',
                    color: msg.role === 'user' ? '#1890ff' : '#52c41a'
                  }}>
                    {msg.role === 'user' ? '您' : 'AI助手'}
                  </div>
                  <div style={{ 
                    background: msg.role === 'user' ? '#e6f7ff' : '#f6ffed',
                    padding: '12px',
                    borderRadius: '6px',
                    border: `1px solid ${msg.role === 'user' ? '#91d5ff' : '#b7eb8f'}`
                  }}>
                    <MarkdownRenderer content={msg.content} />
                    
                    {/* 待确认的操作卡片 */}
                    {msg.pendingAction && (
                      <Card 
                        size="small" 
                        style={{ 
                          marginTop: '12px', 
                          border: '1px solid #ffa940',
                          background: '#fff7e6'
                        }}
                        title={
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span style={{ color: '#fa8c16' }}>⚠️ 待确认操作</span>
                          </div>
                        }
                      >
                        <div style={{ marginBottom: '12px' }}>
                          <Text strong>操作类型：</Text>
                          <Text>创建行程</Text>
                        </div>
                        <div style={{ marginBottom: '12px' }}>
                          <Text strong>行程信息：</Text>
                          <div style={{ 
                            marginTop: '8px', 
                            padding: '8px', 
                            background: '#fff', 
                            borderRadius: '4px',
                            fontFamily: 'monospace',
                            fontSize: '12px',
                            whiteSpace: 'pre-wrap'
                          }}>
                            {formatActionDetails(msg.pendingAction)}
                          </div>
                        </div>
                        <Space>
                          <Button 
                            type="primary" 
                            size="small"
                            onClick={() => handleExecuteAction(msg.pendingAction)}
                            loading={loading}
                          >
                            确认创建
                          </Button>
                          <Button 
                            size="small"
                            onClick={() => handleCancelAction(index)}
                          >
                            取消
                          </Button>
                        </Space>
                      </Card>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* 输入区域 */}
          <div style={{ display: 'flex', gap: '8px' }}>
            <div style={{ flex: 1, position: 'relative' }}>
              <Input.TextArea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onPressEnter={(e) => {
                  if (e.shiftKey) return; // Shift+Enter 换行
                  e.preventDefault();
                  handleQuery();
                }}
                placeholder="输入您的问题，例如：我想创建一个去北京的行程..."
                rows={3}
                disabled={loading || isProcessing}
                style={{ paddingRight: '40px' }}
              />
              <Button
                type="text"
                icon={<AudioOutlined />}
                onClick={toggleRecording}
                loading={isProcessing}
                danger={isRecording}
                style={{
                  position: 'absolute',
                  right: '4px',
                  bottom: '4px',
                  border: 'none',
                  padding: '4px 8px'
                }}
              />
            </div>
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={() => handleQuery()}
              loading={loading}
              disabled={!input.trim() || loading || isProcessing}
              style={{ alignSelf: 'flex-end' }}
            >
              发送
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
};

export default TripAIAssistant;
