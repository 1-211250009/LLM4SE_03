import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Typography,
  Card,
  Tag,
  Button,
  Space,
  Row,
  Col,
  Descriptions,
  Empty,
  message,
  Spin,
  Statistic,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  Popconfirm,
  AutoComplete,
  TimePicker,
  DatePicker
} from 'antd';
import dayjs, { Dayjs } from 'dayjs';
import {
  CalendarOutlined,
  EnvironmentOutlined,
  UserOutlined,
  DollarOutlined,
  ClockCircleOutlined,
  ArrowLeftOutlined,
  EditOutlined,
  DeleteOutlined,
  PlusOutlined,
  AimOutlined
} from '@ant-design/icons';
import { MapContainer } from '../../modules/map';
import { MapConfig, MapMarker, RouteInfo } from '../../modules/map/types/map.types';
import axios from 'axios';
import { useAuthStore } from '../../store/auth.store';  // 添加这一行
import TripPlanningAIAssistant from '../../components/trip/TripPlanningAIAssistant';

const { Title, Text, Paragraph } = Typography;

interface ItineraryItem {
  id: string;
  poi_id?: string;
  name: string;
  description?: string;
  address?: string;
  coordinates?: { lat: number; lng: number };
  category: string;
  start_time?: string;
  end_time?: string;
  estimated_duration?: number;
  estimated_cost?: number;
  rating?: number;
  price_level?: string;
  phone?: string;
  website?: string;
  opening_hours?: string;
  images?: string[];
  order_index: number;
  is_completed: boolean;
  notes?: string;
}

interface Itinerary {
  id: string;
  day_number: number;
  date?: string;
  title?: string;
  description?: string;
  items: ItineraryItem[];
}

interface Expense {
  id: string;
  amount: number;
  currency: string;
  category: string;
  description?: string;
  location?: string;
  expense_date?: string;
  itinerary_id?: string;
  itinerary_item_id?: string;
}

interface Trip {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  destination?: string;
  start_date?: string;
  end_date?: string;
  duration_days: number;
  budget_total?: number;
  currency: string;
  status: string;
  tags?: string[];
  preferences?: any;
  traveler_count: number;
  itineraries: Itinerary[];
  expenses?: Expense[];
  created_at: string;
  updated_at?: string;
}

