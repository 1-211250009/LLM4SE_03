/**
 * 行程管理页面
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
  EyeOutlined,
  CalendarOutlined,
  DollarOutlined,
  EnvironmentOutlined,
  ClockCircleOutlined,
  WalletOutlined
} from '@ant-design/icons';
import { useAuthStore } from '../../store/auth.store';
import { VoiceButton } from '../../modules/voice';
import { VoiceCommand } from '../../modules/voice/types/voice.types';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';

// const { RangePicker } = DatePicker;
const { Option } = Select;
const { TextArea } = Input;

interface Trip {
  id: string;
  title: string;
  description?: string;
  destination?: string;
  start_date?: string;
  end_date?: string;
  duration_days: number;
  budget?: number;
  status: 'draft' | 'planned' | 'active' | 'completed' | 'cancelled';
  is_public: boolean;
  tags?: string[];
  created_at: string;
  updated_at?: string;
}

interface TripStats {
  total_trips: number;
  active_trips: number;
  completed_trips: number;
  total_expenses: number;
  average_trip_duration: number;
  most_visited_destinations: Array<{
    destination: string;
    count: number;
  }>;
}

const TripManagement = () => {
  const { accessToken } = useAuthStore();
  const navigate = useNavigate();
  const [trips, setTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<TripStats | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingTrip, setEditingTrip] = useState<Trip | null>(null);
  const [form] = Form.useForm();
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  });

  // 获取行程列表
  const fetchTrips = useCallback(async (page = 1, size = 10) => {
    if (!accessToken) return;

    try {
      setLoading(true);
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${baseUrl}/api/v1/trips?page=${page}&size=${size}`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });

      if (!response.ok) {
        throw new Error('获取行程列表失败');
      }

      const data = await response.json();
      setTrips(data.trips);
      setPagination(prev => ({
        ...prev,
        current: data.page,
        total: data.total
      }));
    } catch (error) {
      message.error('获取行程列表失败');
      console.error('Fetch trips error:', error);
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  // 获取统计信息
  const fetchStats = useCallback(async () => {
    if (!accessToken) return;

    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${baseUrl}/api/v1/trips/stats/overview`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });

      if (!response.ok) {
        throw new Error('获取统计信息失败');
      }

      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Fetch stats error:', error);
    }
  }, [accessToken]);

  // 创建或更新行程
  const handleSubmit = async (values: any) => {
    if (!accessToken) return;

    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const url = editingTrip 
        ? `${baseUrl}/api/v1/trips/${editingTrip.id}`
        : `${baseUrl}/api/v1/trips`;
      
      const method = editingTrip ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({
          ...values,
          start_date: values.start_date?.toISOString(),
          end_date: values.end_date?.toISOString(),
          tags: values.tags || []
        })
      });

      if (!response.ok) {
        throw new Error(editingTrip ? '更新行程失败' : '创建行程失败');
      }

      message.success(editingTrip ? '行程更新成功' : '行程创建成功');
      setModalVisible(false);
      setEditingTrip(null);
      form.resetFields();
      fetchTrips(pagination.current, pagination.pageSize);
      fetchStats();
    } catch (error) {
      message.error(editingTrip ? '更新行程失败' : '创建行程失败');
      console.error('Submit trip error:', error);
    }
  };

  // 删除行程
  const handleDelete = async (tripId: string) => {
    if (!accessToken) return;

    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${baseUrl}/api/v1/trips/${tripId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });

      if (!response.ok) {
        throw new Error('删除行程失败');
      }

      message.success('行程删除成功');
      fetchTrips(pagination.current, pagination.pageSize);
      fetchStats();
    } catch (error) {
      message.error('删除行程失败');
      console.error('Delete trip error:', error);
    }
  };

  // 编辑行程
  const handleEdit = (trip: Trip) => {
    setEditingTrip(trip);
    form.setFieldsValue({
      ...trip,
      start_date: trip.start_date ? dayjs(trip.start_date) : null,
      end_date: trip.end_date ? dayjs(trip.end_date) : null
    });
    setModalVisible(true);
  };

  // 查看行程详情
  const handleView = (trip: Trip) => {
    navigate(`/trip/${trip.id}`);
  };

  // 语音命令处理
  const handleVoiceCommand = useCallback((command: VoiceCommand) => {
    console.log('Voice command:', command);
    
    if (command.type === 'plan_trip') {
      // 解析语音命令中的行程信息
      const entities = command.entities || {};
      const locations = entities.locations || [];
      const duration = entities.duration || 1;
      const budget = entities.budget || 0;
      
      // 自动填充表单
      form.setFieldsValue({
        title: `语音创建的行程 - ${locations.join(', ')}`,
        destination: locations[0] || '',
        duration_days: duration,
        budget: budget,
        description: `通过语音创建的行程，包含地点：${locations.join(', ')}`
      });
      
      setModalVisible(true);
      message.success('语音命令已识别，请完善行程信息');
    }
  }, [form]);

  // 表格列定义
  const columns = [
    {
      title: '行程标题',
      dataIndex: 'title',
      key: 'title',
      render: (text: string, record: Trip) => (
        <div>
          <div style={{ fontWeight: 500, marginBottom: 4 }}>{text}</div>
          {record.destination && (
            <div style={{ fontSize: '12px', color: '#666' }}>
              <EnvironmentOutlined style={{ marginRight: 4 }} />
              {record.destination}
            </div>
          )}
        </div>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusConfig = {
          draft: { color: 'default', text: '草稿' },
          planned: { color: 'blue', text: '已规划' },
          active: { color: 'green', text: '进行中' },
          completed: { color: 'success', text: '已完成' },
          cancelled: { color: 'error', text: '已取消' }
        };
        const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.draft;
        return <Tag color={config.color}>{config.text}</Tag>;
      }
    },
    {
      title: '时间',
      dataIndex: 'start_date',
      key: 'time',
      render: (startDate: string, record: Trip) => (
        <div>
          {startDate && (
            <div style={{ fontSize: '12px' }}>
              <CalendarOutlined style={{ marginRight: 4 }} />
              {dayjs(startDate).format('YYYY-MM-DD')}
            </div>
          )}
          <div style={{ fontSize: '12px', color: '#666' }}>
            <ClockCircleOutlined style={{ marginRight: 4 }} />
            {record.duration_days}天
          </div>
        </div>
      )
    },
    {
      title: '预算',
      dataIndex: 'budget',
      key: 'budget',
      render: (budget: number) => (
        budget ? (
          <div style={{ fontSize: '12px' }}>
            <DollarOutlined style={{ marginRight: 4 }} />
            ¥{budget.toLocaleString()}
          </div>
        ) : '-'
      )
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      render: (tags: string[]) => (
        <div>
          {tags?.slice(0, 2).map(tag => (
            <Tag key={tag} style={{ marginBottom: 2 }}>
              {tag}
            </Tag>
          ))}
          {tags?.length > 2 && (
            <Tag>+{tags.length - 2}</Tag>
          )}
        </div>
      )
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: Trip) => (
        <Space>
          <Tooltip title="查看详情">
            <Button 
              type="text" 
              icon={<EyeOutlined />} 
              onClick={() => handleView(record)}
            />
          </Tooltip>
          <Tooltip title="费用管理">
            <Button 
              type="text" 
              icon={<WalletOutlined />} 
              onClick={() => navigate(`/expense-management?tripId=${record.id}`)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button 
              type="text" 
              icon={<EditOutlined />} 
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除这个行程吗？"
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
    fetchStats();
  }, [fetchTrips, fetchStats]);

  return (
    <div style={{ padding: '24px' }}>
      {/* 统计卡片 */}
      {stats && (
        <Row gutter={16} style={{ marginBottom: '24px' }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="总行程数"
                value={stats.total_trips}
                prefix={<CalendarOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="进行中"
                value={stats.active_trips}
                prefix={<ClockCircleOutlined />}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="已完成"
                value={stats.completed_trips}
                prefix={<CalendarOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="总支出"
                value={stats.total_expenses}
                prefix={<DollarOutlined />}
                precision={2}
                suffix="元"
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 操作栏 */}
      <Card style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ margin: 0 }}>我的行程</h3>
            <p style={{ margin: '4px 0 0 0', color: '#666' }}>
              管理您的旅行计划和行程安排
            </p>
          </div>
          <Space>
            <VoiceButton
              onCommand={handleVoiceCommand}
              type="primary"
              size="middle"
            />
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              onClick={() => {
                setEditingTrip(null);
                form.resetFields();
                setModalVisible(true);
              }}
            >
              新建行程
            </Button>
          </Space>
        </div>
      </Card>

      {/* 行程列表 */}
      <Card>
        <Table
          columns={columns}
          dataSource={trips}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            onChange: (page, size) => {
              fetchTrips(page, size || pagination.pageSize);
            }
          }}
        />
      </Card>

      {/* 创建/编辑行程模态框 */}
      <Modal
        title={editingTrip ? '编辑行程' : '新建行程'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setEditingTrip(null);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="title"
            label="行程标题"
            rules={[{ required: true, message: '请输入行程标题' }]}
          >
            <Input placeholder="请输入行程标题" />
          </Form.Item>

          <Form.Item
            name="description"
            label="行程描述"
          >
            <TextArea 
              rows={3} 
              placeholder="请输入行程描述" 
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="destination"
                label="目的地"
              >
                <Input placeholder="请输入目的地" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="duration_days"
                label="行程天数"
                rules={[{ required: true, message: '请输入行程天数' }]}
              >
                <InputNumber 
                  min={1} 
                  max={365} 
                  style={{ width: '100%' }}
                  placeholder="请输入行程天数"
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="start_date"
                label="开始日期"
              >
                <DatePicker 
                  style={{ width: '100%' }}
                  placeholder="选择开始日期"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="end_date"
                label="结束日期"
              >
                <DatePicker 
                  style={{ width: '100%' }}
                  placeholder="选择结束日期"
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="budget"
                label="预算（元）"
              >
                <InputNumber 
                  min={0} 
                  style={{ width: '100%' }}
                  placeholder="请输入预算"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="status"
                label="状态"
                initialValue="draft"
              >
                <Select placeholder="选择状态">
                  <Option value="draft">草稿</Option>
                  <Option value="planned">已规划</Option>
                  <Option value="active">进行中</Option>
                  <Option value="completed">已完成</Option>
                  <Option value="cancelled">已取消</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="tags"
            label="标签"
          >
            <Select
              mode="tags"
              placeholder="添加标签"
              style={{ width: '100%' }}
            />
          </Form.Item>

          <Form.Item
            name="is_public"
            valuePropName="checked"
          >
            <input type="checkbox" /> 公开此行程
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TripManagement;
