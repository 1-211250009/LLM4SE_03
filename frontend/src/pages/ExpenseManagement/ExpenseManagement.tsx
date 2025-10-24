/**
 * 费用管理页面
 */

import { useState, useEffect, useCallback } from 'react';
import { 
  Card, 
  Button, 
  Table, 
  Tag, 
  Space, 
  Modal, 
  Form, 
  Input, 
  DatePicker, 
  Select, 
  InputNumber,
  message,
  Popconfirm,
  Tooltip,
  Row,
  Col,
  Statistic
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  DollarOutlined,
  PieChartOutlined,
  CalendarOutlined
} from '@ant-design/icons';
import { useAuthStore } from '../../store/auth.store';
import { VoiceButton } from '../../modules/voice';
import { VoiceCommand } from '../../modules/voice/types/voice.types';
import dayjs from 'dayjs';

const { Option } = Select;
const { TextArea } = Input;

interface Expense {
  id: string;
  trip_id: string;
  itinerary_id?: string;
  amount: number;
  currency: string;
  category: 'transport' | 'accommodation' | 'food' | 'attraction' | 'shopping' | 'other';
  description?: string;
  location?: string;
  payment_method?: string;
  is_shared: boolean;
  shared_amount?: number;
  notes?: string;
  expense_date: string;
  created_at: string;
  updated_at?: string;
}

interface Trip {
  id: string;
  title: string;
  destination: string;
  start_date: string;
  end_date: string;
}

interface ExpenseStats {
  total_amount: number;
  category_stats: Array<{
    category: string;
    amount: number;
  }>;
  expense_days: number;
}