const TripDetail: React.FC = () => {
  const { tripId } = useParams<{ tripId: string }>();
  const navigate = useNavigate();
  const { accessToken, isAuthenticated } = useAuthStore();  // 使用auth store获取token
  
  const [trip, setTrip] = useState<Trip | null>(null);
  const [loading, setLoading] = useState(true);
  const [mapMarkers, setMapMarkers] = useState<MapMarker[]>([]);
  const [mapRoutes, setMapRoutes] = useState<RouteInfo[]>([]);
  const focusToPointRef = useRef<((point: { lat: number; lng: number }, zoom?: number) => void) | null>(null);
  
  // 节点管理状态
  const [nodeModalVisible, setNodeModalVisible] = useState(false);
  const [editingNode, setEditingNode] = useState<ItineraryItem | null>(null);
  const [selectedItineraryId, setSelectedItineraryId] = useState<string | null>(null);
  const [nodeForm] = Form.useForm();
  const [poiSearchOptions, setPoiSearchOptions] = useState<Array<{value: string, label: string, poi: any}>>([]);
  const [searchingPOI, setSearchingPOI] = useState(false);

  // 地图配置
  const mapConfig: MapConfig = useMemo(() => ({
    center: { lat: 39.9042, lng: 116.4074 }, // 默认北京
    zoom: 12,
    enableScrollWheelZoom: true,
    enableDragging: true,
    enableDoubleClickZoom: true,
    enableKeyboard: true,
    enableInertialDragging: true,
    enableContinuousZoom: true,
    enablePinchToZoom: true
  }), []);

  // 地图聚焦回调
  const handleMapReady = useCallback((focusFn: (point: { lat: number; lng: number }, zoom?: number) => void) => {
    focusToPointRef.current = focusFn;
  }, []);

  // 获取行程详情
  useEffect(() => {
    const fetchTripDetail = async () => {
      // 检查是否已登录
      if (!isAuthenticated || !accessToken) {
        console.error('未登录或token不存在');
        message.error('请先登录');
        navigate('/login');
        setLoading(false);
        return;
      }
      
      if (!tripId) {
        setLoading(false);
        return;
      }
      
      try {
        setLoading(true);
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
        
        console.log('Fetching trip detail:', tripId);
        console.log('API URL:', `${baseUrl}/api/v1/trips/${tripId}`);
        console.log('Token exists:', !!accessToken);
        
        const response = await axios.get(`${baseUrl}/api/v1/trips/${tripId}`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`  // 使用auth store的token
          }
        });
        
        console.log('Trip detail response:', response.data);
        console.log('Expenses in response:', response.data?.expenses);
        console.log('Expenses count:', response.data?.expenses?.length || 0);
        
        if (response.data) {
          setTrip(response.data);
          // 生成地图标记
          await generateMapMarkers(response.data);
        } else {
          console.error('No trip data in response');
          message.error('行程数据为空');
        }
      } catch (error: any) {
        console.error('获取行程详情失败:', error);
        console.error('Error details:', error.response?.data);
        
        if (error.response?.status === 404) {
          message.error('行程不存在');
        } else if (error.response?.status === 401) {
          message.error('未授权，请重新登录');
          navigate('/login');
        } else {
          message.error('获取行程详情失败');
        }
        
        // 设置trip为null以显示空状态
        setTrip(null);
      } finally {
        setLoading(false);
      }
    };

    fetchTripDetail();
  }, [tripId, navigate, accessToken, isAuthenticated]);

  // 生成地图标记和路径
  const generateMapMarkers = useCallback(async (tripData: Trip) => {
    try {
    const markers: MapMarker[] = [];
    const routes: RouteInfo[] = [];
    
    // 检查是否有行程数据
    if (!tripData || !tripData.itineraries || tripData.itineraries.length === 0) {
      console.log('No itineraries to generate markers');
      setMapMarkers([]);
      setMapRoutes([]);
      return;
    }
      
      console.log('开始生成地图标记和路线，行程天数:', tripData.itineraries.length);
    
    // 生成标记
    tripData.itineraries.forEach((itinerary) => {
      if (!itinerary.items || itinerary.items.length === 0) {
        return;
      }
      
      itinerary.items.forEach((item) => {
        if (item.coordinates) {
          // 格式化日期用于地图标记
          const dateStr = itinerary.date ? dayjs(itinerary.date).format('YYYY-MM-DD') : '';
          
          markers.push({
            id: item.id,
            position: item.coordinates,
            title: item.name,
            content: `
              <div style="padding: 12px; max-width: 250px;">
                <h4 style="margin: 0 0 8px 0; font-size: 16px; font-weight: bold; color: #1890ff;">
                  ${item.name}
                </h4>
                <div style="margin-bottom: 8px;">
                  <span style="background: #e6f7ff; color: #1890ff; padding: 2px 8px; border-radius: 4px; font-size: 12px;">
                    第${itinerary.day_number}天
                  </span>
                  ${dateStr ? `<span style="color: #666; font-size: 12px; margin-left: 8px;">📅 ${dateStr}</span>` : ''}
                  ${item.start_time ? `<span style="color: #666; font-size: 12px; margin-left: 8px;">⏰ ${item.start_time}</span>` : ''}
                </div>
                ${item.address ? `<p style="margin: 4px 0; font-size: 13px; color: #666;">📍 ${item.address}</p>` : ''}
                ${item.description ? `<p style="margin: 4px 0; font-size: 13px; color: #333;">${item.description}</p>` : ''}
                ${item.rating ? `<p style="margin: 4px 0; font-size: 13px; color: #ffa500;">⭐ ${item.rating}</p>` : ''}
                ${item.estimated_cost ? `<p style="margin: 4px 0; font-size: 13px; color: #52c41a;">💰 约 ¥${item.estimated_cost}</p>` : ''}
              </div>
            `,
            poi: {
              id: item.id,
              name: item.name,
              address: item.address || '',
              location: item.coordinates,
              category: item.category as any,  // 类型转换
              rating: item.rating || 0,
              price: item.price_level || '',
              phone: item.phone || '',
              website: item.website || '',
              openingHours: item.opening_hours || '',
              description: item.description || ''
            }
          });
        }
      });
    });
    
      // 生成路径 - 同一天的节点按顺序使用路线规划API连接
    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      
      // 按天数排序itineraries
      const sortedItineraries = [...tripData.itineraries].sort((a, b) => a.day_number - b.day_number);
      
        // 为每天的节点按顺序计算路径
      for (const itinerary of sortedItineraries) {
          // 过滤出有坐标的节点，并按order_index排序，确保按顺序连接
        const itemsWithCoords = itinerary.items
          .filter(item => item.coordinates && item.coordinates.lat && item.coordinates.lng)
            .sort((a, b) => (a.order_index || 0) - (b.order_index || 0));  // 按order_index排序，确保顺序
        
          // 如果这一天有多个节点，按顺序计算路径（从第1个到第2个，第2个到第3个...）
        if (itemsWithCoords.length > 1) {
          for (let i = 0; i < itemsWithCoords.length - 1; i++) {
            const origin = itemsWithCoords[i];
            const dest = itemsWithCoords[i + 1];
            
            try {
                // 调用百度地图路线规划API，按顺序连接相邻节点
              const response = await axios.post(
                `${baseUrl}/api/v1/map/route`,
                {
                  origin: {
                    lat: origin.coordinates!.lat,
                    lng: origin.coordinates!.lng
                  },
                  destination: {
                    lat: dest.coordinates!.lat,
                    lng: dest.coordinates!.lng
                  },
                  mode: 'driving'  // 可以根据节点类型智能选择：walking/driving/transit
                },
                {
                  headers: { 'Authorization': `Bearer ${accessToken}` }
                }
              );
              
              if (response.data && response.data.data) {
                  // 添加路径信息，包含天数标识，用于在地图上区分不同天的路线
                const routeData = {
                  ...response.data.data,
                  day_number: itinerary.day_number,  // 添加天数标识
                  itinerary_id: itinerary.id
                };
                routes.push(routeData);
                  console.log(`路径计算成功: 第${itinerary.day_number}天 ${origin.name} -> ${dest.name} (顺序: ${i + 1} -> ${i + 2})`);
                  console.log('路线数据:', {
                    hasPolyline: !!routeData.overview_polyline,
                    polylineLength: routeData.overview_polyline?.length,
                    distance: routeData.distance,
                    duration: routeData.duration
                  });
              } else if (response.data && response.data.success === false) {
                console.warn(`路径计算失败: 第${itinerary.day_number}天 ${origin.name} -> ${dest.name}`, response.data.message);
              }
            } catch (error: any) {
              console.error(`路径计算失败: 第${itinerary.day_number}天 ${origin.name} -> ${dest.name}`, error.response?.data || error.message);
            }
          }
        }
      }
      
      console.log(`总共生成 ${routes.length} 条路径`);
        console.log('所有路线数据:', routes.map(r => ({
          hasPolyline: !!r.overview_polyline,
          polylineLength: r.overview_polyline?.length,
          dayNumber: (r as any).day_number
        })));
        
        // 先设置标记，再设置路线，确保标记先显示
        setMapMarkers(markers);
        
        // 延迟设置路线，确保地图已准备好
        setTimeout(() => {
      setMapRoutes(routes);
          console.log('路线数据已设置，等待地图绘制');
        }, 100);
    } catch (error) {
      console.error('生成路径失败:', error);
        setMapMarkers([]);
      setMapRoutes([]);
        message.error('生成地图标记和路线失败');
      }
    } catch (error) {
      console.error('生成地图标记和路线失败:', error);
      setMapMarkers([]);
      setMapRoutes([]);
      message.error('生成地图标记和路线失败');
    }
  }, [accessToken]);

  // 计算总费用
  const totalExpenses = useMemo(() => {
    if (!trip?.expenses || !Array.isArray(trip.expenses)) {
      console.log('No expenses found or expenses is not an array:', trip?.expenses);
      return 0;
    }
    const total = trip.expenses.reduce((sum, expense) => {
      const amount = expense.amount || 0;
      console.log('Expense amount:', amount);
      return sum + amount;
    }, 0);
    console.log('Total expenses calculated:', total);
    return total;
  }, [trip?.expenses]);

  // 计算剩余预算
  const remainingBudget = useMemo(() => {
    if (!trip?.budget_total) return null;
    return trip.budget_total - totalExpenses;
  }, [trip?.budget_total, totalExpenses]);
  
  // 计算天数：根据日期和开始日期计算是第几天
  const calculateDayNumber = (date: dayjs.Dayjs, startDate: dayjs.Dayjs): number => {
    const diff = date.diff(startDate, 'day');
    return Math.max(1, diff + 1); // 例如：2025-11-11 到 2025-11-11 是第1天
  };

  // 根据日期查找或创建itinerary
  const findOrCreateItinerary = async (date: dayjs.Dayjs): Promise<string | null> => {
    if (!tripId || !accessToken || !trip?.start_date) {
      return null;
    }

    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const dateStr = date.format('YYYY-MM-DD') + 'T00:00:00';
    const startDate = dayjs(trip.start_date);
    const dayNumber = calculateDayNumber(date, startDate);

    // 先查找是否已存在该日期的itinerary
    if (trip.itineraries && trip.itineraries.length > 0) {
      const existingItinerary = trip.itineraries.find(it => {
        if (!it.date) return false;
        const itDate = dayjs(it.date);
        return itDate.isSame(date, 'day');
      });
      
      if (existingItinerary) {
        return existingItinerary.id;
      }
    }

    // 如果不存在，创建新的itinerary
    try {
      const response = await axios.post(
        `${baseUrl}/api/v1/trips/${tripId}/itineraries`,
        {
          day_number: dayNumber,
          date: dateStr,
          title: `第${dayNumber}天`,
          description: ''
        },
        {
          headers: { 
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
          }
        }
      );

      // 重新获取行程详情以更新itineraries列表
      const tripResponse = await axios.get(`${baseUrl}/api/v1/trips/${tripId}`, {
        headers: { 'Authorization': `Bearer ${accessToken}` }
      });
      setTrip(tripResponse.data);

      message.success(`已创建第${dayNumber}天行程安排`);
      return response.data.id;
    } catch (error: any) {
      console.error('创建行程安排失败:', error);
      message.error(error.response?.data?.detail || '创建行程安排失败');
      return null;
    }
  };

  // 添加节点
  const handleAddNode = async (itineraryId?: string) => {
    if (!tripId || !accessToken) {
      message.error('未登录或行程ID不存在');
      return;
    }

    if (!trip?.start_date) {
      message.error('行程未设置开始日期，请先设置行程的开始日期');
      return;
    }

    // 如果指定了itineraryId，直接使用
    if (itineraryId) {
      setSelectedItineraryId(itineraryId);
      setEditingNode(null);
      nodeForm.resetFields();
      // 设置默认日期为当前itinerary的日期
      const itinerary = trip.itineraries?.find(it => it.id === itineraryId);
      const defaultDate = itinerary?.date 
        ? dayjs(itinerary.date) 
        : dayjs(trip.start_date);
      nodeForm.setFieldsValue({ 
        category: 'attraction',
        itinerary_date: defaultDate
      });
      setNodeModalVisible(true);
      return;
    }

    // 如果没有指定itineraryId，打开Modal让用户选择日期
    setSelectedItineraryId(null);
    setEditingNode(null);
    nodeForm.resetFields();
    // 设置默认日期为开始日期（如果没有itinerary）或最后一天的日期
    let defaultDate = dayjs(trip.start_date);
    if (trip.itineraries && trip.itineraries.length > 0) {
      // 如果有itinerary，默认选择最后一天的日期
      const sortedItineraries = [...trip.itineraries].sort((a, b) => 
        (a.day_number || 0) - (b.day_number || 0)
      );
      const lastItinerary = sortedItineraries[sortedItineraries.length - 1];
      if (lastItinerary.date) {
        defaultDate = dayjs(lastItinerary.date);
      }
    }
    nodeForm.setFieldsValue({ 
      category: 'attraction',
      itinerary_date: defaultDate
    });
    setNodeModalVisible(true);
  };
  
  // 编辑节点
  const handleEditNode = (node: ItineraryItem, itineraryId: string) => {
    setSelectedItineraryId(itineraryId);
    setEditingNode(node);
    
    // 找到节点所属的itinerary，获取日期
    const itinerary = trip?.itineraries?.find(it => it.id === itineraryId);
    
    // 转换时间为dayjs对象
    const formValues: any = {
      ...node,
      start_time: node.start_time ? dayjs(node.start_time, 'HH:mm') : null,
      end_time: node.end_time ? dayjs(node.end_time, 'HH:mm') : null,
      // 编辑时不需要显示日期选择器，但保留itinerary_date字段以避免表单错误
      itinerary_date: itinerary?.date ? dayjs(itinerary.date) : null
    };
    
    nodeForm.setFieldsValue(formValues);
    setNodeModalVisible(true);
  };
  
  // 删除节点
  const handleDeleteNode = async (nodeId: string, itineraryId: string) => {
    if (!accessToken) {
      message.error('未登录');
      return;
    }
    
    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      
      await axios.delete(
        `${baseUrl}/api/v1/trips/itineraries/${itineraryId}/items/${nodeId}`,
        {
          headers: { 'Authorization': `Bearer ${accessToken}` }  // 使用auth store的token
        }
      );
      
      message.success('节点删除成功');
      // 重新获取行程详情
      if (tripId) {
        const response = await axios.get(`${baseUrl}/api/v1/trips/${tripId}`, {
          headers: { 'Authorization': `Bearer ${accessToken}` }  // 使用auth store的token
        });
        setTrip(response.data);
        generateMapMarkers(response.data);
      }
    } catch (error) {
      console.error('删除节点失败:', error);
      message.error('删除节点失败');
    }
  };
  
  // POI搜索
  const handlePOISearch = async (keyword: string) => {
    if (!keyword || keyword.length < 2) {
      setPoiSearchOptions([]);
      return;
    }
    
    if (!accessToken) {
      return;
    }
    
    try {
      setSearchingPOI(true);
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const city = trip?.destination || '北京';
      
      const response = await axios.post(
        `${baseUrl}/api/v1/map/poi/search`,
        {
          keyword: keyword,
          city: city,
          category: nodeForm.getFieldValue('category') || 'attraction'
        },
        {
          headers: { 'Authorization': `Bearer ${accessToken}` }
        }
      );
      
      if (response.data.success && response.data.data) {
        const pois = response.data.data.pois || [];
        const options = pois.map((poi: any) => ({
          value: poi.name,
          label: `${poi.name} - ${poi.address || ''}`,
          poi: poi
        }));
        setPoiSearchOptions(options);
      } else {
        setPoiSearchOptions([]);
      }
    } catch (error) {
      console.error('POI搜索失败:', error);
      setPoiSearchOptions([]);
    } finally {
      setSearchingPOI(false);
    }
  };
  
  // 选择POI
  const handlePOISelect = (_value: string, option: any) => {
    if (option && option.poi) {
      const poi = option.poi;
      nodeForm.setFieldsValue({
        name: poi.name,
        address: poi.address,
        lat: poi.location?.lat,
        lng: poi.location?.lng,
        description: poi.description || poi.name,
        phone: poi.phone,
        website: poi.website,
        openingHours: poi.opening_hours,
        rating: poi.rating
      });
    }
  };
  
  // 计算时长（分钟）
  const calculateDuration = (startTime: Dayjs | null, endTime: Dayjs | null): number | null => {
    if (!startTime || !endTime) return null;
    const diff = endTime.diff(startTime, 'minute');
    return diff > 0 ? diff : null;
  };

  // 保存节点
  const handleSaveNode = async (values: any) => {
    if (!accessToken) {
      message.error('未登录');
      return;
    }

    if (!trip?.start_date) {
      message.error('行程未设置开始日期');
      return;
    }

    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      
      // 确定要使用的itinerary ID
      let targetItineraryId = selectedItineraryId;
      
      // 如果用户选择了日期（itinerary_date），根据日期查找或创建itinerary
      if (values.itinerary_date) {
        const selectedDate = values.itinerary_date as Dayjs;
        
        // 验证日期是否在开始和结束日期之间
        const startDate = dayjs(trip.start_date);
        if (selectedDate.isBefore(startDate, 'day')) {
          message.error('选择的日期不能早于行程开始日期');
          return;
        }
        if (trip.end_date) {
          const endDate = dayjs(trip.end_date);
          if (selectedDate.isAfter(endDate, 'day')) {
            message.error('选择的日期不能晚于行程结束日期');
            return;
          }
        }
        
        // 查找或创建itinerary
        targetItineraryId = await findOrCreateItinerary(selectedDate);
        if (!targetItineraryId) {
          message.error('无法创建或找到行程安排');
          return;
        }
      } else if (!targetItineraryId) {
        // 如果没有选择日期且没有itineraryId，使用开始日期创建第一天的itinerary
        const startDate = dayjs(trip.start_date);
        targetItineraryId = await findOrCreateItinerary(startDate);
        if (!targetItineraryId) {
          message.error('无法创建或找到行程安排');
          return;
        }
      }
      
      // 格式化时间：将dayjs对象转换为HH:mm格式字符串
      const startTime = values.start_time ? (values.start_time as Dayjs).format('HH:mm') : null;
      const endTime = values.end_time ? (values.end_time as Dayjs).format('HH:mm') : null;
      
      // 自动计算预计时长
      const estimatedDuration = calculateDuration(values.start_time, values.end_time);
      
      // 计算order_index：如果是新增节点，使用当前itinerary中节点的最大order_index + 1
      // 注意：如果刚刚创建了itinerary（通过findOrCreateItinerary），trip数据已经更新，直接使用即可
      let orderIndex = 0;
      if (!editingNode) {
        // 重新获取最新的trip数据以确保itineraries和items是最新的
        const tripResponse = await axios.get(`${baseUrl}/api/v1/trips/${tripId}`, {
          headers: { 'Authorization': `Bearer ${accessToken}` }
        });
        const currentTripData = tripResponse.data as Trip;
        const currentItinerary = currentTripData.itineraries?.find((it: Itinerary) => it.id === targetItineraryId);
        if (currentItinerary && currentItinerary.items && currentItinerary.items.length > 0) {
          const maxOrderIndex = Math.max(...currentItinerary.items.map((item: ItineraryItem) => item.order_index || 0));
          orderIndex = maxOrderIndex + 1;
        }
      } else if (editingNode) {
        orderIndex = editingNode.order_index || 0;
      }
      
      const nodeData: any = {
        name: values.name,
        category: values.category,
        description: values.description,
        address: values.address,
        start_time: startTime,
        end_time: endTime,
        estimated_duration: estimatedDuration,
        estimated_cost: values.estimated_cost,
        notes: values.notes,
        order_index: orderIndex
      };
      
      // 如果有坐标，添加坐标
      if (values.lat && values.lng) {
        nodeData.coordinates = {
          lat: parseFloat(values.lat),
          lng: parseFloat(values.lng)
        };
      }
      
      // 修复API路径：使用正确的路径 /api/v1/trips/itineraries/{itinerary_id}/items
      if (editingNode) {
        // 更新节点
        const response = await axios.put(
          `${baseUrl}/api/v1/trips/itineraries/${targetItineraryId}/items/${editingNode.id}`,
          nodeData,
          {
            headers: { 
              'Authorization': `Bearer ${accessToken}`,
              'Content-Type': 'application/json'
            }
          }
        );
        console.log('更新节点响应:', response.data);
        message.success('节点更新成功');
      } else {
        // 添加节点
        const response = await axios.post(
          `${baseUrl}/api/v1/trips/itineraries/${targetItineraryId}/items`,
          nodeData,
          {
            headers: { 
              'Authorization': `Bearer ${accessToken}`,
              'Content-Type': 'application/json'
            }
          }
        );
        console.log('添加节点响应:', response.data);
        message.success('节点添加成功');
      }
      
      setNodeModalVisible(false);
      setPoiSearchOptions([]);
      nodeForm.resetFields();
      
      // 重新获取行程详情
      if (tripId) {
        const response = await axios.get(`${baseUrl}/api/v1/trips/${tripId}`, {
          headers: { 'Authorization': `Bearer ${accessToken}` }
        });
        setTrip(response.data);
        await generateMapMarkers(response.data);
      }
    } catch (error: any) {
      console.error('保存节点失败:', error);
      console.error('错误详情:', error.response?.data);
      message.error(error.response?.data?.detail || error.response?.data?.message || '保存节点失败');
    }
  };

  // 渲染加载状态
  if (loading) {
    return (
      <div style={{ 
        minHeight: '100vh', 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center',
        background: '#f9fafb'
      }}>
        <Spin size="large" tip="加载行程中..." />
      </div>
    );
  }

  // 渲染空状态
  if (!trip) {
  return (
    <div style={{ minHeight: '100vh', background: '#f9fafb', padding: '32px 0' }}>
      <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '0 16px' }}>
          <Empty 
            description="行程不存在或已被删除"
            style={{ marginTop: '100px' }}
          >
            <Button type="primary" onClick={() => navigate('/trips')}>
              返回行程列表
            </Button>
          </Empty>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: '#f9fafb' }}>
      {/* 页面头部 */}
      <div style={{ 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
        padding: '32px 0',
        marginBottom: '24px'
      }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '0 24px' }}>
          <Button 
            icon={<ArrowLeftOutlined />} 
            onClick={() => navigate('/trips')}
            style={{ 
              marginBottom: '16px',
              color: 'white',
              border: '1px solid rgba(255,255,255,0.3)',
              background: 'transparent'
            }}
          >
            返回行程列表
          </Button>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <Title level={2} style={{ color: 'white', marginBottom: '8px' }}>
                {trip.title}
              </Title>
              <Space wrap>
                {trip.destination && (
                  <Tag icon={<EnvironmentOutlined />} color="blue">{trip.destination}</Tag>
                )}
                <Tag icon={<CalendarOutlined />} color="purple">
                  {trip.duration_days} 天
                </Tag>
                <Tag icon={<UserOutlined />} color="green">
                  {trip.traveler_count} 人
                </Tag>
                {trip.status && (
                  <Tag color={trip.status === 'active' ? 'success' : 'default'}>
                    {trip.status === 'draft' ? '草稿' :
                     trip.status === 'planned' ? '已计划' :
                     trip.status === 'active' ? '进行中' :
                     trip.status === 'completed' ? '已完成' : '已取消'}
                  </Tag>
                )}
              </Space>
            </div>
          </div>
        </div>
      </div>

      {/* 主要内容区域 */}
      <div style={{ maxWidth: '1600px', margin: '0 auto', padding: '0 24px 32px' }}>
        <Row gutter={[24, 24]}>
          {/* 左侧：行程信息和时间轴 */}
          <Col xs={24} lg={14}>
            {/* 基本信息卡片 */}
            <Card 
              title="行程信息" 
              style={{ marginBottom: '24px' }}
              extra={
                <Space>
                  {trip.budget_total && (
                    <>
                      <Statistic
                        title="总预算"
                        value={trip.budget_total}
                        prefix="¥"
                        valueStyle={{ fontSize: '20px', color: '#1890ff' }}
                      />
                      <Statistic
                        title="已花费"
                        value={totalExpenses}
                        prefix="¥"
                        valueStyle={{ 
                          fontSize: '20px', 
                          color: remainingBudget && remainingBudget < 0 ? '#ff4d4f' : '#52c41a' 
                        }}
                      />
                    </>
                  )}
                </Space>
              }
            >
              <Descriptions column={2}>
                {trip.description && (
                  <Descriptions.Item label="行程描述" span={2}>
                    {trip.description}
                  </Descriptions.Item>
                )}
                {trip.start_date && (
                  <Descriptions.Item label="开始日期">
                    {new Date(trip.start_date).toLocaleDateString('zh-CN')}
                  </Descriptions.Item>
                )}
                {trip.end_date && (
                  <Descriptions.Item label="结束日期">
                    {new Date(trip.end_date).toLocaleDateString('zh-CN')}
                  </Descriptions.Item>
                )}
                <Descriptions.Item label="行程天数">
                  {trip.duration_days} 天
                </Descriptions.Item>
                <Descriptions.Item label="同行人数">
                  {trip.traveler_count} 人
                </Descriptions.Item>
                {trip.currency && (
                  <Descriptions.Item label="货币单位">
                    {trip.currency}
                  </Descriptions.Item>
                )}
              </Descriptions>
              
              {trip.tags && trip.tags.length > 0 && (
                <div style={{ marginTop: '16px' }}>
                  <Text strong>标签：</Text>
                  <Space wrap style={{ marginTop: '8px' }}>
                    {trip.tags.map((tag, index) => (
                      <Tag key={index} color="blue">{tag}</Tag>
                    ))}
                  </Space>
                </div>
              )}
            </Card>

            {/* 行程时间轴 */}
            <Card 
              title="行程安排" 
              extra={
                <Space>
                  {tripId && (
                    <TripPlanningAIAssistant 
                      tripId={tripId}
                      onItemChanged={() => {
                        // 刷新行程数据
                        if (tripId) {
                          const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
                          axios.get(`${baseUrl}/api/v1/trips/${tripId}`, {
                            headers: { 'Authorization': `Bearer ${accessToken}` }
                          }).then(response => {
                            if (response.data) {
                              setTrip(response.data);
                              generateMapMarkers(response.data);
                            }
                          }).catch(error => {
                            console.error('Failed to refresh trip:', error);
                          });
                        }
                      }}
                    />
                  )}
                <Button 
                  type="primary" 
                  icon={<PlusOutlined />} 
                  size="small"
                  onClick={() => handleAddNode()}
                >
                  添加行程节点
                </Button>
                </Space>
              }
            >
              {trip.itineraries.length === 0 ? (
                <Empty 
                  description="暂无行程安排，点击右上角按钮添加第一个节点"
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
              ) : (
                <div style={{ paddingLeft: '0' }}>
                  {trip.itineraries
                    .sort((a, b) => a.day_number - b.day_number)
                    .map((itinerary) => (
                    <div key={itinerary.id} style={{ marginBottom: '24px', position: 'relative' }}>
                      {/* 天数标题 */}
                        <div style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        marginBottom: '16px',
                        paddingLeft: '0'
                      }}>
                        <div style={{
                          width: '4px',
                          height: '24px',
                          background: '#1890ff',
                          borderRadius: '2px',
                          marginRight: '12px',
                          flexShrink: 0
                        }} />
                        <div>
                          <Text strong style={{ fontSize: '16px', color: '#1890ff' }}>
                          第 {itinerary.day_number} 天
                          </Text>
                          {itinerary.date ? (
                            <Text type="secondary" style={{ fontSize: '13px', marginLeft: '8px' }}>
                              {dayjs(itinerary.date).format('YYYY-MM-DD')}
                            </Text>
                          ) : (
                            trip?.start_date && (
                              <Text type="danger" style={{ fontSize: '13px', marginLeft: '8px' }}>
                                日期未设置
                              </Text>
                            )
                          )}
                        </div>
                      </div>
                      
                      <Card 
                        size="small" 
                        title={`共 ${itinerary.items.length} 个行程节点`}
                        style={{ marginBottom: '16px', marginLeft: '0' }}
                      >
                        {itinerary.description && (
                          <Paragraph style={{ color: '#666', marginBottom: '12px' }}>
                            {itinerary.description}
                          </Paragraph>
                        )}
                        
                        {itinerary.items.length === 0 ? (
                          <Empty description="暂无节点" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                        ) : (
                          <Space direction="vertical" style={{ width: '100%' }} size="middle">
                            {itinerary.items
                              .sort((a, b) => a.order_index - b.order_index)
                              .map((item, index) => (
                              <Card 
                                key={item.id}
                                size="small"
                                style={{ 
                                  background: '#fafafa',
                                  border: '1px solid #e8e8e8'
                                }}
                                bodyStyle={{ padding: '12px' }}
                              >
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                  <div style={{ flex: 1 }}>
                                    <div style={{ marginBottom: '8px' }}>
                                      <Text strong style={{ fontSize: '15px' }}>
                                        {index + 1}. {item.name}
                                      </Text>
                                      <Tag 
                                        color={
                                          item.category === 'attraction' ? 'blue' :
                                          item.category === 'restaurant' ? 'orange' :
                                          item.category === 'hotel' ? 'purple' :
                                          item.category === 'transport' ? 'green' : 'default'
                                        }
                                        style={{ marginLeft: '8px' }}
                                      >
                                        {item.category === 'attraction' ? '景点' :
                                         item.category === 'restaurant' ? '餐厅' :
                                         item.category === 'hotel' ? '酒店' :
                                         item.category === 'transport' ? '交通' :
                                         item.category === 'shopping' ? '购物' : '其他'}
                                      </Tag>
                                      {item.is_completed && (
                                        <Tag color="success">已完成</Tag>
                                      )}
                                    </div>
                                    
                                    {item.description && (
                                      <Paragraph style={{ color: '#666', margin: '4px 0', fontSize: '13px' }}>
                                        {item.description}
                                      </Paragraph>
                                    )}
                                    
                                    <Space wrap size="small">
                                      {itinerary.date && (
                                        <Text type="secondary" style={{ fontSize: '12px' }}>
                                          <CalendarOutlined /> {dayjs(itinerary.date).format('YYYY-MM-DD')}
                                        </Text>
                                      )}
                                      {item.start_time && (
                                        <Text type="secondary" style={{ fontSize: '12px' }}>
                                          <ClockCircleOutlined /> {item.start_time}
                                          {item.end_time && ` - ${item.end_time}`}
                                        </Text>
                                      )}
                                      {item.estimated_duration && (
                                        <Text type="secondary" style={{ fontSize: '12px' }}>
                                          约 {item.estimated_duration} 分钟
                                        </Text>
                                      )}
                                      {item.estimated_cost && (
                                        <Text type="secondary" style={{ fontSize: '12px' }}>
                                          <DollarOutlined /> 约 ¥{item.estimated_cost}
                                        </Text>
                                      )}
                                      {item.rating && (
                                        <Text type="secondary" style={{ fontSize: '12px' }}>
                                          ⭐ {item.rating}
                                        </Text>
                                      )}
                                    </Space>
                                    
                                    {item.address && (
                                      <div style={{ marginTop: '8px' }}>
                                        <Text type="secondary" style={{ fontSize: '12px' }}>
                                          <EnvironmentOutlined /> {item.address}
                                        </Text>
                                      </div>
                                    )}
                                  </div>
                                  
                                  {/* 操作按钮 */}
                                  <div style={{ marginLeft: '12px' }}>
                                    <Space direction="vertical" size="small">
                                      {item.coordinates && focusToPointRef.current && (
                                        <Button 
                                          type="text" 
                                          size="small"
                                          icon={<AimOutlined />}
                                          onClick={() => {
                                            if (focusToPointRef.current) {
                                              focusToPointRef.current(item.coordinates!, 16);
                                              message.success(`已定位到 ${item.name}`);
                                            }
                                          }}
                                        >
                                          定位
                                        </Button>
                                      )}
                                      <Button 
                                        type="text" 
                                        size="small"
                                        icon={<EditOutlined />}
                                        onClick={() => handleEditNode(item, itinerary.id)}
                                      >
                                        编辑
                                      </Button>
                                      <Popconfirm
                                        title="确定删除这个节点吗？"
                                        onConfirm={() => handleDeleteNode(item.id, itinerary.id)}
                                        okText="确定"
                                        cancelText="取消"
                                      >
                                        <Button 
                                          type="text" 
                                          size="small"
                                          danger
                                          icon={<DeleteOutlined />}
                                        >
                                          删除
                                        </Button>
                                      </Popconfirm>
                                    </Space>
                                  </div>
                                </div>
                              </Card>
                            ))}
                            
                            {/* 添加节点按钮 */}
                            <Button 
                              type="dashed"
                              block
                              icon={<PlusOutlined />}
                              onClick={() => handleAddNode(itinerary.id)}
                              style={{ marginTop: '12px' }}
                            >
                              添加节点
                            </Button>
                          </Space>
                        )}
                      </Card>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </Col>

          {/* 右侧：地图 */}
          <Col xs={24} lg={10} style={{ display: 'flex', flexDirection: 'column' }}>
            <div style={{ position: 'sticky', top: '24px' }}>
              <Card 
                title="行程地图" 
                style={{ marginBottom: '24px' }}
                bodyStyle={{ padding: 0 }}
              >
                <div style={{ height: '600px' }}>
                  <MapContainer
                    containerId="trip-detail-map"
                    config={mapConfig}
                    markers={mapMarkers}
                    routes={mapRoutes}
                    onMapReady={handleMapReady}
                    style={{ height: '100%', borderRadius: '0 0 8px 8px' }}
                  />
                </div>
              </Card>
              
              {/* 费用统计卡片 */}
              {trip.expenses && trip.expenses.length > 0 && (
                <Card title="费用统计">
                  <Statistic
                    title="总花费"
                    value={totalExpenses}
                    prefix="¥"
                    valueStyle={{ color: '#52c41a' }}
                  />
                  {trip.budget_total && (
                    <Statistic
                      title={remainingBudget && remainingBudget >= 0 ? "剩余预算" : "超出预算"}
                      value={Math.abs(remainingBudget || 0)}
                      prefix={remainingBudget && remainingBudget >= 0 ? "¥" : "-¥"}
                      valueStyle={{ 
                        color: remainingBudget && remainingBudget >= 0 ? '#1890ff' : '#ff4d4f' 
                      }}
                      style={{ marginTop: '16px' }}
                    />
                  )}
                </Card>
              )}
            </div>
          </Col>
        </Row>
      </div>
      
      {/* 节点管理Modal */}
      <Modal
        title={editingNode ? '编辑节点' : '添加节点'}
        open={nodeModalVisible}
        onCancel={() => {
          setNodeModalVisible(false);
          setEditingNode(null);
          setPoiSearchOptions([]);
          nodeForm.resetFields();
        }}
        onOk={() => nodeForm.submit()}
        width={700}
        okText="保存"
        cancelText="取消"
      >
        <Form
          form={nodeForm}
          layout="vertical"
          onFinish={handleSaveNode}
        >
          <Form.Item
            name="name"
            label="节点名称/地点搜索"
            rules={[{ required: true, message: '请输入节点名称或搜索地点' }]}
          >
            <AutoComplete
              options={poiSearchOptions}
              onSearch={handlePOISearch}
              onSelect={handlePOISelect}
              placeholder="搜索地点，例如：故宫、全聚德烤鸭店、北京饭店"
              notFoundContent={searchingPOI ? <Spin size="small" /> : '暂无数据'}
              style={{ width: '100%' }}
            />
          </Form.Item>

          {/* 日期选择 - 只在添加节点时显示，编辑时隐藏 */}
          {!editingNode && (
            <Form.Item
              name="itinerary_date"
              label="行程日期"
              rules={[{ required: true, message: '请选择行程日期' }]}
              tooltip="选择要将节点添加到哪一天，如果该日期还没有行程安排，系统会自动创建"
            >
              <DatePicker
                style={{ width: '100%' }}
                format="YYYY-MM-DD"
                placeholder="选择行程日期"
                disabledDate={(current: dayjs.Dayjs | null) => {
                  if (!trip?.start_date || !trip?.end_date || !current) return false;
                  const startDate = dayjs(trip.start_date);
                  const endDate = dayjs(trip.end_date);
                  // 禁用不在开始和结束日期之间的日期
                  return current.isBefore(startDate, 'day') || current.isAfter(endDate, 'day');
                }}
              />
            </Form.Item>
          )}
          
          <Form.Item
            name="category"
            label="节点类型"
            rules={[{ required: true, message: '请选择节点类型' }]}
            initialValue="attraction"
          >
            <Select 
              onChange={() => {
                // 切换类型时重新搜索
                const name = nodeForm.getFieldValue('name');
                if (name) {
                  handlePOISearch(name);
                }
              }}
            >
              <Select.Option value="attraction">景点</Select.Option>
              <Select.Option value="restaurant">餐厅</Select.Option>
              <Select.Option value="hotel">酒店</Select.Option>
              <Select.Option value="transport">交通</Select.Option>
              <Select.Option value="shopping">购物</Select.Option>
              <Select.Option value="other">其他</Select.Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="description"
            label="描述"
          >
            <Input.TextArea rows={2} placeholder="节点描述" />
          </Form.Item>
          
          <Form.Item
            name="address"
            label="地址"
          >
            <Input placeholder="详细地址" />
          </Form.Item>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="start_time"
                label="开始时间"
              >
                <TimePicker
                  format="HH:mm"
                  style={{ width: '100%' }}
                  placeholder="选择开始时间"
                  minuteStep={5}
                  onChange={() => {
                    // 触发预计时长的更新
                    nodeForm.setFieldsValue({});
                  }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="end_time"
                label="结束时间"
                dependencies={['start_time']}
                rules={[
                  ({ getFieldValue }) => ({
                    validator(_, value) {
                      const startTime = getFieldValue('start_time');
                      if (!value || !startTime) {
                        return Promise.resolve();
                      }
                      if (value.isBefore(startTime) || value.isSame(startTime)) {
                        return Promise.reject(new Error('结束时间必须晚于开始时间'));
                      }
                      return Promise.resolve();
                    },
                  }),
                ]}
              >
                <TimePicker
                  format="HH:mm"
                  style={{ width: '100%' }}
                  placeholder="选择结束时间"
                  minuteStep={5}
                  onChange={() => {
                    // 触发预计时长的更新
                    nodeForm.setFieldsValue({});
                  }}
                />
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="预计时长（分钟）"
                shouldUpdate={(prevValues, currentValues) =>
                  prevValues.start_time !== currentValues.start_time ||
                  prevValues.end_time !== currentValues.end_time
                }
              >
                {() => {
                  const startTime = nodeForm.getFieldValue('start_time');
                  const endTime = nodeForm.getFieldValue('end_time');
                  const duration = calculateDuration(startTime, endTime);
                  return (
                    <InputNumber
                      min={0}
                      style={{ width: '100%' }}
                      placeholder="自动计算"
                      disabled
                      value={duration}
                    />
                  );
                }}
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="estimated_cost"
                label="预计费用（元）"
              >
                <InputNumber min={0} style={{ width: '100%' }} placeholder="150" />
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="lat"
                label="纬度"
              >
                <InputNumber 
                  style={{ width: '100%' }} 
                  placeholder="39.9163"
                  step={0.000001}
                  precision={6}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="lng"
                label="经度"
              >
                <InputNumber 
                  style={{ width: '100%' }} 
                  placeholder="116.3972"
                  step={0.000001}
                  precision={6}
                />
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item
            name="notes"
            label="备注"
          >
            <Input.TextArea rows={2} placeholder="其他备注信息" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TripDetail;
