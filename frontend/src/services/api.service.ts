import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { useAuthStore } from '../store/auth.store';

// API 基础配置
// - 生产环境(容器/Nginx)：同源 + Nginx 代理 `/api/`，避免 CORS
// - 开发环境(vite)：可通过 VITE_API_BASE_URL 指向后端，例如 http://localhost:8000
const API_PREFIX = '/api/v1';
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '';
const RESOLVED_BASE_URL = API_BASE ? `${API_BASE}${API_PREFIX}` : `${API_PREFIX}`;

// 创建 axios 实例
const apiClient: AxiosInstance = axios.create({
  baseURL: RESOLVED_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 添加认证token
apiClient.interceptors.request.use(
  (config) => {
    const { accessToken } = useAuthStore.getState();
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器 - 处理错误和token刷新
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // 如果是401错误且没有重试过
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const { refreshToken, login } = useAuthStore.getState();
        if (refreshToken) {
          // 尝试刷新token
          const response = await axios.post(`${RESOLVED_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token, refresh_token, user } = response.data;
          login({ access_token, refresh_token, user });

          // 重新发送原始请求
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // 刷新失败，清除认证信息
        useAuthStore.getState().logout();
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

// 通用API方法
export class ApiService {
  static async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await apiClient.get(url, config);
    return response.data;
  }

  static async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await apiClient.post(url, data, config);
    return response.data;
  }

  static async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await apiClient.put(url, data, config);
    return response.data;
  }

  static async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await apiClient.delete(url, config);
    return response.data;
  }

  static async patch<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await apiClient.patch(url, data, config);
    return response.data;
  }
}

export default apiClient;
