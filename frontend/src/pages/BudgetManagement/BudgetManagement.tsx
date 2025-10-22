import { Typography } from 'antd';

const { Title } = Typography;

const BudgetManagement = () => {
  return (
    <div style={{ minHeight: '100vh', background: '#f9fafb', padding: '32px 0' }}>
      <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '0 16px' }}>
        <Title level={2}>费用管理</Title>
        <p>费用管理功能正在开发中...</p>
      </div>
    </div>
  );
};

export default BudgetManagement;
