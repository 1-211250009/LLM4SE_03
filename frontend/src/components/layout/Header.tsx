import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Button, Dropdown, Avatar, Space } from 'antd';
import { UserOutlined, LogoutOutlined, RobotOutlined } from '@ant-design/icons';
import { useAuthStore } from '../../store/auth.store';

interface HeaderProps {
  onToggleChat?: () => void;
  isChatOpen?: boolean;
}

const Header = ({ onToggleChat, isChatOpen }: HeaderProps) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isAuthenticated, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人中心',
      onClick: () => navigate('/profile'),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ];

  return (
    <header style={{ 
      background: 'white', 
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)', 
      borderBottom: '1px solid #f0f0f0',
      position: 'sticky',
      top: 0,
      zIndex: 1000
    }}>
      <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '0 16px' }}>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: '1fr auto 1fr', 
          alignItems: 'center', 
          height: '64px',
          gap: '16px'
        }}>
          {/* Logo */}
          <Link to="/" style={{ display: 'flex', alignItems: 'center', textDecoration: 'none', justifySelf: 'start' }}>
            <div style={{ 
              fontSize: '1.5rem', 
              fontWeight: 'bold', 
              color: '#1890ff',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}>
              AI旅行规划师
            </div>
          </Link>

          {/* Navigation - 网格居中 */}
          <nav style={{ 
            display: 'flex', 
            gap: '32px', 
            justifySelf: 'center'
          }}>
            <Link
              to="/"
              style={{ 
                color: '#374151', 
                textDecoration: 'none',
                padding: '10px 20px',
                borderRadius: '8px',
                fontSize: '16px',
                fontWeight: '600',
                transition: 'all 0.3s ease',
                position: 'relative',
                background: 'transparent',
                border: '1px solid rgba(102, 126, 234, 0.3)'
              }}
              onMouseEnter={(e: React.MouseEvent<HTMLAnchorElement>) => {
                e.currentTarget.style.color = '#667eea';
                e.currentTarget.style.background = 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)';
                e.currentTarget.style.borderColor = 'rgba(102, 126, 234, 0.6)';
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.2)';
              }}
              onMouseLeave={(e: React.MouseEvent<HTMLAnchorElement>) => {
                e.currentTarget.style.color = '#374151';
                e.currentTarget.style.background = 'transparent';
                e.currentTarget.style.borderColor = 'rgba(102, 126, 234, 0.3)';
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              首页
            </Link>
            {isAuthenticated && (
              <>
                <Link
                  to="/trip-planning"
                  style={{ 
                    color: '#374151', 
                    textDecoration: 'none',
                    padding: '10px 20px',
                    borderRadius: '8px',
                    fontSize: '16px',
                    fontWeight: '600',
                    transition: 'all 0.3s ease',
                    position: 'relative',
                    background: 'transparent',
                    border: '1px solid rgba(102, 126, 234, 0.3)'
                  }}
                  onMouseEnter={(e: React.MouseEvent<HTMLAnchorElement>) => {
                    e.currentTarget.style.color = '#667eea';
                    e.currentTarget.style.background = 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)';
                    e.currentTarget.style.borderColor = 'rgba(102, 126, 234, 0.6)';
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.2)';
                  }}
                  onMouseLeave={(e: React.MouseEvent<HTMLAnchorElement>) => {
                    e.currentTarget.style.color = '#374151';
                    e.currentTarget.style.background = 'transparent';
                    e.currentTarget.style.borderColor = 'rgba(102, 126, 234, 0.3)';
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = 'none';
                  }}
                >
                  行程规划
                </Link>
                <Link
                  to="/trips"
                  style={{ 
                    color: '#374151', 
                    textDecoration: 'none',
                    padding: '10px 20px',
                    borderRadius: '8px',
                    fontSize: '16px',
                    fontWeight: '600',
                    transition: 'all 0.3s ease',
                    position: 'relative',
                    background: 'transparent',
                    border: '1px solid rgba(102, 126, 234, 0.3)'
                  }}
                  onMouseEnter={(e: React.MouseEvent<HTMLAnchorElement>) => {
                    e.currentTarget.style.color = '#667eea';
                    e.currentTarget.style.background = 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)';
                    e.currentTarget.style.borderColor = 'rgba(102, 126, 234, 0.6)';
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.2)';
                  }}
                  onMouseLeave={(e: React.MouseEvent<HTMLAnchorElement>) => {
                    e.currentTarget.style.color = '#374151';
                    e.currentTarget.style.background = 'transparent';
                    e.currentTarget.style.borderColor = 'rgba(102, 126, 234, 0.3)';
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = 'none';
                  }}
                >
                  我的行程
                </Link>
                <Link
                  to="/expense-management"
                  style={{ 
                    color: '#374151', 
                    textDecoration: 'none',
                    padding: '10px 20px',
                    borderRadius: '8px',
                    fontSize: '16px',
                    fontWeight: '600',
                    transition: 'all 0.3s ease',
                    position: 'relative',
                    background: 'transparent',
                    border: '1px solid rgba(102, 126, 234, 0.3)'
                  }}
                  onMouseEnter={(e: React.MouseEvent<HTMLAnchorElement>) => {
                    e.currentTarget.style.color = '#667eea';
                    e.currentTarget.style.background = 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)';
                    e.currentTarget.style.borderColor = 'rgba(102, 126, 234, 0.6)';
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.2)';
                  }}
                  onMouseLeave={(e: React.MouseEvent<HTMLAnchorElement>) => {
                    e.currentTarget.style.color = '#374151';
                    e.currentTarget.style.background = 'transparent';
                    e.currentTarget.style.borderColor = 'rgba(102, 126, 234, 0.3)';
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = 'none';
                  }}
                >
                  费用管理
                </Link>
              </>
            )}
          </nav>

          {/* User Actions - 网格右侧 */}
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '16px', 
            justifySelf: 'end'
          }}>
            {isAuthenticated ? (
              <>
                {/* AI助手按钮 - 只在trip-planning页面显示 */}
                {location.pathname === '/trip-planning' && onToggleChat && (
                  <Button
                    type="primary"
                    shape="circle"
                    size="middle"
                    icon={<RobotOutlined />}
                    onClick={onToggleChat}
                    style={{
                      width: '40px',
                      height: '40px',
                      boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                      background: isChatOpen ? '#52c41a' : '#1890ff',
                      border: 'none'
                    }}
                  />
                )}
                
                <Dropdown
                  menu={{ items: userMenuItems }}
                  placement="bottomRight"
                  arrow
                >
                  <Button 
                    type="text" 
                    style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '8px',
                      height: '40px',
                      padding: '0 12px',
                      borderRadius: '8px'
                    }}
                  >
                    <Avatar
                      size="small"
                      icon={<UserOutlined />}
                      src={user?.avatar}
                      style={{ background: '#1890ff' }}
                    />
                    <span style={{ fontSize: '16px', fontWeight: '600' }}>{user?.name}</span>
                  </Button>
                </Dropdown>
              </>
            ) : (
              <Space>
                <Button 
                  type="text" 
                  onClick={() => navigate('/login')}
                  style={{ 
                    height: '40px',
                    padding: '0 20px',
                    borderRadius: '8px',
                    fontWeight: '600',
                    fontSize: '16px',
                    color: '#374151',
                    transition: 'all 0.3s ease',
                    border: '1px solid rgba(102, 126, 234, 0.3)'
                  }}
                  onMouseEnter={(e: React.MouseEvent<HTMLButtonElement>) => {
                    e.currentTarget.style.color = '#667eea';
                    e.currentTarget.style.background = 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)';
                    e.currentTarget.style.borderColor = 'rgba(102, 126, 234, 0.6)';
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.2)';
                  }}
                  onMouseLeave={(e: React.MouseEvent<HTMLButtonElement>) => {
                    e.currentTarget.style.color = '#374151';
                    e.currentTarget.style.background = 'transparent';
                    e.currentTarget.style.borderColor = 'rgba(102, 126, 234, 0.3)';
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = 'none';
                  }}
                >
                  登录
                </Button>
                <Button 
                  type="primary" 
                  onClick={() => navigate('/register')}
                  style={{ 
                    height: '40px',
                    padding: '0 20px',
                    borderRadius: '8px',
                    fontWeight: '600',
                    fontSize: '16px',
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    border: 'none',
                    transition: 'all 0.3s ease',
                    boxShadow: '0 2px 8px rgba(102, 126, 234, 0.3)'
                  }}
                  onMouseEnter={(e: React.MouseEvent<HTMLButtonElement>) => {
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = '0 6px 16px rgba(102, 126, 234, 0.4)';
                    e.currentTarget.style.background = 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)';
                    e.currentTarget.style.color = '#00bfff';
                  }}
                  onMouseLeave={(e: React.MouseEvent<HTMLButtonElement>) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = '0 2px 8px rgba(102, 126, 234, 0.3)';
                    e.currentTarget.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                    e.currentTarget.style.color = 'white';
                  }}
                >
                  注册
                </Button>
              </Space>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
