import { Typography } from 'antd';

const { Title } = Typography;

const Profile = () => {
  return (
    <div style={{ minHeight: '100vh', background: '#f9fafb', padding: '32px 0' }}>
      <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '0 16px' }}>
        <Title level={2}>个人中心</Title>
        <p>个人中心功能正在开发中...</p>
      </div>
    </div>
  );
};

export default Profile;
