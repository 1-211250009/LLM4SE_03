const Footer = () => {
  return (
    <footer style={{ 
      background: '#f8f9fa', 
      color: '#6b7280',
      padding: '16px 0',
      marginTop: 'auto',
      borderTop: '1px solid #e5e7eb'
    }}>
      <div style={{ 
        maxWidth: '1280px', 
        margin: '0 auto', 
        padding: '0 16px',
        textAlign: 'center'
      }}>
        <p style={{ margin: 0, fontSize: '14px' }}>
          &copy; 2025 旅行规划平台. 保留所有权利.
        </p>
      </div>
    </footer>
  );
};

export default Footer;
