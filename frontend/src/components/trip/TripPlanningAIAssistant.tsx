/**
 * AI行程规划助手组件
 * 通过对话方式帮助用户管理行程节点（添加、修改、删除）
 */

import React, { useState, useCallback, useRef } from 'react';
import { Modal, Input, Button, Card, Space, Typography, message } from 'antd';
import { RobotOutlined, SendOutlined, AudioOutlined } from '@ant-design/icons';
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition';
import { ApiService } from '../../services/api.service';
import MarkdownRenderer from '../common/MarkdownRenderer';

const { Text } = Typography;

interface TripPlanningAIAssistantProps {
  tripId: string;
  onItemChanged?: () => void; // 当节点发生变化时调用，用于刷新数据
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

const TripPlanningAIAssistant: React.FC<TripPlanningAIAssistantProps> = ({ tripId, onItemChanged }) => {
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

      const data = await ApiService.post<AIQueryResponse>(`/trips/${tripId}/planning/ai/query`, {
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
        const content = data.response || '我准备执行以下操作，请确认：';
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
  }, [tripId]);

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
        const initialMessage = '你好，我想管理我的行程节点';
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
      const result = await ApiService.post<{success: boolean, message: string, data?: any}>(`/trips/${tripId}/planning/ai/execute`, {
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
            content: msg.content + '\n\n✅ ' + (result.message || '操作成功')
          };
        }
        return msg;
      }));

      // 刷新行程数据
      if (onItemChanged) {
        onItemChanged();
      }
    } catch (error: any) {
      console.error('Execute action failed:', error);
      const errorMessage = error.response?.data?.detail || error.message || '执行操作失败';
      message.error(errorMessage);
    } finally {
      setLoading(false);
      requestInProgressRef.current = false;
    }
  }, [tripId, onItemChanged]);

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
      
      if (action.function_name === 'add_itinerary_item') {
        details.push('操作类型：添加行程节点');
        if (args.name) details.push(`节点名称：${args.name}`);
        if (args.description) details.push(`描述：${args.description}`);
        if (args.address) details.push(`地址：${args.address}`);
        if (args.category) details.push(`分类：${args.category}`);
        if (args.start_time) details.push(`开始时间：${args.start_time}`);
        if (args.end_time) details.push(`结束时间：${args.end_time}`);
        if (args.estimated_duration) details.push(`预计时长：${args.estimated_duration}分钟`);
        if (args.estimated_cost) details.push(`预计费用：¥${args.estimated_cost}`);
        if (args.itinerary_id) details.push(`行程安排ID：${args.itinerary_id}`);
      } else if (action.function_name === 'update_itinerary_item') {
        details.push('操作类型：更新行程节点');
        if (args.item_id) details.push(`节点ID：${args.item_id}`);
        if (args.name) details.push(`新名称：${args.name}`);
        if (args.description) details.push(`新描述：${args.description}`);
        if (args.address) details.push(`新地址：${args.address}`);
        if (args.category) details.push(`新分类：${args.category}`);
        if (args.start_time) details.push(`新开始时间：${args.start_time}`);
        if (args.end_time) details.push(`新结束时间：${args.end_time}`);
        if (args.itinerary_id) details.push(`行程安排ID：${args.itinerary_id}`);
      } else if (action.function_name === 'delete_itinerary_item') {
        details.push('操作类型：删除行程节点');
        if (args.item_id) details.push(`节点ID：${args.item_id}`);
        if (args.itinerary_id) details.push(`行程安排ID：${args.itinerary_id}`);
      }
      
      return details.join('\n');
    } catch (e) {
      return action.arguments;
    }
  };

  // 获取操作类型名称
  const getActionTypeName = (functionName: string) => {
    const names: Record<string, string> = {
      'add_itinerary_item': '添加行程节点',
      'update_itinerary_item': '更新行程节点',
      'delete_itinerary_item': '删除行程节点'
    };
    return names[functionName] || '未知操作';
  };

  return (
    <>
      <Button
        type="default"
        icon={<RobotOutlined />}
        onClick={handleOpen}
        size="small"
      >
        AI行程规划助手
      </Button>

      <Modal
        title={
          <Space>
            <RobotOutlined />
            <span>AI行程规划助手</span>
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
                <Text type="secondary">开始对话，我将帮助您管理行程节点</Text>
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
                          <Text>{getActionTypeName(msg.pendingAction.function_name)}</Text>
                        </div>
                        <div style={{ marginBottom: '12px' }}>
                          <Text strong>操作详情：</Text>
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
                            确认执行
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
                placeholder="输入您的问题，例如：在第1天添加一个景点..."
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

export default TripPlanningAIAssistant;

