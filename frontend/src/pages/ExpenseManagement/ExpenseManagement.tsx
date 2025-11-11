/**
 * 费用管理页面
 * 支持费用的增删改查、预算分析、智能管理
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Card,
  Button,
  Table,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  DatePicker,
  Space,
  Tag,
  Statistic,
  Row,
  Col,
  Typography,
  message,
  Popconfirm,
  Progress,
  Empty,
  Spin,
  Tooltip
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  RobotOutlined,
  DollarOutlined,
  AudioOutlined
} from '@ant-design/icons';
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition';
import { useAuthStore } from '../../store/auth.store';
import { useNavigate, useSearchParams } from 'react-router-dom';
// import { AGUIClient, AGUIEventHandler, AGUIEvent } from '../../utils/agui-client';
import MarkdownRenderer from '../../components/common/MarkdownRenderer';
import { ApiService } from '../../services/api.service';
import { Trip, Expense, Budget, TripListResponse, ExpenseListResponse, AIQueryResponse } from '../../types/api.types';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;
// const { TextArea } = Input;

// 费用类型
const EXPENSE_CATEGORIES = [
  { value: 'transportation', label: '交通', color: 'blue' },
  { value: 'accommodation', label: '住宿', color: 'green' },
  { value: 'food', label: '餐饮', color: 'orange' },
  { value: 'attraction', label: '景点', color: 'purple' },
  { value: 'shopping', label: '购物', color: 'red' },
  { value: 'entertainment', label: '娱乐', color: 'cyan' },
  { value: 'other', label: '其他', color: 'default' }
];


const ExpenseManagement: React.FC = () => {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const tripId = searchParams.get('tripId');
  

  // 状态管理
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [trips, setTrips] = useState<Trip[]>([]);
  const [selectedTrip, setSelectedTrip] = useState<Trip | null>(null);
  const [loading, setLoading] = useState(false);
  const [tripsLoading, setTripsLoading] = useState(true); // 添加行程列表加载状态
  const [aiLoading, setAiLoading] = useState(false);
  const [aiMessages, setAiMessages] = useState<Array<{role: 'user' | 'assistant', content: string, pendingAction?: any}>>([]);
  const [aiInput, setAiInput] = useState('');
  
  // 语音识别
  const { isRecording, isProcessing, toggleRecording } = useSpeechRecognition({
    onResult: (text) => {
      setAiInput(prev => prev + (prev ? ' ' : '') + text);
    },
    onError: (error) => {
      console.error('Speech recognition error:', error);
    }
  });

  // 模态框状态
  const [expenseModalVisible, setExpenseModalVisible] = useState(false);
  const [aiModalVisible, setAiModalVisible] = useState(false);
  const [editingExpense, setEditingExpense] = useState<Expense | null>(null);

  // 表单
  const [expenseForm] = Form.useForm();

  // 筛选状态
  const [filters, setFilters] = useState({
    category: 'all',
    dateRange: null as [dayjs.Dayjs, dayjs.Dayjs] | null,
    amountRange: [0, 10000] as [number, number]
  });

  // AG-UI客户端
  // const [aguiClient] = useState(() => new AGUIClient());
  // const eventHandlerRef = React.useRef<AGUIEventHandler | null>(null);

  // 初始化
  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }

    loadTrips();
  }, [user, tripId, navigate]);

  // 加载行程列表
  const loadTrips = async () => {
    setTripsLoading(true); // 开始加载
    try {
      const data = await ApiService.get<TripListResponse>('/trips/?page=1&size=100');
      setTrips(data.trips || []);
      
      // 如果有tripId参数，自动选中该行程并加载完整详情
      if (tripId) {
        try {
          // 加载完整的行程详情（包含itineraries和items）
          const tripDetail = await ApiService.get<Trip>(`/trips/${tripId}`);
          if (tripDetail) {
            setSelectedTrip(tripDetail);
          // 加载该行程的费用和预算数据
            loadExpenses(tripDetail.id);
            loadBudget(tripDetail.id);
        } else {
          message.warning('指定的行程不存在');
          }
        } catch (error) {
          console.error('Failed to load trip detail:', error);
          message.warning('加载行程详情失败');
        }
      }
    } catch (error) {
      console.error('Failed to load trips:', error);
      message.error('加载行程失败');
      setTrips([]); // 确保在错误时设置为空数组
    } finally {
      setTripsLoading(false); // 加载完成
    }
  };

  // 加载费用数据
  const loadExpenses = async (tripId: string) => {
    setLoading(true);
    try {
      const data = await ApiService.get<ExpenseListResponse>(`/budgets/trips/${tripId}/expenses`);
      console.log('Loaded expenses:', data.expenses);
      // 调试：检查每个费用的 itinerary_item_id
      data.expenses?.forEach((expense: Expense) => {
        console.log(`Expense ${expense.id}: itinerary_item_id =`, expense.itinerary_item_id);
      });
      setExpenses(data.expenses || []);
    } catch (error) {
      console.error('Failed to load expenses:', error);
      message.error('加载费用失败');
      setExpenses([]);
    } finally {
      setLoading(false);
    }
  };

  // 加载预算数据
  const loadBudget = async (tripId: string) => {
    try {
      const data = await ApiService.get<any>(`/budgets/trips/${tripId}/budget`);
      // 后端返回BudgetSummaryResponse，包含total_budget, spent_amount, remaining_budget等
      if (data) {
        // 将预算摘要数据存储起来
        // 注意：remaining_budget 可能为 null（当没有设置预算时），不应该转换为 0
        setBudgets([{
          id: tripId,
          trip_id: tripId,
          total_budget: data.total_budget ?? null,
          spent_amount: data.spent_amount || 0,
          remaining_budget: data.remaining_budget ?? null, // 保持 null，不要转换为 0
          budget_usage_percent: data.budget_usage_percent ?? null
        } as any]);
      }
    } catch (error) {
      console.error('Failed to load budget:', error);
      setBudgets([]);
    }
  };

  // 保存费用
  const saveExpense = async (values: any) => {
    try {
      // 构建费用数据，移除不需要的字段，确保格式正确
      let expenseData: any = {
        amount: values.amount,
        category: values.category,
        description: values.description || '',
        currency: 'CNY',
        location: values.location || null,
        payment_method: values.payment_method || null,
        receipt_image: values.receipt_image || null,
        is_shared: values.is_shared || false,
        shared_with: values.shared_with || [],
        my_share: values.my_share || null,
        notes: values.notes || null,
        tags: values.tags || [],
        // 日期格式：转换为 ISO 格式字符串，后端会自动解析为 datetime
        expense_date: values.date ? values.date.format('YYYY-MM-DD') + 'T00:00:00' : null,
        // 关联节点ID - 如果字段存在（包括 null），则包含在请求中
        // undefined 表示字段未修改（更新时），null 表示清空关联（创建或更新时）
        itinerary_item_id: 'itinerary_item_id' in values ? (values.itinerary_item_id || null) : undefined
      };

      // 数据清理：移除undefined，但保留null和空字符串（对于可选字段）
      // 特别注意：itinerary_item_id 需要保留 null 值（表示清空关联）
      const cleanedData: any = {};
      Object.keys(expenseData).forEach(key => {
        const value = expenseData[key];
        // 只移除undefined，保留其他值（包括null和空字符串）
        if (value !== undefined) {
          cleanedData[key] = value;
        }
      });
      
      // 确保必填字段有默认值
      if (cleanedData.description === undefined) {
        cleanedData.description = '';
      }
      if (cleanedData.currency === undefined) {
        cleanedData.currency = 'CNY';
      }
      if (cleanedData.is_shared === undefined) {
        cleanedData.is_shared = false;
      }
      if (cleanedData.shared_with === undefined) {
        cleanedData.shared_with = [];
      }
      if (cleanedData.tags === undefined) {
        cleanedData.tags = [];
      }
      
      expenseData = cleanedData;

      if (editingExpense) {
        // 更新费用时使用正确的路径
        await ApiService.put(`/budgets/expenses/${editingExpense.id}`, expenseData);
        message.success('费用更新成功');
      } else {
        if (!selectedTrip) {
          message.error('请先选择行程');
          return;
        }
        // 创建费用时不需要在请求体中发送 trip_id，因为它在路径参数中
        // expenseData.trip_id 会被忽略，后端会使用路径参数中的 trip_id
        await ApiService.post(`/budgets/trips/${selectedTrip.id}/expenses`, expenseData);
        message.success('费用添加成功');
      }
      
      setExpenseModalVisible(false);
      expenseForm.resetFields();
      setEditingExpense(null);
      if (selectedTrip) {
        loadExpenses(selectedTrip.id);
        loadBudget(selectedTrip.id);
      }
    } catch (error: any) {
      console.error('Failed to save expense:', error);
      const errorMessage = error.response?.data?.detail || error.message || '保存失败';
      message.error(errorMessage);
    }
  };

  // 删除费用
  const deleteExpense = async (id: string) => {
    try {
      await ApiService.delete(`/budgets/expenses/${id}`);
      message.success('费用删除成功');
      if (selectedTrip) {
        loadExpenses(selectedTrip.id);
        loadBudget(selectedTrip.id);
      }
    } catch (error) {
      console.error('Failed to delete expense:', error);
      message.error('删除失败');
    }
  };

  // 编辑费用
  const editExpense = (expense: Expense) => {
    console.log('Editing expense:', expense);
    console.log('itinerary_item_id:', expense.itinerary_item_id);
    setEditingExpense(expense);
    expenseForm.setFieldsValue({
      ...expense,
      date: dayjs(expense.expense_date),
      itinerary_item_id: expense.itinerary_item_id || undefined  // 设置关联节点ID
    });
    // 验证表单值是否正确设置
    const formValues = expenseForm.getFieldsValue();
    console.log('Form values after setFieldsValue:', formValues);
    setExpenseModalVisible(true);
  };

  // 筛选费用
  const filteredExpenses = useMemo(() => {
    return expenses.filter(expense => {
      if (filters.category && filters.category !== 'all' && expense.category !== filters.category) return false;
      if (filters.dateRange) {
        const expenseDate = dayjs(expense.expense_date);
        if (expenseDate.isBefore(filters.dateRange[0]) || expenseDate.isAfter(filters.dateRange[1])) {
          return false;
        }
      }
      if (expense.amount < filters.amountRange[0] || expense.amount > filters.amountRange[1]) {
        return false;
      }
      return true;
    });
  }, [expenses, filters]);

  // 计算统计数据
  const statistics = useMemo(() => {
    const totalSpent = filteredExpenses.reduce((sum, expense) => sum + expense.amount, 0);
    const categoryStats = EXPENSE_CATEGORIES.map(cat => {
      const categoryExpenses = filteredExpenses.filter(exp => exp.category === cat.value);
      const amount = categoryExpenses.reduce((sum, exp) => sum + exp.amount, 0);
      return {
        category: cat.label,
        amount,
        count: categoryExpenses.length,
        percentage: totalSpent > 0 ? (amount / totalSpent * 100).toFixed(1) : 0
      };
    }).filter(stat => stat.amount > 0);

    return {
      totalSpent,
      categoryStats,
      averageExpense: filteredExpenses.length > 0 ? totalSpent / filteredExpenses.length : 0,
      expenseCount: filteredExpenses.length
    };
  }, [filteredExpenses]);

  // AI费用管理
  const handleAiQuery = async () => {
    if (!aiInput.trim()) {
      message.warning('请输入您的问题');
      return;
    }
    
    if (!selectedTrip) {
      message.warning('请先选择一个行程');
      return;
    }

    setAiLoading(true);
    const userMessage = aiInput.trim();
    setAiInput('');

    // 添加用户消息
    setAiMessages(prev => [...prev, { role: 'user', content: userMessage }]);

    try {
      // 发送请求到后端AI服务（AI查询需要更长的超时时间）
      const data = await ApiService.post<AIQueryResponse>('/expenses/ai/query', {
        query: userMessage,
        trip_id: selectedTrip.id,
        context: {
          trip_title: selectedTrip.title,
          expenses: expenses || [],
          budgets: budgets || [],
          statistics: statistics || {
            totalSpent: 0,
            expenseCount: 0,
            averageExpense: 0,
            categoryStats: []
          }
        }
      }, {
        timeout: 60000 // AI查询设置为60秒超时
      });
      
      console.log('AI query response:', data);

      // 检查响应是否有效
      if (!data) {
        throw new Error('AI响应格式错误');
      }

      // 如果有待确认的操作，显示确认卡片
      // 注意：当AI触发Function Call时，response可能为空字符串，这是正常的
      if (data.pending_action) {
        // 如果有pending_action，即使response为空也显示确认卡片
        // 可以显示一个默认的提示信息
        const content = data.response || '我准备执行以下操作，请确认：';
        setAiMessages(prev => [...prev, { 
          role: 'assistant', 
          content: content,
          pendingAction: data.pending_action
        }]);
      } else {
        // 如果没有pending_action，必须有response内容
        if (!data.response || data.response.trim() === '') {
          throw new Error('AI响应内容为空');
        }
        setAiMessages(prev => [...prev, { 
          role: 'assistant', 
          content: data.response 
        }]);
      }
      
      // 如果AI执行了操作，刷新数据
      if (data.action_performed) {
        loadExpenses(selectedTrip.id);
        loadBudget(selectedTrip.id);
      }
    } catch (error: any) {
      console.error('AI query failed:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'AI查询失败';
      message.error(errorMessage);
      setAiMessages(prev => [...prev, { 
        role: 'assistant', 
        content: errorMessage || '抱歉，AI助手暂时无法响应，请稍后再试。' 
      }]);
    } finally {
      setAiLoading(false);
    }
  };

  // 执行待确认的操作
  const handleExecuteAction = async (action: any) => {
    if (!selectedTrip) return;

    try {
      const result = await ApiService.post<{success: boolean, message: string, data?: any}>('/expenses/ai/execute', {
        function_name: action.function_name,
        arguments: action.arguments,
        trip_id: selectedTrip.id
      }, {
        timeout: 60000 // AI执行操作也需要更长的超时时间
      });

      message.success(result.message || '操作执行成功');
      
      // 更新消息，移除待确认操作
      setAiMessages(prev => prev.map((msg, idx) => {
        if (idx === prev.length - 1 && msg.pendingAction) {
          return {
            ...msg,
            content: msg.content + '\n\n' + (result.message || '操作执行成功'),
            pendingAction: undefined
          };
        }
        return msg;
      }));
      
      // 刷新数据
      loadExpenses(selectedTrip.id);
      loadBudget(selectedTrip.id);
    } catch (error: any) {
      console.error('Execute action failed:', error);
      message.error(error.response?.data?.detail || '操作执行失败');
    }
  };

  // 取消待确认的操作
  const handleCancelAction = (messageIndex: number) => {
    setAiMessages(prev => prev.map((msg, idx) => {
      if (idx === messageIndex && msg.pendingAction) {
        return {
          ...msg,
          content: msg.content + '\n\n❌ 操作已取消',
          pendingAction: undefined
        };
      }
      return msg;
    }));
  };

  // 获取操作名称
  const getActionName = (functionName: string): string => {
    const actionNames: Record<string, string> = {
      'add_expense': '新增费用',
      'update_expense': '修改费用',
      'delete_expense': '删除费用',
      'get_filtered_expenses': '获取筛选的费用列表'
    };
    return actionNames[functionName] || functionName;
  };

  // 格式化操作详情
  const formatActionDetails = (action: any): string => {
    try {
      const args = JSON.parse(action.arguments);
      const details: string[] = [];
      
      if (action.function_name === 'add_expense') {
        details.push(`分类：${EXPENSE_CATEGORIES.find(c => c.value === args.category)?.label || args.category}`);
        details.push(`金额：¥${args.amount?.toFixed(2) || 0}`);
        details.push(`描述：${args.description || ''}`);
        if (args.location) details.push(`地点：${args.location}`);
        if (args.expense_date) details.push(`日期：${args.expense_date}`);
      } else if (action.function_name === 'update_expense') {
        details.push(`费用ID：${args.expense_id}`);
        if (args.category) details.push(`分类：${EXPENSE_CATEGORIES.find(c => c.value === args.category)?.label || args.category}`);
        if (args.amount) details.push(`金额：¥${args.amount.toFixed(2)}`);
        if (args.description) details.push(`描述：${args.description}`);
      } else if (action.function_name === 'delete_expense') {
        details.push(`费用ID：${args.expense_id}`);
      } else if (action.function_name === 'get_filtered_expenses') {
        if (args.category) details.push(`分类：${EXPENSE_CATEGORIES.find(c => c.value === args.category)?.label || args.category}`);
        if (args.start_date) details.push(`开始日期：${args.start_date}`);
        if (args.end_date) details.push(`结束日期：${args.end_date}`);
      }
      
      return details.join('\n') || JSON.stringify(args, null, 2);
    } catch (e) {
      return action.arguments;
    }
  };

  // 表格列定义 - 顺序：日期、分类、金额、关联节点、描述、操作
  const columns = [
    {
      title: '日期',
      dataIndex: 'expense_date',
      key: 'expense_date',
      width: 100,
      render: (date: string) => dayjs(date).format('MM-DD')
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 100,
      render: (category: string) => {
        const cat = EXPENSE_CATEGORIES.find(c => c.value === category);
        return <Tag color={cat?.color}>{cat?.label || category}</Tag>;
      }
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 100,
      render: (amount: number) => `¥${amount.toFixed(2)}`,
      sorter: (a: Expense, b: Expense) => a.amount - b.amount
    },
    {
      title: '关联节点',
      key: 'itinerary_item',
      width: 200,
      ellipsis: true,
      render: (_: any, record: Expense) => {
        // 调试信息
        console.log('Rendering itinerary_item for expense:', record.id, 'itinerary_item_id:', record.itinerary_item_id);
        console.log('selectedTrip?.itineraries:', selectedTrip?.itineraries);
        
        if (!record.itinerary_item_id) {
          console.log('No itinerary_item_id for expense:', record.id);
          return <span style={{ color: '#999' }}>-</span>;
        }
        
        if (!selectedTrip?.itineraries || selectedTrip.itineraries.length === 0) {
          console.log('No itineraries in selectedTrip');
          return <span style={{ color: '#999' }}>-</span>;
        }
        
        // 查找关联的节点
        for (const itinerary of selectedTrip.itineraries) {
          if (!itinerary.items || itinerary.items.length === 0) {
            continue;
          }
          const item = itinerary.items.find((it: any) => it.id === record.itinerary_item_id);
          if (item) {
            console.log('Found item:', item.name, 'in day', itinerary.day_number);
            return (
              <Tooltip title={`第${itinerary.day_number}天 - ${item.name}`}>
                <span>{item.name}</span>
              </Tooltip>
            );
          }
        }
        console.log('Item not found for itinerary_item_id:', record.itinerary_item_id);
        return <span style={{ color: '#999' }}>-</span>;
      }
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      width: 150,
      ellipsis: true
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: Expense) => (
        <Space size="small">
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => editExpense(record)}
            size="small"
          />
          <Popconfirm
            title="确定删除这笔费用吗？"
            onConfirm={() => deleteExpense(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              size="small"
            />
          </Popconfirm>
        </Space>
      )
    }
  ];

  if (!user) {
    return null;
  }

  return (
    <div style={{ padding: '24px', background: '#f5f5f5', minHeight: '100vh' }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: '24px' }}>
        <Title level={2} style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '12px' }}>
          <DollarOutlined />
          费用管理
        </Title>
      </div>

      {/* 行程选择 */}
      <Card style={{ marginBottom: '24px' }}>
        <Space wrap>
          <Text strong>选择行程：</Text>
          <Select
            placeholder={tripsLoading ? "正在加载行程..." : "请选择行程"}
            style={{ width: 300 }}
            value={selectedTrip?.id}
            loading={tripsLoading}
            disabled={tripsLoading || trips.length === 0}
            onChange={async (tripId) => {
              try {
                // 加载完整的行程详情（包含itineraries和items）
                const tripDetail = await ApiService.get<Trip>(`/trips/${tripId}`);
                setSelectedTrip(tripDetail || null);
                if (tripDetail) {
                  loadExpenses(tripDetail.id);
                  loadBudget(tripDetail.id);
                  navigate(`/expense-management?tripId=${tripId}`);
                }
              } catch (error) {
                console.error('Failed to load trip detail:', error);
              const trip = trips.find(t => t.id === tripId);
              setSelectedTrip(trip || null);
              if (trip) {
                loadExpenses(trip.id);
                loadBudget(trip.id);
                navigate(`/expense-management?tripId=${tripId}`);
                }
              }
            }}
          >
            {trips.map(trip => (
              <Option key={trip.id} value={trip.id}>
                {trip.title} ({trip.destination || '未设置目的地'})
              </Option>
            ))}
          </Select>
          {tripId && !selectedTrip && trips.length > 0 && (
            <Text type="warning">指定的行程不存在或已被删除</Text>
          )}
        </Space>
      </Card>


      {/* 显示加载状态或内容 */}
      {tripsLoading ? (
        <Card>
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin size="large" />
            <div style={{ marginTop: '16px' }}>
            <Text type="secondary">正在加载行程数据...</Text>
            </div>
          </div>
        </Card>
      ) : trips.length === 0 ? (
        <Card>
          <Empty 
            description="暂无行程数据"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Button 
              type="primary" 
              onClick={() => navigate('/trips')}
            >
              去创建行程
            </Button>
          </Empty>
        </Card>
      ) : selectedTrip ? (
        <>
          {/* 统计概览 */}
          <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="总支出"
                  value={budgets[0]?.spent_amount !== undefined ? budgets[0].spent_amount : statistics.totalSpent}
                  prefix="¥"
                  precision={2}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="费用笔数"
                  value={statistics.expenseCount}
                  suffix="笔"
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="平均支出"
                  value={statistics.averageExpense}
                  prefix="¥"
                  precision={2}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="剩余预算"
                  value={(() => {
                    // 优先使用后端返回的准确值
                    if (budgets[0]?.remaining_budget !== null && budgets[0]?.remaining_budget !== undefined) {
                      return budgets[0].remaining_budget;
                    }
                    // 如果后端没有返回 remaining_budget，使用后端返回的 spent_amount 计算（更准确）
                    if (budgets[0]?.spent_amount !== undefined && selectedTrip?.budget_total) {
                      return selectedTrip.budget_total - budgets[0].spent_amount;
                    }
                    // 最后回退到使用前端统计（基于筛选后的费用，可能不准确）
                    if (selectedTrip?.budget_total) {
                      return selectedTrip.budget_total - statistics.totalSpent;
                    }
                    return 0;
                  })()}
                  prefix="¥"
                  precision={2}
                  valueStyle={{ 
                    color: (() => {
                      // 计算剩余预算值
                      const remaining = budgets[0]?.remaining_budget !== null && budgets[0]?.remaining_budget !== undefined
                        ? budgets[0].remaining_budget
                        : (budgets[0]?.spent_amount !== undefined && selectedTrip?.budget_total
                          ? selectedTrip.budget_total - budgets[0].spent_amount
                          : (selectedTrip?.budget_total ? selectedTrip.budget_total - statistics.totalSpent : 0));
                      return remaining < 0 ? '#cf1322' : '#3f8600';
                    })()
                  }}
                />
              </Card>
            </Col>
          </Row>

          {/* 预算进度 */}
          {selectedTrip.budget_total && (
            <Card style={{ marginBottom: '24px' }}>
              <Title level={4}>预算进度</Title>
              <Progress
                percent={(() => {
                  const spent = budgets[0]?.spent_amount !== undefined ? budgets[0].spent_amount : statistics.totalSpent;
                  return Math.min((spent / selectedTrip.budget_total) * 100, 100);
                })()}
                status={(() => {
                  const spent = budgets[0]?.spent_amount !== undefined ? budgets[0].spent_amount : statistics.totalSpent;
                  return spent > selectedTrip.budget_total ? 'exception' : 'active';
                })()}
                format={(percent) => `${percent?.toFixed(1)}%`}
              />
              <div style={{ marginTop: '8px', display: 'flex', justifyContent: 'space-between' }}>
                <Text type="secondary">已用：¥{((budgets[0]?.spent_amount !== undefined ? budgets[0].spent_amount : statistics.totalSpent).toFixed(2))}</Text>
                <Text type="secondary">预算：¥{selectedTrip.budget_total.toFixed(2)}</Text>
              </div>
            </Card>
          )}

          {/* 费用分类统计 */}
          <Card style={{ marginBottom: '24px' }}>
            <Title level={4}>费用分类统计</Title>
            <Row gutter={[16, 16]}>
              {statistics.categoryStats.map(stat => (
                <Col xs={24} sm={12} md={8} lg={6} key={stat.category}>
                  <Card size="small">
                    <div style={{ textAlign: 'center' }}>
                      <Text strong style={{ fontSize: '16px' }}>{stat.category}</Text>
                      <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#1890ff', margin: '8px 0' }}>
                        ¥{stat.amount.toFixed(2)}
                      </div>
                      <Text type="secondary">{stat.count}笔 • {stat.percentage}%</Text>
                    </div>
                  </Card>
                </Col>
              ))}
            </Row>
          </Card>

          {/* 操作栏 */}
          <Card style={{ marginBottom: '24px' }}>
            <Row justify="space-between" align="middle">
              <Col>
                <Space wrap>
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={() => {
                      setEditingExpense(null);
                      expenseForm.resetFields();
                      setExpenseModalVisible(true);
                    }}
                  >
                    添加费用
                  </Button>
                  <Button
                    icon={<RobotOutlined />}
                    onClick={() => setAiModalVisible(true)}
                  >
                    AI费用助手
                  </Button>
                </Space>
              </Col>
              <Col>
                <Space wrap>
                  <Select
                    placeholder="分类筛选"
                    style={{ width: 120 }}
                    value={filters.category}
                    onChange={(value) => setFilters(prev => ({ ...prev, category: value }))}
                  >
                    <Option value="all">全部</Option>
                    {EXPENSE_CATEGORIES.map(cat => (
                      <Option key={cat.value} value={cat.value}>{cat.label}</Option>
                    ))}
                  </Select>
                  <RangePicker
                    placeholder={['开始日期', '结束日期']}
                    value={filters.dateRange}
                    onChange={(dates) => setFilters(prev => ({ ...prev, dateRange: dates as [dayjs.Dayjs, dayjs.Dayjs] | null }))}
                  />
                </Space>
              </Col>
            </Row>
          </Card>

          {/* 费用列表 */}
          <Card>
            <Table
              columns={columns}
              dataSource={filteredExpenses}
              rowKey="id"
              loading={loading}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 条记录`
              }}
            />
          </Card>
        </>
      ) : (
        <Card>
          <Empty 
            description="请选择一个行程以查看和管理费用"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        </Card>
      )}

      {/* 添加/编辑费用模态框 */}
      <Modal
        title={editingExpense ? '编辑费用' : '添加费用'}
        open={expenseModalVisible}
        onCancel={() => {
          setExpenseModalVisible(false);
          setEditingExpense(null);
          expenseForm.resetFields();
        }}
        onOk={() => expenseForm.submit()}
        width={600}
      >
        <Form
          form={expenseForm}
          layout="vertical"
          onFinish={saveExpense}
        >
          <Form.Item
            name="category"
            label="费用分类"
            rules={[{ required: true, message: '请选择费用分类' }]}
          >
            <Select placeholder="请选择分类">
              {EXPENSE_CATEGORIES.map(cat => (
                <Option key={cat.value} value={cat.value}>
                  <Tag color={cat.color}>{cat.label}</Tag>
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="amount"
            label="金额"
            rules={[{ required: true, message: '请输入金额' }]}
          >
            <InputNumber
              style={{ width: '100%' }}
              placeholder="请输入金额"
              min={0}
              precision={2}
              formatter={(value) => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
            />
          </Form.Item>
          
          {/* 节点关联 - 新增 */}
          <Form.Item
            name="itinerary_item_id"
            label="关联行程节点（可选）"
            tooltip="将此费用关联到具体的行程节点，例如景点门票、餐厅账单等。选择节点后，费用日期将自动设置为节点所在日期。"
          >
            <Select
              placeholder="选择关联的行程节点"
              allowClear
              showSearch
              optionFilterProp="children"
              onChange={(value) => {
                console.log('itinerary_item_id changed to:', value);
                // 当选择节点时，自动设置费用日期为节点所在日期
                if (value && selectedTrip?.itineraries) {
                  for (const itinerary of selectedTrip.itineraries) {
                    const item = itinerary.items?.find((it: any) => it.id === value);
                    if (item && itinerary.date) {
                      // 设置费用日期为节点所在日期
                      expenseForm.setFieldsValue({
                        date: dayjs(itinerary.date)
                      });
                      break;
                    }
                  }
                }
              }}
            >
              {selectedTrip?.itineraries?.map((itinerary: any) => (
                <Select.OptGroup key={itinerary.id} label={`第${itinerary.day_number}天 - ${itinerary.title || ''} ${itinerary.date ? `(${dayjs(itinerary.date).format('YYYY-MM-DD')})` : ''}`}>
                  {itinerary.items?.map((item: any) => (
                    <Option key={item.id} value={item.id}>
                      {item.name} {item.category && `(${item.category})`}
                    </Option>
                  ))}
                </Select.OptGroup>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
            rules={[{ required: true, message: '请输入费用描述' }]}
          >
            <Input placeholder="请输入费用描述" />
          </Form.Item>

          <Form.Item
            name="date"
            label="日期"
            rules={[{ required: true, message: '请选择日期' }]}
          >
            <DatePicker 
              style={{ width: '100%' }}
              disabledDate={(current) => {
                // 限制日期选择范围在行程的开始日期和结束日期之间（含开始和结束日期）
                if (!selectedTrip?.start_date || !selectedTrip?.end_date) {
                  return false;
                }
                const startDate = dayjs(selectedTrip.start_date);
                const endDate = dayjs(selectedTrip.end_date);
                return current && (current.isBefore(startDate, 'day') || current.isAfter(endDate, 'day'));
              }}
            />
          </Form.Item>

          <Form.Item
            name="location"
            label="地点"
          >
            <Input placeholder="请输入地点（可选）" />
          </Form.Item>
        </Form>
      </Modal>

      {/* AI费用助手模态框 */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <RobotOutlined />
            AI费用助手
          </div>
        }
        open={aiModalVisible}
        onCancel={() => setAiModalVisible(false)}
        footer={null}
        width={800}
      >
        <div style={{ height: '500px', display: 'flex', flexDirection: 'column' }}>
          {/* AI对话区域 */}
          <div style={{ 
            flex: 1, 
            border: '1px solid #d9d9d9', 
            borderRadius: '6px', 
            padding: '16px', 
            marginBottom: '16px',
            overflowY: 'auto',
            background: '#fafafa'
          }}>
            {aiMessages.length === 0 ? (
              <div style={{ textAlign: 'center', color: '#999', marginTop: '100px' }}>
                <RobotOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                <div>我是您的费用管理助手，可以帮您：</div>
                <div>• 分析费用支出情况</div>
                <div>• 提供预算建议</div>
                <div>• 智能分类费用</div>
                <div>• 生成费用报告</div>
              </div>
            ) : (
              aiMessages.map((msg, index) => (
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
                          <Text>{getActionName(msg.pendingAction.function_name)}</Text>
                        </div>
                        <div style={{ marginBottom: '12px' }}>
                          <Text strong>操作详情：</Text>
                          <div style={{ 
                            marginTop: '8px', 
                            padding: '8px', 
                            background: '#fff', 
                            borderRadius: '4px',
                            fontFamily: 'monospace',
                            fontSize: '12px'
                          }}>
                            {formatActionDetails(msg.pendingAction)}
                          </div>
                        </div>
                        <Space>
                          <Button 
                            type="primary" 
                            size="small"
                            onClick={() => handleExecuteAction(msg.pendingAction)}
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
            {aiLoading && (
              <div style={{ textAlign: 'center', color: '#999' }}>
                <div>AI正在思考中...</div>
              </div>
            )}
          </div>

          {/* 输入区域 */}
          <div style={{ display: 'flex', gap: '8px' }}>
            <Input
              value={aiInput}
              onChange={(e) => setAiInput(e.target.value)}
              placeholder="请输入您的问题，例如：分析我的交通费用支出情况"
              onPressEnter={handleAiQuery}
              disabled={aiLoading || isProcessing}
              suffix={
                <Button
                  type="text"
                  icon={<AudioOutlined />}
                  onClick={toggleRecording}
                  loading={isProcessing}
                  danger={isRecording}
                  style={{ border: 'none', padding: 0 }}
                />
              }
            />
            <Button
              type="primary"
              onClick={handleAiQuery}
              loading={aiLoading}
              disabled={!aiInput.trim() || isProcessing}
            >
              发送
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default ExpenseManagement;