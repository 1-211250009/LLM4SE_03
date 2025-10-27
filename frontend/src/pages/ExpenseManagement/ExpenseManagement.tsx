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
  Progress
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  DownloadOutlined,
  RobotOutlined,
  DollarOutlined
} from '@ant-design/icons';
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
  const [aiLoading, setAiLoading] = useState(false);
  const [aiMessages, setAiMessages] = useState<Array<{role: 'user' | 'assistant', content: string}>>([]);
  const [aiInput, setAiInput] = useState('');

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
    try {
      const data = await ApiService.get<TripListResponse>('/trips/?page=1&size=100');
      setTrips(data.trips || []);
      
      // 如果有tripId参数，自动选中该行程
      if (tripId) {
        const trip = data.trips?.find((t: Trip) => t.id === tripId);
        if (trip) {
          setSelectedTrip(trip);
          // 加载该行程的费用和预算数据
          loadExpenses(trip.id);
          loadBudget(trip.id);
        } else {
          message.warning('指定的行程不存在');
        }
      }
    } catch (error) {
      console.error('Failed to load trips:', error);
      message.error('加载行程失败');
    }
  };

  // 加载费用数据
  const loadExpenses = async (tripId: string) => {
    setLoading(true);
    try {
      const data = await ApiService.get<ExpenseListResponse>(`/expenses/?trip_id=${tripId}`);
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
      const data = await ApiService.get<Budget[]>(`/budgets/trips/${tripId}/budgets`);
      setBudgets(data || []);
    } catch (error) {
      console.error('Failed to load budget:', error);
      setBudgets([]);
    }
  };

  // 保存费用
  const saveExpense = async (values: any) => {
    try {
      const expenseData = {
        ...values,
        trip_id: selectedTrip?.id,
        expense_date: values.date.format('YYYY-MM-DD'),
        currency: 'CNY'
      };

      if (editingExpense) {
        await ApiService.put(`/expenses/${editingExpense.id}`, expenseData);
        message.success('费用更新成功');
      } else {
        if (!selectedTrip) {
          message.error('请先选择行程');
          return;
        }
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
    } catch (error) {
      console.error('Failed to save expense:', error);
      message.error('保存失败');
    }
  };

  // 删除费用
  const deleteExpense = async (id: string) => {
    try {
      await ApiService.delete(`/expenses/${id}`);
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
    setEditingExpense(expense);
    expenseForm.setFieldsValue({
      ...expense,
      date: dayjs(expense.expense_date)
    });
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
    if (!aiInput.trim() || !selectedTrip) return;

    setAiLoading(true);
    const userMessage = aiInput.trim();
    setAiInput('');

    // 添加用户消息
    setAiMessages(prev => [...prev, { role: 'user', content: userMessage }]);

    try {
      // 发送请求到后端AI服务
      const data = await ApiService.post<AIQueryResponse>('/expenses/ai/query', {
        query: userMessage,
        trip_id: selectedTrip.id,
        context: {
          trip_title: selectedTrip.title,
          expenses: expenses,
          budgets: budgets,
          statistics: statistics
        }
      });

      setAiMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
      
      // 如果AI执行了操作，刷新数据
      if (data.action_performed) {
        loadExpenses(selectedTrip.id);
        loadBudget(selectedTrip.id);
      }
    } catch (error) {
      console.error('AI query failed:', error);
      message.error('AI查询失败');
      setAiMessages(prev => [...prev, { 
        role: 'assistant', 
        content: '抱歉，AI助手暂时无法响应，请稍后再试。' 
      }]);
    } finally {
      setAiLoading(false);
    }
  };

  // 表格列定义
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
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true
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
      title: '地点',
      dataIndex: 'location',
      key: 'location',
      width: 120,
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
            placeholder={trips.length === 0 ? "正在加载行程..." : "请选择行程"}
            style={{ width: 300 }}
            value={selectedTrip?.id}
            loading={trips.length === 0}
            onChange={(tripId) => {
              const trip = trips.find(t => t.id === tripId);
              setSelectedTrip(trip || null);
              if (trip) {
                loadExpenses(trip.id);
                loadBudget(trip.id);
                navigate(`/expense-management?tripId=${tripId}`);
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
      {trips.length === 0 ? (
        <Card>
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Text type="secondary">正在加载行程数据...</Text>
          </div>
        </Card>
      ) : selectedTrip ? (
        <>
          {/* 统计概览 */}
          <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="总支出"
                  value={statistics.totalSpent}
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
                  value={selectedTrip.budget ? selectedTrip.budget - statistics.totalSpent : 0}
                  prefix="¥"
                  precision={2}
                  valueStyle={{ color: selectedTrip.budget && selectedTrip.budget - statistics.totalSpent < 0 ? '#cf1322' : '#3f8600' }}
                />
              </Card>
            </Col>
          </Row>

          {/* 预算进度 */}
          {selectedTrip.budget && (
            <Card style={{ marginBottom: '24px' }}>
              <Title level={4}>预算进度</Title>
              <Progress
                percent={Math.min((statistics.totalSpent / selectedTrip.budget) * 100, 100)}
                status={statistics.totalSpent > selectedTrip.budget ? 'exception' : 'active'}
                format={(percent) => `${percent?.toFixed(1)}%`}
              />
              <div style={{ marginTop: '8px', display: 'flex', justifyContent: 'space-between' }}>
                <Text type="secondary">已用：¥{statistics.totalSpent.toFixed(2)}</Text>
                <Text type="secondary">预算：¥{selectedTrip.budget.toFixed(2)}</Text>
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
                  <Button
                    icon={<DownloadOutlined />}
                    onClick={() => message.info('导出功能开发中')}
                  >
                    导出数据
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
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Text type="secondary">请选择一个行程以查看和管理费用</Text>
          </div>
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
            <DatePicker style={{ width: '100%' }} />
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
              disabled={aiLoading}
            />
            <Button
              type="primary"
              onClick={handleAiQuery}
              loading={aiLoading}
              disabled={!aiInput.trim()}
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