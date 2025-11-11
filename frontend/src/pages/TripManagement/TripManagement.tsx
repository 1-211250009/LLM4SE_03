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
import TripAIAssistant from '../../components/trip/TripAIAssistant';
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
  budget_total?: number;
  currency?: string;
  traveler_count?: number;
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

  // 计算行程天数
  const calculateDurationDays = (startDate: dayjs.Dayjs | null, endDate: dayjs.Dayjs | null): number => {
    if (!startDate || !endDate) return 1;
    // 计算天数：结束日期 - 开始日期 + 1
    // 例如：2025-11-11 到 2025-11-11 是1天
    const diff = endDate.diff(startDate, 'day');
    return Math.max(1, diff + 1);
  };

  // 创建或更新行程
  const handleSubmit = async (values: any) => {
    if (!accessToken) return;

    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const url = editingTrip 
        ? `${baseUrl}/api/v1/trips/${editingTrip.id}`
        : `${baseUrl}/api/v1/trips`;
      
      const method = editingTrip ? 'PUT' : 'POST';
      
      // 自动计算行程天数
      const durationDays = calculateDurationDays(values.start_date, values.end_date);
      
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
          duration_days: durationDays,  // 使用计算得到的天数
          tags: values.tags || [],
          budget_total: values.budget_total || null,
          currency: values.currency || 'CNY',
          traveler_count: values.traveler_count || 1,
          preferences: values.preferences || {}
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
      end_date: trip.end_date ? dayjs(trip.end_date) : null,
      budget_total: trip.budget_total || null,
      currency: trip.currency || 'CNY',
      traveler_count: trip.traveler_count || 1
    });
    setModalVisible(true);
  };

  // 查看行程详情
  const handleView = (trip: Trip) => {
    navigate(`/trip/${trip.id}`);
  };

  // 处理AI创建的行程
  const handleTripCreated = useCallback(() => {
    message.success('行程创建成功！');
    // 刷新行程列表
    fetchTrips(pagination.current, pagination.pageSize);
    fetchStats();
    // 可选：跳转到行程详情页
    // navigate(`/trip/${tripId}`);
  }, [fetchTrips, fetchStats, pagination]);

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
      dataIndex: 'budget_total',
      key: 'budget_total',
      render: (budget_total: number) => (
        budget_total ? (
          <div style={{ fontSize: '12px' }}>
            <DollarOutlined style={{ marginRight: 4 }} />
            ¥{budget_total.toLocaleString()}
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
            <TripAIAssistant onTripCreated={handleTripCreated} />
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
                label="行程天数"
              >
                <Input
                  style={{ width: '100%' }}
                  value={
                    form.getFieldValue('start_date') && form.getFieldValue('end_date')
                      ? `${calculateDurationDays(form.getFieldValue('start_date'), form.getFieldValue('end_date'))} 天`
                      : '自动计算'
                  }
                  disabled
                  placeholder="自动计算"
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="start_date"
                label="开始日期"
                rules={[{ required: true, message: '请选择开始日期' }]}
              >
                <DatePicker 
                  style={{ width: '100%' }}
                  format="YYYY-MM-DD"
                  placeholder="选择开始日期"
                  onChange={() => {
                    // 当开始日期改变时，触发表单更新
                    form.setFieldsValue({});
                  }}
                  disabledDate={(current) => {
                    // 结束日期不能早于开始日期
                    const endDate = form.getFieldValue('end_date');
                    if (endDate && current && current.isAfter(endDate, 'day')) {
                      return true;
                    }
                    return false;
                  }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="end_date"
                label="结束日期"
                rules={[{ required: true, message: '请选择结束日期' }]}
              >
                <DatePicker 
                  style={{ width: '100%' }}
                  format="YYYY-MM-DD"
                  placeholder="选择结束日期"
                  onChange={() => {
                    // 当结束日期改变时，触发表单更新
                    form.setFieldsValue({});
                  }}
                  disabledDate={(current) => {
                    // 结束日期不能早于开始日期
                    const startDate = form.getFieldValue('start_date');
                    if (startDate && current && current.isBefore(startDate, 'day')) {
                      return true;
                    }
                    return false;
                  }}
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="budget_total"
                label="总预算"
              >
                <InputNumber 
                  min={0} 
                  style={{ width: '100%' }}
                  placeholder="请输入预算金额"
                  addonAfter="元"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="traveler_count"
                label="同行人数"
                initialValue={1}
              >
                <InputNumber 
                  min={1}
                  max={100}
                  style={{ width: '100%' }}
                  placeholder="同行人数"
                  addonAfter="人"
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="currency"
                label="货币单位"
                initialValue="CNY"
              >
                <Select placeholder="选择货币">
                  <Option value="CNY">人民币 (CNY)</Option>
                  <Option value="USD">美元 (USD)</Option>
                  <Option value="EUR">欧元 (EUR)</Option>
                  <Option value="JPY">日元 (JPY)</Option>
                  <Option value="HKD">港币 (HKD)</Option>
                </Select>
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
