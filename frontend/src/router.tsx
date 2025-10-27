import { createBrowserRouter, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/auth.store';
import Layout from './components/layout/Layout';
import Home from './pages/Home/Home';
import Login from './pages/Login/Login';
import Register from './pages/Register/Register';
import TripPlanning from './pages/TripPlanning/TripPlanning';
import TripDetail from './pages/TripDetail/TripDetail';
import TripManagement from './pages/TripManagement/TripManagement';
import ExpenseManagement from './pages/ExpenseManagement/ExpenseManagement';
import BudgetManagement from './pages/BudgetManagement/BudgetManagement';
import Profile from './pages/Profile/Profile';

// 受保护的路由组件
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

// 公开路由组件（已登录用户重定向到首页）
const PublicRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuthStore();
  return !isAuthenticated ? <>{children}</> : <Navigate to="/" replace />;
};

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      {
        index: true,
        element: <Home />,
      },
      {
        path: 'trip-planning',
        element: (
          <ProtectedRoute>
            <TripPlanning />
          </ProtectedRoute>
        ),
      },
      {
        path: 'trips',
        element: (
          <ProtectedRoute>
            <TripManagement />
          </ProtectedRoute>
        ),
      },
      {
        path: 'trip/:id',
        element: (
          <ProtectedRoute>
            <TripDetail />
          </ProtectedRoute>
        ),
      },
      {
        path: 'expense-management',
        element: (
          <ProtectedRoute>
            <ExpenseManagement />
          </ProtectedRoute>
        ),
      },
      {
        path: 'budget/:tripId',
        element: (
          <ProtectedRoute>
            <BudgetManagement />
          </ProtectedRoute>
        ),
      },
      {
        path: 'profile',
        element: (
          <ProtectedRoute>
            <Profile />
          </ProtectedRoute>
        ),
      },
    ],
  },
  {
    path: '/login',
    element: (
      <PublicRoute>
        <Login />
      </PublicRoute>
    ),
  },
  {
    path: '/register',
    element: (
      <PublicRoute>
        <Register />
      </PublicRoute>
    ),
  },
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
]);
