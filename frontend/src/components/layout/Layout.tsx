import { Outlet } from 'react-router-dom';
import { useState } from 'react';
import Header from './Header';
import Footer from './Footer';

const Layout = () => {
  const [isChatOpen, setIsChatOpen] = useState(false);

  return (
    <div style={{ 
      minHeight: '100vh', 
      display: 'flex', 
      flexDirection: 'column',
      background: '#f9fafb'
    }}>
      {/* 行程规划页面已隐藏，但保留代码以便将来使用 */}
      <Header 
        onToggleChat={undefined} // location.pathname === '/trip-planning' ? handleToggleChat : undefined
        isChatOpen={isChatOpen}
      />
      <main style={{ flex: 1, minHeight: 0 }}>
        <Outlet context={{ isChatOpen, setIsChatOpen }} />
      </main>
      <Footer />
    </div>
  );
};

export default Layout;