const ExpenseManagement = () => {
  const { accessToken } = useAuthStore();
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<ExpenseStats | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingExpense, setEditingExpense] = useState<Expense | null>(null);
  const [form] = Form.useForm();
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  });
  const [selectedTripId, setSelectedTripId] = useState<string>('');
  const [trips, setTrips] = useState<Trip[]>([]);

  // 获取行程列表
  const fetchTrips = useCallback(async () => {
    if (!accessToken) return;

    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${baseUrl}/api/v1/trips/?page=1&size=100`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });

      if (!response.ok) {
        throw new Error('获取行程列表失败');
      }

      const data = await response.json();
      setTrips(data.trips || []);
    } catch (error) {
      message.error('获取行程列表失败');
      console.error('Fetch trips error:', error);
    }
  }, [accessToken]);

  // 获取费用列表
  const fetchExpenses = useCallback(async (tripId: string, page = 1, size = 10) => {
    if (!accessToken || !tripId) return;

    try {
      setLoading(true);
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${baseUrl}/api/v1/budgets/trips/${tripId}/expenses?page=${page}&size=${size}`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });

      if (!response.ok) {
        throw new Error('获取费用列表失败');
      }

      const data = await response.json();
      setExpenses(data.expenses);
      setPagination(prev => ({
        ...prev,
        current: data.page,
        total: data.total
      }));
    } catch (error) {
      message.error('获取费用列表失败');
      console.error('Fetch expenses error:', error);
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  // 获取费用统计
  const fetchExpenseStats = useCallback(async (tripId: string) => {
    if (!accessToken || !tripId) return;

    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${baseUrl}/api/v1/budgets/trips/${tripId}/expenses/stats`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });

      if (!response.ok) {
        throw new Error('获取费用统计失败');
      }

      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Fetch expense stats error:', error);
    }
  }, [accessToken]);

  // 创建或更新费用
  const handleSubmit = async (values: any) => {
    if (!accessToken || !selectedTripId) return;

    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const url = editingExpense 
        ? `${baseUrl}/api/v1/budgets/expenses/${editingExpense.id}`
        : `${baseUrl}/api/v1/budgets/trips/${selectedTripId}/expenses`;
      
      const method = editingExpense ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({
          ...values,
          trip_id: selectedTripId,
          expense_date: values.expense_date?.toISOString()
        })
      });

      if (!response.ok) {
        throw new Error(editingExpense ? '更新费用失败' : '创建费用失败');
      }

      message.success(editingExpense ? '费用更新成功' : '费用创建成功');
      setModalVisible(false);
      setEditingExpense(null);
      form.resetFields();
      fetchExpenses(selectedTripId, pagination.current, pagination.pageSize);
      fetchExpenseStats(selectedTripId);
    } catch (error) {
      message.error(editingExpense ? '更新费用失败' : '创建费用失败');
      console.error('Submit expense error:', error);
    }
  };

  // 删除费用
  const handleDelete = async (expenseId: string) => {
    if (!accessToken || !selectedTripId) return;

    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${baseUrl}/api/v1/budgets/expenses/${expenseId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });

      if (!response.ok) {
        throw new Error('删除费用失败');
      }

      message.success('费用删除成功');
      fetchExpenses(selectedTripId, pagination.current, pagination.pageSize);
      fetchExpenseStats(selectedTripId);
    } catch (error) {
      message.error('删除费用失败');
      console.error('Delete expense error:', error);
    }
  };

  // 编辑费用
  const handleEdit = (expense: Expense) => {
    setEditingExpense(expense);
    form.setFieldsValue({
      ...expense,
      expense_date: expense.expense_date ? dayjs(expense.expense_date) : null
    });
    setModalVisible(true);
  };

  // 语音命令处理
  const handleVoiceCommand = useCallback((command: VoiceCommand) => {
    console.log('Voice command:', command);
    
    if (command.type === 'add_expense') {
      // 解析语音命令中的费用信息
      const entities = command.entities || {};
      const amount = entities.amount || 0;
      const category = entities.category || 'other';
      
      // 自动填充表单
      form.setFieldsValue({
        amount: amount,
        category: category,
        description: command.text,
        expense_date: dayjs()
      });
      
      setModalVisible(true);
      message.success('语音命令已识别，请完善费用信息');
    }
  }, [form]);

  // 表格列定义
  const columns = [
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      render: (amount: number, record: Expense) => (
        <div>
          <div style={{ fontWeight: 500, color: '#f50' }}>
            ¥{amount.toLocaleString()}
          </div>
          {record.is_shared && (
            <div style={{ fontSize: '12px', color: '#666' }}>
              分摊: ¥{record.shared_amount?.toLocaleString() || 0}
            </div>
          )}
        </div>
      )
    },
    {
      title: '类别',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => {
        const categoryConfig = {
          transport: { color: 'blue', text: '交通' },
          accommodation: { color: 'green', text: '住宿' },
          food: { color: 'orange', text: '餐饮' },
          attraction: { color: 'purple', text: '景点' },
          shopping: { color: 'pink', text: '购物' },
          other: { color: 'default', text: '其他' }
        };
        const config = categoryConfig[category as keyof typeof categoryConfig] || categoryConfig.other;
        return <Tag color={config.color}>{config.text}</Tag>;
      }
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      render: (text: string, record: Expense) => (
        <div>
          <div style={{ marginBottom: 4 }}>{text || '-'}</div>
          {record.location && (
            <div style={{ fontSize: '12px', color: '#666' }}>
              📍 {record.location}
            </div>
          )}
        </div>
      )
    },
    {
      title: '支付方式',
      dataIndex: 'payment_method',
      key: 'payment_method',
      render: (method: string) => method || '-'
    },
    {
      title: '日期',
      dataIndex: 'expense_date',
      key: 'expense_date',
      render: (date: string) => (
        <div style={{ fontSize: '12px' }}>
          <CalendarOutlined style={{ marginRight: 4 }} />
          {dayjs(date).format('YYYY-MM-DD HH:mm')}
        </div>
      )
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: Expense) => (
        <Space>
          <Tooltip title="编辑">
            <Button 
              type="text" 
              icon={<EditOutlined />} 
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除这笔费用吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button 
                type="text" 
                danger 
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      )
    }
  ];

  // 页面加载时获取数据
  useEffect(() => {
    fetchTrips();
  }, [fetchTrips]);

  useEffect(() => {
    if (selectedTripId) {
      fetchExpenses(selectedTripId);
      fetchExpenseStats(selectedTripId);
    }
  }, [selectedTripId, fetchExpenses, fetchExpenseStats]);

  return (
    <div style={{ padding: '24px' }}>
      {/* 统计概览 */}
      {stats && (
        <Row gutter={16} style={{ marginBottom: '24px' }}>
          <Col span={8}>
            <Card>
              <Statistic
                title="总支出"
                value={stats.total_amount}
                prefix={<DollarOutlined />}
                precision={2}
                suffix="元"
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="费用天数"
                value={stats.expense_days}
                prefix={<CalendarOutlined />}
                suffix="天"
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <div style={{ textAlign: 'center' }}>
                <PieChartOutlined style={{ fontSize: '24px', color: '#1890ff' }} />
                <div style={{ marginTop: '8px' }}>费用分析</div>
              </div>
            </Card>
          </Col>
        </Row>
      )}

      {/* 操作栏 */}
      <Card style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ margin: 0 }}>费用管理</h3>
            <p style={{ margin: '4px 0 0 0', color: '#666' }}>
              记录和管理您的旅行费用
            </p>
          </div>
          <Space>
            <Select
              placeholder="选择行程"
              style={{ width: 200 }}
              value={selectedTripId}
              onChange={setSelectedTripId}
              options={trips.map(trip => ({
                value: trip.id,
                label: `${trip.title} - ${trip.destination}`
              }))}
            />
            <VoiceButton
              onCommand={handleVoiceCommand}
              type="primary"
              size="middle"
            />
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              onClick={() => {
                setEditingExpense(null);
                form.resetFields();
                setModalVisible(true);
              }}
              disabled={!selectedTripId}
            >
              添加费用
            </Button>
          </Space>
        </div>
      </Card>

      {/* 费用列表 */}
      <Card>
        <Table
          columns={columns}
          dataSource={expenses}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            onChange: (page, size) => {
              fetchExpenses(selectedTripId, page, size || pagination.pageSize);
            }
          }}
        />
      </Card>

      {/* 创建/编辑费用模态框 */}
      <Modal
        title={editingExpense ? '编辑费用' : '添加费用'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setEditingExpense(null);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        width={500}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="amount"
            label="金额"
            rules={[{ required: true, message: '请输入金额' }]}
          >
            <InputNumber 
              min={0} 
              style={{ width: '100%' }}
              placeholder="请输入金额"
              addonBefore="¥"
            />
          </Form.Item>

          <Form.Item
            name="category"
            label="类别"
            rules={[{ required: true, message: '请选择类别' }]}
          >
            <Select placeholder="选择费用类别">
              <Option value="transport">交通</Option>
              <Option value="accommodation">住宿</Option>
              <Option value="food">餐饮</Option>
              <Option value="attraction">景点</Option>
              <Option value="shopping">购物</Option>
              <Option value="other">其他</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <Input placeholder="请输入费用描述" />
          </Form.Item>

          <Form.Item
            name="location"
            label="地点"
          >
            <Input placeholder="请输入地点" />
          </Form.Item>

          <Form.Item
            name="payment_method"
            label="支付方式"
          >
            <Select placeholder="选择支付方式">
              <Option value="cash">现金</Option>
              <Option value="card">银行卡</Option>
              <Option value="mobile">手机支付</Option>
              <Option value="other">其他</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="expense_date"
            label="费用日期"
            rules={[{ required: true, message: '请选择费用日期' }]}
          >
            <DatePicker 
              style={{ width: '100%' }}
              placeholder="选择费用日期"
              showTime
            />
          </Form.Item>

          <Form.Item
            name="is_shared"
            valuePropName="checked"
          >
            <input type="checkbox" /> 这是分摊费用
          </Form.Item>

          <Form.Item
            name="shared_amount"
            label="分摊金额"
          >
            <InputNumber 
              min={0} 
              style={{ width: '100%' }}
              placeholder="请输入分摊金额"
              addonBefore="¥"
            />
          </Form.Item>

          <Form.Item
            name="notes"
            label="备注"
          >
            <TextArea 
              rows={3} 
              placeholder="请输入备注" 
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ExpenseManagement;
