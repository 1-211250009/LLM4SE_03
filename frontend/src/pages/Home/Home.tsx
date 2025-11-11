import { Button, Card, Row, Col, Typography, Space } from 'antd';
import { GlobalOutlined, SoundOutlined, DollarOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/auth.store';

const { Title, Paragraph } = Typography;

const Home = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();

  const features = [
    // 智能行程规划功能已隐藏，但保留代码以便将来使用
    // {
    //   icon: <RocketOutlined style={{ fontSize: '48px', color: '#1890ff' }} />,
    //   title: '智能行程规划',
    //   description: '基于AI技术，为您量身定制个性化旅行路线',
    //   color: '#1890ff',
    // },
    {
      icon: <SoundOutlined style={{ fontSize: '48px', color: '#52c41a' }} />,
      title: '语音交互',
      description: '支持语音输入，让旅行规划更加便捷自然',
      color: '#52c41a',
    },
    {
      icon: <GlobalOutlined style={{ fontSize: '48px', color: '#fa8c16' }} />,
      title: '地图导航',
      description: '集成百度地图，提供精准的路线规划和导航',
      color: '#fa8c16',
    },
    {
      icon: <DollarOutlined style={{ fontSize: '48px', color: '#eb2f96' }} />,
      title: '费用管理',
      description: '智能预算分析，帮您合理控制旅行开支',
      color: '#eb2f96',
    },
  ];


  return (
    <div style={{ minHeight: '100vh' }}>
      {/* Hero Section */}
      <section style={{ 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        padding: '80px 0',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'url("data:image/svg+xml,%3Csvg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg"%3E%3Cg fill="none" fill-rule="evenodd"%3E%3Cg fill="%23ffffff" fill-opacity="0.1"%3E%3Ccircle cx="30" cy="30" r="2"/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")',
        }} />
        <div style={{ 
          maxWidth: '1280px', 
          margin: '0 auto', 
          padding: '0 16px', 
          textAlign: 'center',
          position: 'relative', 
          zIndex: 1 
        }}>
          <Title level={1} style={{ color: 'white', marginBottom: '24px', fontSize: '3.5rem', fontWeight: 'bold' }}>
            AI旅行规划师
          </Title>
          <Paragraph style={{ fontSize: '1.25rem', color: 'rgba(255,255,255,0.9)', marginBottom: '32px', maxWidth: '600px', margin: '0 auto 32px' }}>
            让AI成为您的专属旅行顾问，为您规划完美的旅程，管理旅行预算，
            让每一次出行都成为美好的回忆。
          </Paragraph>
          <Space size="large">
            {isAuthenticated ? (
              <Button
                type="primary"
                size="large"
                onClick={() => navigate('/trips')}
                style={{ 
                  background: 'white', 
                  color: '#1890ff', 
                  border: 'none',
                  height: '48px',
                  padding: '0 32px',
                  fontSize: '16px',
                  fontWeight: 'bold'
                }}
              >
                开始规划行程
              </Button>
            ) : (
              <>
                <Button
                  type="primary"
                  size="large"
                  onClick={() => navigate('/register')}
                  style={{ 
                    background: 'white', 
                    color: '#1890ff', 
                    border: 'none',
                    height: '48px',
                    padding: '0 32px',
                    fontSize: '16px',
                    fontWeight: 'bold'
                  }}
                >
                  立即注册
                </Button>
                <Button
                  size="large"
                  onClick={() => navigate('/login')}
                  style={{ 
                    border: '2px solid white', 
                    color: 'white', 
                    background: 'transparent',
                    height: '48px',
                    padding: '0 32px',
                    fontSize: '16px',
                    fontWeight: 'bold'
                  }}
                >
                  登录
                </Button>
              </>
            )}
          </Space>
        </div>
      </section>


      {/* Features Section */}
      <section style={{ padding: '80px 0', background: 'white' }}>
        <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '0 16px' }}>
          <div style={{ textAlign: 'center', marginBottom: '64px' }}>
            <Title level={2} style={{ fontSize: '2.5rem', marginBottom: '16px', color: '#1f2937' }}>
              为什么选择我们
            </Title>
            <Paragraph style={{ fontSize: '1.125rem', color: '#6b7280', maxWidth: '600px', margin: '0 auto' }}>
              我们结合了最先进的人工智能技术和丰富的旅行经验，
              为您提供最专业、最贴心的旅行规划服务。
            </Paragraph>
          </div>

          <Row gutter={[32, 32]} justify="center" style={{ maxWidth: '1200px', margin: '0 auto' }}>
            {features.map((feature, index) => (
              <Col 
                xs={24} 
                sm={24} 
                md={8} 
                lg={8} 
                xl={8}
                key={index}
                style={{
                  display: 'flex',
                  justifyContent: 'center'
                }}
              >
                <Card
                  hoverable
                  style={{ 
                    textAlign: 'center', 
                    height: '100%', 
                    border: 'none', 
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                    transition: 'all 0.3s ease',
                    borderRadius: '12px',
                    width: '100%',
                    maxWidth: '360px'
                  }}
                  bodyStyle={{ padding: '32px 24px' }}
                >
                  <div style={{ marginBottom: '24px' }}>{feature.icon}</div>
                  <Title level={4} style={{ marginBottom: '16px', color: '#1f2937' }}>
                    {feature.title}
                  </Title>
                  <Paragraph style={{ color: '#6b7280', margin: 0 }}>
                    {feature.description}
                  </Paragraph>
                </Card>
              </Col>
            ))}
          </Row>
        </div>
      </section>

      {/* CTA Section */}
      <section style={{ 
        background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        padding: '80px 0',
        color: 'white',
        textAlign: 'center'
      }}>
        <div style={{ maxWidth: '896px', margin: '0 auto', padding: '0 16px' }}>
          <Title level={2} style={{ color: 'white', marginBottom: '24px', fontSize: '2.5rem' }}>
            准备开始您的智能旅行规划之旅？
          </Title>
          <Paragraph style={{ fontSize: '1.125rem', color: 'rgba(255,255,255,0.9)', marginBottom: '32px' }}>
            立即注册，体验AI驱动的个性化旅行规划服务。
          </Paragraph>
          {!isAuthenticated && (
            <Button
              type="primary"
              size="large"
              onClick={() => navigate('/register')}
              style={{ 
                background: 'white', 
                color: '#f5576c', 
                border: 'none',
                height: '48px',
                padding: '0 32px',
                fontSize: '16px',
                fontWeight: 'bold'
              }}
            >
              免费注册
            </Button>
          )}
        </div>
      </section>
    </div>
  );
};

export default Home;
