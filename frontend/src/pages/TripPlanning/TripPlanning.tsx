import React, { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import { useOutletContext } from 'react-router-dom';
import { 
  Typography, 
  Input, 
  Button, 
  Space, 
  message,
  Spin,
  Alert,
  Tag,
  Card,
  Checkbox
} from 'antd';
import { 
  SendOutlined, 
  RobotOutlined, 
  CloseOutlined
} from '@ant-design/icons';
import { useAuthStore } from '../../store/auth.store';
import { AGUIClient, AGUIEventHandler, AGUIEvent } from '../../utils/agui-client';
import MarkdownRenderer from '../../components/common/MarkdownRenderer';
import { MapContainer } from '../../modules/map';
import { MapConfig, MapMarker, POIInfo, Point, MarkerSelection, RouteInfo } from '../../modules/map/types/map.types';
import { useRouteCalc } from '../../modules/map/hooks/useRouteCalc';

const { Text } = Typography;
const { TextArea } = Input;

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  isStreaming?: boolean;
}

const TripPlanning = () => {
  const { accessToken } = useAuthStore();
  const { isChatOpen, setIsChatOpen } = useOutletContext<{
    isChatOpen: boolean;
    setIsChatOpen: (open: boolean) => void;
  }>();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [systemMessage, setSystemMessage] = useState<string | null>(null);
  const [toolCalls, setToolCalls] = useState<Array<{id: string, name: string, status: 'calling' | 'success' | 'error', result?: any}>>([]);
  const [hasToolCalls, setHasToolCalls] = useState(false);
  const [pendingMessage, setPendingMessage] = useState<string>('');
  
  // 地图相关状态
  const [mapMarkers, setMapMarkers] = useState<MapMarker[]>([]);
  const [currentRoutes, setCurrentRoutes] = useState<RouteInfo[]>([]);
  
  // 路线计算Hook
  const { calculateRoute, clearRoutes } = useRouteCalc();
  
  // 行程相关状态 - 暂时注释掉，后续可能会用到
  // const [currentTrip, setCurrentTrip] = useState<TripInfo | null>(null);
  // const [tripSteps, setTripSteps] = useState<TripStep[]>([]);
  
  // 标记选择相关状态
  const [selectedMarkers, setSelectedMarkers] = useState<MarkerSelection[]>([]);
  const [showMarkerSelector, setShowMarkerSelector] = useState(false);
  
  // 行程规划相关状态
  const [currentTripPlan, setCurrentTripPlan] = useState<{
    title?: string;
    duration?: string;
    transport_mode?: string;
    locations?: string[];
    schedule?: Array<{
      time: string;
      location: string;
      activity: string;
      duration: string;
    }>;
    routes?: Array<{
      from: string;
      to: string;
      transport: string;
      estimated_time: string;
    }>;
    tips?: string[];
  } | null>(null);
  const [showTripPlanCard, setShowTripPlanCard] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const aguiClientRef = useRef<AGUIClient | null>(null);
  const eventHandlerRef = useRef<AGUIEventHandler | null>(null);

  // 滚动到底部的函数
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  // 当消息变化时自动滚动到底部
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // 地图配置 - 使用useMemo避免重复创建
  const mapConfig: MapConfig = useMemo(() => ({
    center: { lat: 39.9042, lng: 116.4074 }, // 北京天安门
    zoom: 12,
    enableScrollWheelZoom: true,
    enableDragging: true,
    enableDoubleClickZoom: true,
    enableKeyboard: true,
    enableInertialDragging: true,
    enableContinuousZoom: true,
    enablePinchToZoom: true
  }), []);


  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 初始化事件处理器 - 只创建一次
  useEffect(() => {
    if (!eventHandlerRef.current) {
      console.log('DEBUG: Creating new AGUIEventHandler');
      eventHandlerRef.current = new AGUIEventHandler();
      
      // 设置事件处理器
      eventHandlerRef.current.setOnTextDelta((delta: string, messageId: string) => {
        console.log('DEBUG: setOnTextDelta called', { delta, messageId });
        
        // 如果有工具调用，先累积消息内容
        if (hasToolCalls) {
          setPendingMessage(prev => prev + delta);
          return;
        }
        
        setMessages(prev => {
          // 查找是否已存在相同ID的流式消息
          const existingMessageIndex = prev.findIndex(msg => 
            msg.role === 'assistant' && msg.isStreaming && msg.id === messageId
          );
          
          console.log('DEBUG: existingMessageIndex', existingMessageIndex, 'prev messages count', prev.length);
          
          if (existingMessageIndex !== -1) {
            // 更新现有消息
            const newMessages = [...prev];
            newMessages[existingMessageIndex] = {
              ...newMessages[existingMessageIndex],
              content: newMessages[existingMessageIndex].content + delta
            };
            console.log('DEBUG: updating existing message');
            return newMessages;
          } else {
            // 创建新消息
            console.log('DEBUG: creating new message');
            return [...prev, {
              id: messageId,
              role: 'assistant',
              content: delta,
              timestamp: Date.now(),
              isStreaming: true
            }];
          }
        });
      });

      eventHandlerRef.current.setOnTextContent((content: string, messageId: string) => {
        console.log('DEBUG: setOnTextContent called', { content, messageId });
        
        setMessages(prev => {
          // 查找是否已存在相同ID的消息
          const existingMessageIndex = prev.findIndex(msg => 
            msg.role === 'assistant' && msg.id === messageId
          );
          
          if (existingMessageIndex !== -1) {
            // 更新现有消息
            const newMessages = [...prev];
            newMessages[existingMessageIndex] = {
              ...newMessages[existingMessageIndex],
              content: content,
              isStreaming: false
            };
            console.log('DEBUG: updating existing message with content');
            return newMessages;
          } else {
            // 创建新消息
            console.log('DEBUG: creating new message with content');
            return [...prev, {
              id: messageId,
              role: 'assistant',
              content: content,
              timestamp: Date.now(),
              isStreaming: false
            }];
          }
        });
      });

      eventHandlerRef.current.setOnRunStarted((_runId: string, _agentId: string) => {
        setIsLoading(true);
        setError(null);
        // 清空工具调用状态
        setToolCalls([]);
        setHasToolCalls(false);
        setPendingMessage('');
        // 清空所有流式消息，确保新的对话从干净状态开始
        setMessages(prev => prev.filter(msg => !msg.isStreaming));
        console.log('DEBUG: Run started, cleared streaming messages');
      });

      eventHandlerRef.current.setOnRunFinished((_runId: string, _result: any) => {
        console.log('DEBUG: setOnRunFinished called');
        setIsLoading(false);
        setMessages(prev => {
          // 将所有流式消息标记为完成
          const newMessages = prev.map(msg => 
            msg.role === 'assistant' && msg.isStreaming 
              ? { ...msg, isStreaming: false }
              : msg
          );
          console.log('DEBUG: marked streaming messages as finished');
          return newMessages;
        });
      });

      eventHandlerRef.current.setOnRunError((_runId: string, error: string) => {
        setIsLoading(false);
        setError(error);
        message.error(`对话失败: ${error}`);
      });

      eventHandlerRef.current.setOnSystemMessage((msg: string, level: string) => {
        // 显示系统消息
        setSystemMessage(msg);
        
        // 3秒后清除系统消息
        setTimeout(() => {
          setSystemMessage(null);
        }, 3000);
        
        // 同时在控制台显示
        if (level === 'info') {
          message.info(msg);
        } else if (level === 'warning') {
          message.warning(msg);
        } else if (level === 'error') {
          message.error(msg);
        } else {
          message.info(msg);
        }
      });

      eventHandlerRef.current.setOnToolCallRequest((callId: string, toolName: string, parameters: any) => {
        console.log('Tool call request:', callId, toolName, parameters);
        
        // 设置有工具调用状态
        setHasToolCalls(true);
        
        // 添加工具调用状态
        setToolCalls(prev => [...prev, {
          id: callId,
          name: toolName,
          status: 'calling'
        }]);
      });

      eventHandlerRef.current.setOnToolCallResult((callId: string, result: any) => {
        console.log('Tool call result:', callId, result);
        
        // 更新工具调用状态
        setToolCalls(prev => prev.map(tool => 
          tool.id === callId 
            ? { ...tool, status: result?.success ? 'success' : 'error', result }
            : tool
        ));
        
        // 如果工具调用返回POI数据，自动在地图上显示
        if (result && result.success && result.data && result.data.pois) {
          result.data.pois.forEach((poi: POIInfo) => {
            handlePOISelect(poi);
          });
        }
        
        // 如果工具调用返回标记地点数据，添加到地图和选择列表
        if (result && result.success && result.data && result.data.marker_id) {
          const markerData = result.data;
          const marker: MapMarker = {
            id: markerData.marker_id,
            position: markerData.coordinates,
            title: markerData.label,
            content: `
              <div style="padding: 8px;">
                <h4 style="margin: 0 0 4px 0; font-size: 14px;">${markerData.label}</h4>
                <p style="margin: 0; font-size: 12px; color: #666;">${markerData.location}</p>
                <p style="margin: 4px 0 0 0; font-size: 12px; color: #1890ff;">📍 ${markerData.category}</p>
              </div>
            `,
            poi: {
              id: markerData.marker_id,
              name: markerData.label,
              address: markerData.location,
              location: markerData.coordinates,
              category: markerData.category,
              rating: 0,
              price: '',
              phone: '',
              website: '',
              openingHours: '',
              description: ''
            }
          };
          
          setMapMarkers(prev => {
            const filtered = prev.filter(m => m.id !== markerData.marker_id);
            return [...filtered, marker];
          });

          // 添加到标记选择列表
          const markerSelection: Omit<MarkerSelection, 'selected'> = {
            id: markerData.marker_id,
            name: `${markerData.label}（${markerData.marker_id}）`,
            coordinates: markerData.coordinates,
            category: markerData.category
          };
          
          setSelectedMarkers(prev => {
            const exists = prev.some(m => m.id === markerSelection.id);
            if (exists) return prev;
            return [...prev, { ...markerSelection, selected: false }];
          });
        }
        
        // 如果工具调用返回行程规划数据，显示行程规划卡片
        if (result && result.success && result.data && result.data.trip_plan) {
          handleTripPlanResult(result.data.trip_plan);
        }
        
        // 如果工具调用返回路线规划数据，在地图上显示路线
        if (result && result.success && result.data && result.data.route_info) {
          displayRouteOnMap(result.data.route_info);
        }
        
        // 如果工具调用返回路线计算数据，在地图上显示路线
        if (result && result.success && result.data && result.data.origin && result.data.destination) {
          displayRouteOnMap({
            origin: result.data.origin,
            destination: result.data.destination,
            mode: result.data.mode || 'driving'
          });
        }
        
        // 检查是否所有工具调用都完成了
        setToolCalls(prev => {
          const allCompleted = prev.every(tool => tool.status === 'success' || tool.status === 'error');
          if (allCompleted && hasToolCalls) {
            // 所有工具调用完成，开始显示累积的消息
            setHasToolCalls(false);
            if (pendingMessage) {
              // 将累积的消息添加到消息列表
              setMessages(prevMessages => [...prevMessages, {
                id: `msg_${Date.now()}`,
                role: 'assistant',
                content: pendingMessage,
                timestamp: Date.now(),
                isStreaming: false
              }]);
              setPendingMessage('');
            }
            // 重新启用流式消息处理
            console.log('DEBUG: Tool calls completed, re-enabling streaming messages');
          }
          return prev;
        });
      });
    }
  }, []); // 空依赖数组，只初始化一次

  // 初始化AG-UI客户端 - 当accessToken变化时重新创建
  useEffect(() => {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    
    console.log('DEBUG: Creating new AGUIClient with token:', accessToken ? 'present' : 'missing');
    
    // 创建新的客户端
    aguiClientRef.current = new AGUIClient({
      baseUrl,
      token: accessToken || undefined,
      onEvent: (event: AGUIEvent) => {
        console.log('DEBUG: AGUIClient received event:', event.type);
        eventHandlerRef.current?.handleEvent(event);
      },
      onError: (error: Error) => {
        setIsLoading(false);
        setError(error.message);
        message.error(`连接错误: ${error.message}`);
      },
      onComplete: () => {
        setIsLoading(false);
      }
    });

    return () => {
      console.log('DEBUG: Closing AGUIClient');
      aguiClientRef.current?.close();
    };
  }, [accessToken]);

  // 发送消息
  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: inputValue.trim(),
      timestamp: Date.now()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setError(null);

    try {
      // 使用行程规划Agent
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${baseUrl}/api/v1/chat/agents/simple-trip-planner/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({
          message: userMessage.content,
          history: messages.map(msg => ({ role: msg.role, content: msg.content })),
          context: {
            map_markers: mapMarkers.map(marker => ({
              id: marker.id,
              name: marker.title,
              category: marker.poi?.category || 'unknown',
              coordinates: marker.position
            }))
          }
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error('No response body available');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      try {
        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            setIsLoading(false);
            break;
          }

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.trim() === '') continue;

            if (line.startsWith('data: ')) {
              const eventData = line.slice(6).trim();

              if (eventData === '[DONE]') {
                setIsLoading(false);
                return;
              }

              try {
                const aguiEvent: AGUIEvent = JSON.parse(eventData);
                eventHandlerRef.current?.handleEvent(aguiEvent);
              } catch (parseError) {
                console.error('Failed to parse AG-UI event:', parseError, 'Data:', eventData);
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    } catch (error) {
      setIsLoading(false);
      setError('发送消息失败');
      message.error('发送消息失败');
    }
  };

  // 处理键盘事件
  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // 处理POI选择 - 当Agent返回POI数据时调用
  const handlePOISelect = useCallback((poi: POIInfo) => {
    // 添加POI标记到地图
    const marker: MapMarker = {
      id: poi.id,
      position: poi.location,
      title: poi.name,
      content: `
        <div style="padding: 8px;">
          <h4 style="margin: 0 0 4px 0; font-size: 14px;">${poi.name}</h4>
          <p style="margin: 0; font-size: 12px; color: #666;">${poi.address}</p>
          ${poi.rating ? `<p style="margin: 4px 0 0 0; font-size: 12px; color: #ffa500;">⭐ ${poi.rating}</p>` : ''}
        </div>
      `,
      poi
    };
    
    setMapMarkers(prev => {
      // 移除相同ID的标记
      const filtered = prev.filter(m => m.id !== poi.id);
      return [...filtered, marker];
    });

    // 添加到标记选择列表
    const markerSelection: Omit<MarkerSelection, 'selected'> = {
      id: poi.id,
      name: `${poi.name}（${poi.id}）`,
      coordinates: poi.location,
      category: poi.category
    };
    
    setSelectedMarkers(prev => {
      const exists = prev.some(m => m.id === markerSelection.id);
      if (exists) return prev;
      return [...prev, { ...markerSelection, selected: false }];
    });
  }, []);

  // 切换标记选择状态
  const toggleMarkerSelection = useCallback((markerId: string) => {
    setSelectedMarkers(prev => 
      prev.map(marker =>
        marker.id === markerId
          ? { ...marker, selected: !marker.selected }
          : marker
      )
    );
  }, []);

  // 获取选中的标记
  const getSelectedMarkers = useCallback(() => {
    return selectedMarkers.filter(marker => marker.selected);
  }, [selectedMarkers]);

  // 清除所有选择
  const clearMarkerSelection = useCallback(() => {
    setSelectedMarkers(prev => 
      prev.map(marker => ({ ...marker, selected: false }))
    );
  }, []);

  // 处理行程规划结果
  const handleTripPlanResult = useCallback((tripPlan: any) => {
    setCurrentTripPlan(tripPlan);
    setShowTripPlanCard(true);
  }, []);

  // 保存行程规划
  const saveTripPlan = useCallback(() => {
    if (currentTripPlan) {
      // 这里可以调用API保存行程规划
      message.success('行程规划已保存！');
      setShowTripPlanCard(false);
      setCurrentTripPlan(null);
    }
  }, [currentTripPlan]);

  // 取消保存行程规划
  const cancelTripPlan = useCallback(() => {
    setShowTripPlanCard(false);
    setCurrentTripPlan(null);
    // 清除路线
    clearRoutes();
    setCurrentRoutes([]);
  }, [clearRoutes]);

  // 显示路线在地图上
  const displayRouteOnMap = useCallback(async (routeInfo: any) => {
    try {
      if (routeInfo.origin && routeInfo.destination) {
        const route = await calculateRoute({
          origin: routeInfo.origin,
          destination: routeInfo.destination,
          mode: routeInfo.mode || 'driving'
        });
        
        setCurrentRoutes([route]);
        
        // 添加起点和终点标记
        const newMarkers: MapMarker[] = [];
        
        // 起点标记
        if (typeof routeInfo.origin === 'string') {
          // 这里简化处理，实际应该调用地理编码API
          newMarkers.push({
            id: 'route_origin',
            position: { lat: 32.0603, lng: 118.7969 }, // 南京坐标
            title: routeInfo.origin,
            content: `<div style="padding: 8px;"><h4>起点</h4><p>${routeInfo.origin}</p></div>`
          });
        }
        
        // 终点标记
        if (typeof routeInfo.destination === 'string') {
          newMarkers.push({
            id: 'route_destination',
            position: { lat: 33.6103, lng: 119.0192 }, // 淮安坐标
            title: routeInfo.destination,
            content: `<div style="padding: 8px;"><h4>终点</h4><p>${routeInfo.destination}</p></div>`
          });
        }
        
        setMapMarkers(prev => [...prev.filter(m => !m.id.startsWith('route_')), ...newMarkers]);
        
        message.success('路线已在地图上显示');
      }
    } catch (error) {
      console.error('Route display error:', error);
      message.error('路线显示失败');
    }
  }, [calculateRoute]);

  // 清除地图上的路线
  const clearMapRoutes = useCallback(() => {
    clearRoutes();
    setCurrentRoutes([]);
    setMapMarkers(prev => prev.filter(m => !m.id.startsWith('route_')));
    message.info('已清除地图路线');
  }, [clearRoutes]);

  // 处理地图点击 - 使用useCallback避免重复创建
  const handleMapClick = useCallback((point: Point) => {
    console.log('Map clicked:', point);
    // 可以在这里添加点击地图的功能
  }, []);

  // 地图组件 - 使用useMemo避免重复渲染
  const mapComponent = useMemo(() => (
    <MapContainer
      key="trip-planning-map-container"
      containerId="trip-planning-map"
      config={mapConfig}
      markers={mapMarkers}
      routes={currentRoutes}
      onMapClick={handleMapClick}
      style={{ height: '100%' }}
    />
  ), [mapConfig, mapMarkers, currentRoutes, handleMapClick]);

  return (
    <>
      <style>
        {`
          @keyframes slideInRight {
            from {
              transform: translateX(100%);
              opacity: 0;
            }
            to {
              transform: translateX(0);
              opacity: 1;
            }
          }
          
          @keyframes slideOutRight {
            from {
              transform: translateX(0);
              opacity: 1;
            }
            to {
              transform: translateX(100%);
              opacity: 0;
            }
          }
          
          @keyframes pulse {
            0%, 100% {
              opacity: 1;
            }
            50% {
              opacity: 0.5;
            }
          }
          
          .markdown-content {
            line-height: 1.6;
          }
          
          .markdown-content h1,
          .markdown-content h2,
          .markdown-content h3,
          .markdown-content h4,
          .markdown-content h5,
          .markdown-content h6 {
            margin-top: 0;
            margin-bottom: 8px;
          }
          
          .markdown-content p {
            margin: 8px 0;
          }
          
          .markdown-content ul,
          .markdown-content ol {
            margin: 8px 0;
            padding-left: 20px;
          }
          
          .markdown-content li {
            margin: 4px 0;
          }
          
          .markdown-content blockquote {
            margin: 12px 0;
            padding: 12px 16px;
            border-left: 4px solid #3b82f6;
            background: rgba(59, 130, 246, 0.05);
            border-radius: 0 4px 4px 0;
          }
          
          .markdown-content code {
            background: rgba(0, 0, 0, 0.1);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.9em;
            font-family: 'Monaco', 'Consolas', 'Courier New', monospace;
          }
          
          .markdown-content pre {
            background: #1e293b;
            color: #e2e8f0;
            padding: 16px;
            border-radius: 8px;
            overflow: auto;
            margin: 12px 0;
            font-size: 0.9rem;
          }
          
          .markdown-content pre code {
            background: transparent;
            padding: 0;
            color: inherit;
          }
          
          .markdown-content table {
            width: 100%;
            border-collapse: collapse;
            margin: 12px 0;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            overflow: hidden;
          }
          
          .markdown-content th,
          .markdown-content td {
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
          }
          
          .markdown-content th {
            background: #f9fafb;
            font-weight: 600;
          }
          
          .markdown-content a {
            color: #3b82f6;
            text-decoration: none;
            border-bottom: 1px solid transparent;
            transition: border-color 0.2s;
          }
          
          .markdown-content a:hover {
            border-bottom-color: #3b82f6;
          }
        `}
      </style>
      
      <div style={{ 
        position: 'relative', 
        width: '100%', 
        height: 'calc(100vh - 64px - 48px)', // 减去Header高度(64px)和Footer高度(48px)
        overflow: 'hidden',
        display: 'flex'
      }}>
        {/* 地图区域 - 独立渲染，不受聊天状态影响 */}
        <div style={{ 
          flex: isChatOpen ? '0 0 70%' : '1',
          height: '100%',
          transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
          position: 'relative'
        }}>
          {mapComponent}
        </div>

        {/* 对话助手面板 - 固定右侧30% */}
        {isChatOpen && (
          <div
            style={{
              flex: '0 0 30%',
              height: '100%',
              background: 'white',
              borderRadius: '12px 0 0 12px',
              boxShadow: '-2px 0 12px rgba(0,0,0,0.06)',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
              animation: 'slideInRight 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
              border: '1px solid rgba(0,0,0,0.05)'
            }}
          >
            {/* 聊天区域 */}
            <div style={{ 
              flex: '1',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden'
            }}>
              {/* 面板头部 */}
              <div style={{
                padding: '16px 20px',
                borderBottom: '1px solid #f0f0f0',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                background: 'linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%)',
                borderRadius: '12px 0 0 0'
              }}>
                <Space>
                  <RobotOutlined style={{ color: '#1890ff' }} />
                  <span style={{ fontWeight: 500 }}>AI旅行助手</span>
                </Space>
                <Button
                  type="text"
                  icon={<CloseOutlined />}
                  onClick={() => setIsChatOpen(false)}
                  style={{ 
                    color: '#999',
                    borderRadius: '6px',
                    transition: 'all 0.2s ease',
                    padding: '4px 8px'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.color = '#ff4d4f';
                    e.currentTarget.style.background = '#fff2f0';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.color = '#999';
                    e.currentTarget.style.background = 'transparent';
                  }}
                />
              </div>

              {/* 消息区域 */}
              <div 
                style={{ 
                  flex: 1, 
                  padding: '20px 24px', 
                  overflowY: 'auto',
                  background: 'linear-gradient(180deg, #ffffff 0%, #f8f9fa 100%)'
                }}
              >
                {messages.length === 0 && (
                  <div style={{ textAlign: 'center', padding: '32px 0' }}>
                    <RobotOutlined style={{ fontSize: '48px', color: '#1890ff', marginBottom: '16px' }} />
                    <Text type="secondary">
                      你好！我是你的AI旅行助手，有什么可以帮助你的吗？
                    </Text>
                  </div>
                )}

                {/* 系统消息显示 */}
                {systemMessage && (
                  <div style={{ 
                    textAlign: 'center', 
                    padding: '12px 16px', 
                    margin: '16px 0',
                    background: 'linear-gradient(135deg, #e6f7ff 0%, #f0f9ff 100%)',
                    border: '1px solid #91d5ff',
                    borderRadius: '8px',
                    color: '#1890ff',
                    fontSize: '14px',
                    fontWeight: '500'
                  }}>
                    <Text style={{ color: '#1890ff', margin: 0 }}>
                      {systemMessage}
                    </Text>
                  </div>
                )}

                {/* 工具调用状态显示 */}
                {toolCalls.length > 0 && (
                  <div style={{ 
                    margin: '16px 0',
                    padding: '16px',
                    background: 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)',
                    border: '1px solid #0ea5e9',
                    borderRadius: '12px',
                    boxShadow: '0 2px 8px rgba(14, 165, 233, 0.1)'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
                      <div style={{ 
                        width: '8px', 
                        height: '8px', 
                        borderRadius: '50%', 
                        background: '#0ea5e9', 
                        marginRight: '8px',
                        animation: 'pulse 2s infinite'
                      }} />
                      <Text strong style={{ color: '#0369a1', fontSize: '16px' }}>
                        🔧 正在调用工具...
                      </Text>
                    </div>
                    {toolCalls.map((tool) => (
                      <Card
                        key={tool.id}
                        size="small"
                        style={{ 
                          marginBottom: '8px',
                          border: tool.status === 'success' ? '1px solid #52c41a' : 
                                 tool.status === 'error' ? '1px solid #ff4d4f' : 
                                 '1px solid #0ea5e9',
                          background: tool.status === 'success' ? '#f6ffed' : 
                                     tool.status === 'error' ? '#fff2f0' : 
                                     '#f0f9ff'
                        }}
                        bodyStyle={{ padding: '12px 16px' }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <Text code style={{ fontSize: '14px', fontWeight: '600' }}>
                              {tool.name}
                            </Text>
                            <Tag 
                              color={tool.status === 'success' ? 'success' : 
                                    tool.status === 'error' ? 'error' : 'processing'}
                              style={{ margin: 0, fontSize: '12px' }}
                            >
                              {tool.status === 'calling' ? '调用中...' :
                               tool.status === 'success' ? '成功' : '失败'}
                            </Tag>
                          </div>
                          {tool.status === 'success' && tool.result?.data?.pois && (
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                              找到 {tool.result.data.pois.length} 个POI
                            </Text>
                          )}
                        </div>
                        {tool.status === 'error' && tool.result?.error && (
                          <Text type="danger" style={{ fontSize: '12px', marginTop: '8px', display: 'block' }}>
                            错误: {tool.result.error}
                          </Text>
                        )}
                      </Card>
                    ))}
                  </div>
                )}

                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    style={{
                      display: 'flex',
                      justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                      marginBottom: '16px',
                      alignItems: 'flex-start'
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                        alignItems: 'flex-start',
                        maxWidth: '80%'
                      }}
                    >
                      <div
                        style={{
                          background: msg.role === 'user' ? '#1890ff' : '#f0f0f0',
                          color: msg.role === 'user' ? 'white' : '#333',
                          padding: '12px 16px',
                          borderRadius: msg.role === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                          wordBreak: 'break-word',
                          position: 'relative',
                          maxWidth: '100%',
                          boxShadow: '0 1px 2px rgba(0,0,0,0.1)'
                        }}
                      >
                        {msg.role === 'user' ? (
                          msg.content
                        ) : (
                          <MarkdownRenderer 
                            content={msg.content}
                            className="markdown-content"
                          />
                        )}
                        {msg.isStreaming && (
                          <Spin size="small" style={{ marginLeft: '8px' }} />
                        )}
                      </div>
                    </div>
                  </div>
                ))}

                {isLoading && (
                  <div style={{ 
                    textAlign: 'center', 
                    padding: '20px',
                    background: 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)',
                    borderRadius: '12px',
                    margin: '16px 0',
                    border: '1px solid #0ea5e9'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
                      <Spin size="default" />
                      <div>
                        <Text strong style={{ color: '#0369a1', fontSize: '16px' }}>
                          AI正在思考中...
                        </Text>
                        <div style={{ marginTop: '4px' }}>
                          <Text type="secondary" style={{ fontSize: '14px' }}>
                            请稍候，正在为您生成最佳方案
                          </Text>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {error && (
                  <Alert
                    message="连接错误"
                    description={error}
                    type="error"
                    showIcon
                    style={{ margin: '16px 0' }}
                  />
                )}

                {/* 滚动锚点 */}
                <div ref={messagesEndRef} />

                {/* 行程规划卡片 */}
                {showTripPlanCard && currentTripPlan && (
                  <div style={{ marginBottom: '16px' }}>
                    <Card
                      title={
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span>🎯</span>
                          <span>{currentTripPlan.title || '行程规划'}</span>
                        </div>
                      }
                      extra={
                        <Button 
                          type="text" 
                          icon={<CloseOutlined />} 
                          onClick={cancelTripPlan}
                          size="small"
                        />
                      }
                      style={{ 
                        border: '2px solid #1890ff',
                        borderRadius: '12px',
                        boxShadow: '0 4px 12px rgba(24, 144, 255, 0.15)'
                      }}
                    >
                      <div style={{ marginBottom: '16px' }}>
                        <Space wrap>
                          <Tag color="blue">时长: {currentTripPlan.duration || '1天'}</Tag>
                          <Tag color="green">交通: {currentTripPlan.transport_mode || 'mixed'}</Tag>
                          <Tag color="orange">地点: {currentTripPlan.locations?.length || 0}个</Tag>
                        </Space>
                      </div>

                      {currentTripPlan.schedule && currentTripPlan.schedule.length > 0 && (
                        <div style={{ marginBottom: '16px' }}>
                          <Text strong style={{ fontSize: '14px', marginBottom: '8px', display: 'block' }}>
                            📅 详细安排
                          </Text>
                          {currentTripPlan.schedule?.map((item, index: number) => (
                            <div 
                              key={index}
                              style={{ 
                                padding: '12px', 
                                background: '#f8f9fa', 
                                borderRadius: '8px', 
                                marginBottom: '8px',
                                border: '1px solid #e9ecef'
                              }}
                            >
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                                <Text strong style={{ color: '#1890ff' }}>{item.time}</Text>
                                <Text type="secondary" style={{ fontSize: '12px' }}>{item.duration}</Text>
                              </div>
                              <Text style={{ fontSize: '13px' }}>{item.activity}</Text>
                              <br />
                              <Text type="secondary" style={{ fontSize: '12px' }}>📍 {item.location}</Text>
                            </div>
                          ))}
                        </div>
                      )}

                      {currentTripPlan.routes && currentTripPlan.routes.length > 0 && (
                        <div style={{ marginBottom: '16px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                            <Text strong style={{ fontSize: '14px' }}>
                              🗺️ 路线规划
                            </Text>
                            <Space>
                              <Button 
                                size="small" 
                                type="primary"
                                onClick={() => {
                                  // 显示第一条路线在地图上
                                  if (currentTripPlan.routes && currentTripPlan.routes.length > 0) {
                                    const firstRoute = currentTripPlan.routes[0];
                                    displayRouteOnMap({
                                      origin: firstRoute.from,
                                      destination: firstRoute.to,
                                      mode: firstRoute.transport === '驾车' ? 'driving' : 
                                            firstRoute.transport === '公交' ? 'transit' : 
                                            firstRoute.transport === '步行' ? 'walking' : 'driving'
                                    });
                                  }
                                }}
                              >
                                在地图上显示
                              </Button>
                              <Button 
                                size="small" 
                                onClick={clearMapRoutes}
                              >
                                清除路线
                              </Button>
                            </Space>
                          </div>
                          {currentTripPlan.routes?.map((route, index: number) => (
                            <div 
                              key={index}
                              style={{ 
                                padding: '8px 12px', 
                                background: '#e6f7ff', 
                                borderRadius: '6px', 
                                marginBottom: '4px',
                                border: '1px solid #91d5ff'
                              }}
                            >
                              <Text style={{ fontSize: '13px' }}>
                                {index + 1}. {route.from} → {route.to}
                              </Text>
                              <br />
                              <Text type="secondary" style={{ fontSize: '11px' }}>
                                {route.transport} • {route.estimated_time}
                              </Text>
                            </div>
                          ))}
                        </div>
                      )}

                      {currentTripPlan.tips && currentTripPlan.tips.length > 0 && (
                        <div style={{ marginBottom: '16px' }}>
                          <Text strong style={{ fontSize: '14px', marginBottom: '8px', display: 'block' }}>
                            💡 实用建议
                          </Text>
                          <ul style={{ margin: 0, paddingLeft: '20px' }}>
                            {currentTripPlan.tips?.map((tip, index: number) => (
                              <li key={index} style={{ fontSize: '13px', marginBottom: '4px' }}>
                                <Text style={{ fontSize: '13px' }}>{tip}</Text>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      <div style={{ 
                        display: 'flex', 
                        justifyContent: 'flex-end', 
                        gap: '8px',
                        paddingTop: '12px',
                        borderTop: '1px solid #f0f0f0'
                      }}>
                        <Button onClick={cancelTripPlan}>
                          取消
                        </Button>
                        <Button type="primary" onClick={saveTripPlan}>
                          保存行程
                        </Button>
                      </div>
                    </Card>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* 标记选择器 */}
              {selectedMarkers.length > 0 && (
                <div style={{ 
                  padding: '16px 24px', 
                  borderTop: '1px solid #f0f0f0',
                  background: '#fafafa'
                }}>
                  <div style={{ marginBottom: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text strong style={{ fontSize: '14px' }}>选择地点进行行程规划</Text>
                    <Space>
                      <Button 
                        size="small" 
                        onClick={() => setShowMarkerSelector(!showMarkerSelector)}
                      >
                        {showMarkerSelector ? '收起' : '展开'}
                      </Button>
                      <Button 
                        size="small" 
                        onClick={clearMarkerSelection}
                        disabled={getSelectedMarkers().length === 0}
                      >
                        清除选择
                      </Button>
                    </Space>
                  </div>
                  
                  {showMarkerSelector && (
                    <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                      <Checkbox.Group 
                        value={selectedMarkers.filter(m => m.selected).map(m => m.id)}
                        onChange={(checkedValues) => {
                          selectedMarkers.forEach(marker => {
                            const shouldSelect = checkedValues.includes(marker.id);
                            if (marker.selected !== shouldSelect) {
                              toggleMarkerSelection(marker.id);
                            }
                          });
                        }}
                        style={{ width: '100%' }}
                      >
                        <Space direction="vertical" style={{ width: '100%' }}>
                          {selectedMarkers.map(marker => (
                            <Checkbox 
                              key={marker.id} 
                              value={marker.id}
                              style={{ 
                                width: '100%',
                                padding: '8px 12px',
                                borderRadius: '6px',
                                border: marker.selected ? '1px solid #1890ff' : '1px solid #d9d9d9',
                                background: marker.selected ? '#f0f9ff' : '#fff'
                              }}
                            >
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div>
                                  <Text strong style={{ fontSize: '13px' }}>{marker.name}</Text>
                                  <br />
                                  <Text type="secondary" style={{ fontSize: '11px' }}>
                                    {marker.category} • {marker.coordinates.lat.toFixed(4)}, {marker.coordinates.lng.toFixed(4)}
                                  </Text>
                                </div>
                                <Tag color="blue" style={{ fontSize: '10px' }}>
                                  {marker.category}
                                </Tag>
                              </div>
                            </Checkbox>
                          ))}
                        </Space>
                      </Checkbox.Group>
                    </div>
                  )}
                  
                  {getSelectedMarkers().length > 0 && (
                    <div style={{ marginTop: '12px', padding: '12px', background: '#e6f7ff', borderRadius: '6px' }}>
                      <Text strong style={{ fontSize: '13px', color: '#1890ff' }}>
                        已选择 {getSelectedMarkers().length} 个地点
                      </Text>
                      <div style={{ marginTop: '8px' }}>
                        <Button 
                          type="primary" 
                          size="small"
                          onClick={() => {
                            const selectedIds = getSelectedMarkers().map(m => m.id);
                            setInputValue(`请为这些地点规划行程：${selectedIds.join(', ')}`);
                          }}
                        >
                          生成行程规划
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* 输入区域 */}
              <div style={{ 
                padding: '20px 24px', 
                borderTop: '1px solid #f0f0f0',
                background: 'linear-gradient(180deg, #ffffff 0%, #f8f9fa 100%)',
                borderRadius: '0 0 0 12px'
              }}>
                <div style={{ 
                  display: 'flex', 
                  gap: '8px', 
                  alignItems: 'flex-end',
                  background: '#fff',
                  border: '1px solid #d9d9d9',
                  borderRadius: '8px',
                  padding: '8px',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.02)',
                  transition: 'all 0.2s ease'
                }}>
                  <TextArea
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="输入你的旅行问题，比如：我想去北京玩3天，预算5000元..."
                    autoSize={{ minRows: 1, maxRows: 4 }}
                    style={{ 
                      resize: 'none',
                      border: 'none',
                      boxShadow: 'none',
                      fontSize: '14px',
                      lineHeight: '1.5'
                    }}
                    disabled={isLoading}
                  />
                  <Button
                    type="primary"
                    icon={<SendOutlined />}
                    onClick={handleSendMessage}
                    loading={isLoading}
                    disabled={!inputValue.trim()}
                    style={{
                      height: '40px',
                      borderRadius: '6px',
                      fontWeight: '500',
                      boxShadow: '0 2px 4px rgba(24, 144, 255, 0.2)',
                      transition: 'all 0.2s ease'
                    }}
                    onMouseEnter={(e) => {
                      if (!isLoading && inputValue.trim()) {
                        e.currentTarget.style.transform = 'translateY(-1px)';
                        e.currentTarget.style.boxShadow = '0 4px 8px rgba(24, 144, 255, 0.3)';
                      }
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = 'translateY(0)';
                      e.currentTarget.style.boxShadow = '0 2px 4px rgba(24, 144, 255, 0.2)';
                    }}
                  >
                    {isLoading ? '发送中...' : '发送'}
                  </Button>
                </div>
                
                {/* 快捷提示 */}
                <div style={{ 
                  marginTop: '12px', 
                  display: 'flex', 
                  gap: '8px', 
                  flexWrap: 'wrap' 
                }}>
                  {[
                    '推荐北京景点',
                    '规划3天行程',
                    '查询美食推荐',
                    '计算交通费用'
                  ].map((hint) => (
                    <Button
                      key={hint}
                      size="small"
                      type="text"
                      onClick={() => setInputValue(hint)}
                      style={{
                        fontSize: '12px',
                        color: '#666',
                        border: '1px solid #e8e8e8',
                        borderRadius: '16px',
                        height: '28px',
                        padding: '0 12px',
                        background: '#fafafa',
                        transition: 'all 0.2s ease'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = '#f0f9ff';
                        e.currentTarget.style.borderColor = '#1890ff';
                        e.currentTarget.style.color = '#1890ff';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = '#fafafa';
                        e.currentTarget.style.borderColor = '#e8e8e8';
                        e.currentTarget.style.color = '#666';
                      }}
                    >
                      {hint}
                    </Button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default TripPlanning;