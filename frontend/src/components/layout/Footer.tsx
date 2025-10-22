const Footer = () => {
  return (
    <footer style={{ 
      background: '#1f2937', 
      color: 'white',
      padding: '32px 0',
      marginTop: 'auto'
    }}>
      <div style={{ 
        maxWidth: '1280px', 
        margin: '0 auto', 
        padding: '0 16px'
      }}>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
          gap: '32px',
          marginBottom: '32px'
        }}>
          {/* 产品信息 */}
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>
              AI旅行规划师
            </h3>
            <p style={{ color: '#d1d5db', fontSize: '14px', lineHeight: '1.5' }}>
              基于人工智能的智能旅行规划平台，为您提供个性化的行程规划和费用管理服务。
            </p>
          </div>

          {/* 功能特色 */}
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>
              功能特色
            </h3>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              <li style={{ color: '#d1d5db', fontSize: '14px', marginBottom: '8px' }}>智能行程规划</li>
              <li style={{ color: '#d1d5db', fontSize: '14px', marginBottom: '8px' }}>语音交互</li>
              <li style={{ color: '#d1d5db', fontSize: '14px', marginBottom: '8px' }}>费用管理</li>
              <li style={{ color: '#d1d5db', fontSize: '14px', marginBottom: '8px' }}>地图导航</li>
            </ul>
          </div>

          {/* 帮助支持 */}
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>
              帮助支持
            </h3>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              <li style={{ marginBottom: '8px' }}>
                <a href="#" style={{ 
                  color: '#d1d5db', 
                  fontSize: '14px', 
                  textDecoration: 'none',
                  transition: 'color 0.2s ease'
                }}
                onMouseEnter={(e) => e.currentTarget.style.color = 'white'}
                onMouseLeave={(e) => e.currentTarget.style.color = '#d1d5db'}
                >
                  使用指南
                </a>
              </li>
              <li style={{ marginBottom: '8px' }}>
                <a href="#" style={{ 
                  color: '#d1d5db', 
                  fontSize: '14px', 
                  textDecoration: 'none',
                  transition: 'color 0.2s ease'
                }}
                onMouseEnter={(e) => e.currentTarget.style.color = 'white'}
                onMouseLeave={(e) => e.currentTarget.style.color = '#d1d5db'}
                >
                  常见问题
                </a>
              </li>
              <li style={{ marginBottom: '8px' }}>
                <a href="#" style={{ 
                  color: '#d1d5db', 
                  fontSize: '14px', 
                  textDecoration: 'none',
                  transition: 'color 0.2s ease'
                }}
                onMouseEnter={(e) => e.currentTarget.style.color = 'white'}
                onMouseLeave={(e) => e.currentTarget.style.color = '#d1d5db'}
                >
                  联系客服
                </a>
              </li>
            </ul>
          </div>

          {/* 关于我们 */}
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>
              关于我们
            </h3>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              <li style={{ marginBottom: '8px' }}>
                <a href="#" style={{ 
                  color: '#d1d5db', 
                  fontSize: '14px', 
                  textDecoration: 'none',
                  transition: 'color 0.2s ease'
                }}
                onMouseEnter={(e) => e.currentTarget.style.color = 'white'}
                onMouseLeave={(e) => e.currentTarget.style.color = '#d1d5db'}
                >
                  公司介绍
                </a>
              </li>
              <li style={{ marginBottom: '8px' }}>
                <a href="#" style={{ 
                  color: '#d1d5db', 
                  fontSize: '14px', 
                  textDecoration: 'none',
                  transition: 'color 0.2s ease'
                }}
                onMouseEnter={(e) => e.currentTarget.style.color = 'white'}
                onMouseLeave={(e) => e.currentTarget.style.color = '#d1d5db'}
                >
                  隐私政策
                </a>
              </li>
              <li style={{ marginBottom: '8px' }}>
                <a href="#" style={{ 
                  color: '#d1d5db', 
                  fontSize: '14px', 
                  textDecoration: 'none',
                  transition: 'color 0.2s ease'
                }}
                onMouseEnter={(e) => e.currentTarget.style.color = 'white'}
                onMouseLeave={(e) => e.currentTarget.style.color = '#d1d5db'}
                >
                  服务条款
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div style={{ 
          borderTop: '1px solid #374151', 
          paddingTop: '32px', 
          textAlign: 'center',
          color: '#9ca3af',
          fontSize: '14px'
        }}>
          <p style={{ margin: 0 }}>&copy; 2025 AI旅行规划师. 保留所有权利.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
