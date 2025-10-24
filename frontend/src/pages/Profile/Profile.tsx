import { useState, useEffect } from 'react';
import { 
  Card, 
  Avatar, 
  Button, 
  Form, 
  Input, 
  Upload, 
  message, 
  Row, 
  Col, 
  Statistic,
  Space,
  Modal,
  Typography
} from 'antd';
import { 
  UserOutlined, 
  EditOutlined, 
  CameraOutlined, 
  LockOutlined,
  CalendarOutlined,
  MailOutlined,
  PhoneOutlined
} from '@ant-design/icons';
import { useAuthStore } from '../../store/auth.store';
import { ApiService } from '../../services/api.service';

const { Title, Text } = Typography;

interface UserProfile {
  id: string;
  name: string;
  email: string;
  avatar_url?: string;
  bio?: string;
  phone?: string;
  created_at: string;
  updated_at: string;
}

interface PasswordForm {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

const Profile: React.FC = () => {
  const { user, updateUser } = useAuthStore();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [editing, setEditing] = useState(false);
  const [passwordModalVisible, setPasswordModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [passwordForm] = Form.useForm();

  // 获取用户详细信息
  const fetchProfile = async () => {
    try {
      setLoading(true);
      const profileData = await ApiService.get<UserProfile>('/auth/profile');
      
      // 处理头像URL，确保相对路径转换为完整URL
      if (profileData.avatar_url && profileData.avatar_url.startsWith('/static/')) {
        const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
        profileData.avatar_url = `${API_BASE_URL}${profileData.avatar_url}`;
      }
      
      console.log('获取到的用户信息:', profileData);
      console.log('头像URL:', profileData.avatar_url);
      
      setProfile(profileData);
    } catch (error) {
      message.error('获取用户信息失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchProfile();
    }
  }, [user]);

  // 更新用户信息
  const handleUpdateProfile = async (values: Partial<UserProfile>) => {
    try {
      setLoading(true);
      const updatedProfile = await ApiService.put<UserProfile>('/auth/profile', values);
      setProfile(updatedProfile);
      updateUser({ ...user, ...updatedProfile });
      setEditing(false);
      message.success('个人信息更新成功');
    } catch (error) {
      message.error('更新失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 修改密码
  const handleChangePassword = async (values: PasswordForm) => {
    if (values.newPassword !== values.confirmPassword) {
      message.error('两次输入的新密码不一致');
      return;
    }
    
    try {
      setLoading(true);
      await ApiService.post('/auth/change-password', {
        current_password: values.currentPassword,
        new_password: values.newPassword
      });
      message.success('密码修改成功');
      setPasswordModalVisible(false);
      passwordForm.resetFields();
    } catch (error) {
      message.error('密码修改失败，请检查原密码是否正确');
    } finally {
      setLoading(false);
    }
  };

  // 头像上传
  const handleAvatarUpload = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      setLoading(true);
      // 使用axios直接发送请求，确保Content-Type为multipart/form-data
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/upload-avatar`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${useAuthStore.getState().accessToken}`,
        },
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      let newAvatar = result.avatar_url;
      
      // 如果是相对路径，转换为完整URL
      if (newAvatar.startsWith('/static/')) {
        newAvatar = `${API_BASE_URL}${newAvatar}`;
      }
      
      console.log('更新前的profile:', profile);
      setProfile(prev => {
        const updated = prev ? { ...prev, avatar_url: newAvatar } : null;
        console.log('更新后的profile:', updated);
        return updated;
      });
      updateUser({ ...user, avatar: newAvatar });
      message.success('头像更新成功');
      
      console.log('头像上传成功，新头像URL:', newAvatar);
    } catch (error) {
      console.error('头像上传失败:', error);
      message.error('头像上传失败');
    } finally {
      setLoading(false);
    }
    return false; // 阻止默认上传
  };

  if (!profile) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      }}>
        <div style={{ textAlign: 'center', color: 'white' }}>
          <div style={{ fontSize: '24px', marginBottom: '16px' }}>加载中...</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '20px'
    }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <Title level={2} style={{ color: 'white', textAlign: 'center', marginBottom: '32px' }}>
          个人中心
        </Title>
        
        <Row gutter={[24, 24]}>
          {/* 个人信息卡片 */}
          <Col xs={24} lg={16}>
            <Card 
              style={{ 
                borderRadius: '16px',
                boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
                backdropFilter: 'blur(10px)',
                background: 'rgba(255,255,255,0.95)'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                <Title level={3} style={{ margin: 0 }}>个人信息</Title>
                <Button 
                  type="primary" 
                  icon={<EditOutlined />}
                  onClick={() => setEditing(!editing)}
                  style={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    border: 'none',
                    borderRadius: '8px'
                  }}
                >
                  {editing ? '取消编辑' : '编辑信息'}
                </Button>
              </div>

              {editing ? (
                <Form
                  form={form}
                  layout="vertical"
                  initialValues={profile}
                  onFinish={handleUpdateProfile}
                >
                  <Row gutter={16}>
                    <Col span={24}>
                      <Form.Item label="头像" name="avatar">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                          <Avatar 
                            size={80} 
                            src={profile.avatar_url} 
                            icon={<UserOutlined />}
                            style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
                          />
                          <Upload
                            beforeUpload={handleAvatarUpload}
                            showUploadList={false}
                            accept="image/*"
                          >
                            <Button icon={<CameraOutlined />}>更换头像</Button>
                          </Upload>
                        </div>
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item 
                        label="姓名" 
                        name="name" 
                        rules={[{ required: true, message: '请输入姓名' }]}
                      >
                        <Input placeholder="请输入姓名" />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item label="手机号" name="phone">
                        <Input placeholder="请输入手机号" />
                      </Form.Item>
                    </Col>
                    <Col span={24}>
                      <Form.Item label="个人简介" name="bio">
                        <Input.TextArea 
                          rows={4} 
                          placeholder="介绍一下自己吧..."
                          maxLength={200}
                          showCount
                        />
                      </Form.Item>
                    </Col>
                  </Row>
                  
                  <div style={{ textAlign: 'right', marginTop: '24px' }}>
                    <Space>
                      <Button onClick={() => setEditing(false)}>取消</Button>
                      <Button 
                        type="primary" 
                        htmlType="submit" 
                        loading={loading}
                        style={{
                          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                          border: 'none'
                        }}
                      >
                        保存
                      </Button>
                    </Space>
                  </div>
                </Form>
              ) : (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', marginBottom: '24px' }}>
                    <Avatar 
                      size={80} 
                      src={profile.avatar_url} 
                      icon={<UserOutlined />}
                      style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
                    />
                    <div style={{ marginLeft: '20px' }}>
                      <Title level={4} style={{ margin: 0 }}>{profile.name}</Title>
                      <Text type="secondary">{profile.email}</Text>
                    </div>
                  </div>
                  
                  <Row gutter={[16, 16]}>
                    <Col span={12}>
                      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
                        <MailOutlined style={{ marginRight: '8px', color: '#667eea' }} />
                        <Text strong>邮箱：</Text>
                        <Text style={{ marginLeft: '8px' }}>{profile.email}</Text>
                      </div>
                    </Col>
                    <Col span={12}>
                      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
                        <PhoneOutlined style={{ marginRight: '8px', color: '#667eea' }} />
                        <Text strong>手机：</Text>
                        <Text style={{ marginLeft: '8px' }}>{profile.phone || '未设置'}</Text>
                      </div>
                    </Col>
                    <Col span={24}>
                      <div style={{ marginBottom: '12px' }}>
                        <Text strong>个人简介：</Text>
                        <div style={{ marginTop: '8px', padding: '12px', background: '#f5f5f5', borderRadius: '8px' }}>
                          <Text>{profile.bio || '这个人很懒，什么都没有留下...'}</Text>
                        </div>
                      </div>
                    </Col>
                  </Row>
                </div>
              )}
            </Card>
          </Col>

          {/* 统计信息和操作 */}
          <Col xs={24} lg={8}>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              {/* 账户统计 */}
              <Card 
                title="账户统计" 
                style={{ 
                  borderRadius: '16px',
                  boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
                  backdropFilter: 'blur(10px)',
                  background: 'rgba(255,255,255,0.95)'
                }}
              >
                <Row gutter={16}>
                  <Col span={12}>
                    <Statistic 
                      title="注册时间" 
                      value={new Date(profile.created_at).toLocaleDateString()}
                      prefix={<CalendarOutlined />}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic 
                      title="行程数量" 
                      value={0}
                      suffix="个"
                    />
                  </Col>
                </Row>
              </Card>

              {/* 安全设置 */}
              <Card 
                title="安全设置" 
                style={{ 
                  borderRadius: '16px',
                  boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
                  backdropFilter: 'blur(10px)',
                  background: 'rgba(255,255,255,0.95)'
                }}
              >
                <Button 
                  type="default" 
                  icon={<LockOutlined />}
                  onClick={() => setPasswordModalVisible(true)}
                  style={{ width: '100%' }}
                >
                  修改密码
                </Button>
              </Card>
            </Space>
          </Col>
        </Row>
      </div>

      {/* 修改密码模态框 */}
      <Modal
        title="修改密码"
        open={passwordModalVisible}
        onCancel={() => {
          setPasswordModalVisible(false);
          passwordForm.resetFields();
        }}
        footer={null}
        style={{ borderRadius: '16px' }}
      >
        <Form
          form={passwordForm}
          layout="vertical"
          onFinish={handleChangePassword}
        >
          <Form.Item 
            label="当前密码" 
            name="currentPassword"
            rules={[{ required: true, message: '请输入当前密码' }]}
          >
            <Input.Password placeholder="请输入当前密码" />
          </Form.Item>
          
          <Form.Item 
            label="新密码" 
            name="newPassword"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '密码至少6位' }
            ]}
          >
            <Input.Password placeholder="请输入新密码" />
          </Form.Item>
          
          <Form.Item 
            label="确认新密码" 
            name="confirmPassword"
            rules={[{ required: true, message: '请确认新密码' }]}
          >
            <Input.Password placeholder="请再次输入新密码" />
          </Form.Item>
          
          <div style={{ textAlign: 'right', marginTop: '24px' }}>
            <Space>
              <Button onClick={() => setPasswordModalVisible(false)}>取消</Button>
              <Button 
                type="primary" 
                htmlType="submit" 
                loading={loading}
                style={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  border: 'none'
                }}
              >
                确认修改
              </Button>
            </Space>
          </div>
        </Form>
      </Modal>
    </div>
  );
};

export default Profile;