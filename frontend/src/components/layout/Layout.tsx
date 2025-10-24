import { Outlet, useLocation } from 'react-router-dom';
import { useState } from 'react';
import Header from './Header';
import Footer from './Footer';

const Layout = () => {
  const location = useLocation();
  const [isChatOpen, setIsChatOpen] = useState(false);

  const handleToggleChat = () => {
    setIsChatOpen(!isChatOpen);
  };

  return (
    <div style={{ 
      minHeight: '100vh', 
      display: 'flex', 
      flexDirection: 'column',
      background: '#f9fafb'
    }}>
      <Header 
        onToggleChat={location.pathname === '/trip-planning' ? handleToggleChat : undefined}
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
