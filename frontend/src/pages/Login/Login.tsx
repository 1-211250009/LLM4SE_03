import { Form, Input, Button, Card, Typography, message, Space } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/auth.store';
import { AuthService } from '../../services/auth.service';
import { LoginRequest } from '../../types/api.types';

const { Title, Text } = Typography;

const Login = () => {
  const navigate = useNavigate();
  const { login, setLoading } = useAuthStore();
  const [form] = Form.useForm();

  const handleSubmit = async (values: LoginRequest) => {
    try {
      setLoading(true);
      const authData = await AuthService.login(values);
      login(authData);
      message.success('登录成功！');
      navigate('/');
    } catch (error: any) {
      message.error(error.response?.data?.message || '登录失败，请检查邮箱和密码');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      height: '100vh', 
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center', 
      padding: '16px',
      overflow: 'hidden',
      boxSizing: 'border-box',
      position: 'relative'
    }}>
      {/* 背景装饰 */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'url("data:image/svg+xml,%3Csvg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg"%3E%3Cg fill="none" fill-rule="evenodd"%3E%3Cg fill="%23ffffff" fill-opacity="0.1"%3E%3Ccircle cx="30" cy="30" r="2"/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")',
        zIndex: 0
      }} />
      <div style={{ 
        maxWidth: '448px', 
        width: '100%',
        maxHeight: 'calc(100vh - 80px)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        position: 'relative',
        zIndex: 1,
        padding: '20px 0'
      }}>
        <div style={{ textAlign: 'center', marginBottom: '20px' }}>
          <Link to="/" style={{ textDecoration: 'none' }}>
            <Title level={2} style={{ 
              color: 'white', 
              marginBottom: '6px', 
              fontSize: '28px',
              fontWeight: 'bold',
              textShadow: '0 2px 4px rgba(0,0,0,0.3)',
              cursor: 'pointer',
              transition: 'all 0.3s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'scale(1.05)';
              e.currentTarget.style.textShadow = '0 4px 8px rgba(0,0,0,0.4)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'scale(1)';
              e.currentTarget.style.textShadow = '0 2px 4px rgba(0,0,0,0.3)';
            }}>
              AI旅行规划师
            </Title>
          </Link>
          <Text style={{ 
            color: 'rgba(255,255,255,0.9)', 
            fontSize: '16px',
            textShadow: '0 1px 2px rgba(0,0,0,0.3)'
          }}>登录您的账户</Text>
        </div>

        <Card style={{ 
          boxShadow: '0 20px 40px rgba(0,0,0,0.2)',
          borderRadius: '16px',
          background: 'rgba(255,255,255,0.95)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255,255,255,0.2)'
        }}>
          <Form
            form={form}
            name="login"
            onFinish={handleSubmit}
            layout="vertical"
            size="large"
            style={{ padding: '16px' }}
          >
            <Form.Item
              name="email"
              label="邮箱地址"
              rules={[
                { required: true, message: '请输入邮箱地址' },
                { type: 'email', message: '请输入有效的邮箱地址' },
              ]}
              style={{ marginBottom: '12px' }}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="请输入邮箱地址"
                style={{ height: '40px' }}
              />
            </Form.Item>

            <Form.Item
              name="password"
              label="密码"
              rules={[
                { required: true, message: '请输入密码' },
                { min: 6, message: '密码至少6位' },
              ]}
              style={{ marginBottom: '16px' }}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="请输入密码"
                style={{ height: '40px' }}
              />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                style={{ 
                  width: '100%',
                  height: '48px',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '16px',
                  fontWeight: 'bold',
                  boxShadow: '0 4px 12px rgba(102, 126, 234, 0.4)'
                }}
                loading={useAuthStore((state) => state.isLoading)}
              >
                登录
              </Button>
            </Form.Item>
          </Form>

          <div style={{ textAlign: 'center', marginTop: '12px' }}>
            <Space>
              <Text>还没有账户？</Text>
              <Link 
                to="/register" 
                style={{ 
                  color: '#667eea', 
                  textDecoration: 'none',
                  fontWeight: 'bold',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.color = '#764ba2';
                  e.currentTarget.style.textShadow = '0 2px 4px rgba(102, 126, 234, 0.3)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.color = '#667eea';
                  e.currentTarget.style.textShadow = 'none';
                }}
              >
                立即注册
              </Link>
            </Space>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Login;
