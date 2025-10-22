import { ApiService } from './api.service';
import { LoginRequest, RegisterRequest, AuthResponse, User } from '../types/api.types';

export class AuthService {
  // 用户登录
  static async login(credentials: LoginRequest): Promise<AuthResponse> {
    return ApiService.post<AuthResponse>('/auth/login', credentials);
  }

  // 用户注册
  static async register(userData: RegisterRequest): Promise<AuthResponse> {
    return ApiService.post<AuthResponse>('/auth/register', userData);
  }

  // 刷新token
  static async refreshToken(refreshToken: string): Promise<AuthResponse> {
    return ApiService.post<AuthResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    });
  }

  // 获取当前用户信息
  static async getCurrentUser(): Promise<User> {
    return ApiService.get<User>('/auth/me');
  }

  // 更新用户信息
  static async updateUser(userId: string, userData: Partial<User>): Promise<User> {
    return ApiService.put<User>(`/auth/users/${userId}`, userData);
  }

  // 修改密码
  static async changePassword(
    userId: string,
    currentPassword: string,
    newPassword: string
  ): Promise<void> {
    return ApiService.post<void>(`/auth/users/${userId}/change-password`, {
      current_password: currentPassword,
      new_password: newPassword,
    });
  }

  // 登出
  static async logout(): Promise<void> {
    return ApiService.post<void>('/auth/logout');
  }
}
