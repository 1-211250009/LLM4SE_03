// API 响应基础类型
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  success: boolean;
}

// 分页响应类型
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

// 错误响应类型
export interface ApiError {
  message: string;
  code?: string;
  details?: any;
}

// 认证相关类型
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  created_at: string;
  updated_at: string;
}

// 行程相关类型
export interface Trip {
  id: string;
  title: string;
  description?: string;
  destination?: string;
  start_date?: string;
  end_date?: string;
  duration_days: number;
  budget_total?: number;  // 新字段
  currency: string;       // 新字段
  status: 'draft' | 'planned' | 'active' | 'completed' | 'cancelled';
  is_public?: boolean;
  tags?: string[];
  preferences?: any;
  traveler_count: number;  // 新字段
  created_at: string;
  updated_at?: string;
  user_id: string;
  itineraries?: Itinerary[];  // 改为复数
  expenses?: Expense[];
}

export interface Itinerary {
  id: string;
  trip_id: string;
  day_number: number;  // 改名
  date?: string;
  title?: string;
  description?: string;
  items: ItineraryItem[];  // 改为items
}

export interface ItineraryItem {
  id: string;
  itinerary_id: string;
  poi_id?: string;
  name: string;
  description?: string;
  address?: string;
  coordinates?: { lat: number; lng: number };
  category: string;
  start_time?: string;
  end_time?: string;
  estimated_duration?: number;
  estimated_cost?: number;
  rating?: number;
  price_level?: string;
  phone?: string;
  website?: string;
  opening_hours?: string;
  images?: string[];
  order_index: number;
  is_completed: boolean;
  notes?: string;
}

// 保留旧的Activity类型以兼容
export interface Activity {
  id: string;
  itinerary_id: string;
  title: string;
  description?: string;
  start_time: string;
  end_time: string;
  location: string;
  poi_id?: string;
  type: 'attraction' | 'restaurant' | 'hotel' | 'transport' | 'other';
  cost?: number;
  notes?: string;
}

// 费用相关类型
export interface Budget {
  id: string;
  trip_id: string;
  total_budget: number;
  spent_amount: number;
  remaining_budget?: number;  // 新增
  budget_usage_percent?: number;  // 新增
  currency?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Expense {
  id: string;
  trip_id: string;  // 改为trip_id
  budget_id?: string;
  itinerary_item_id?: string;  // 新增：关联到节点
  amount: number;
  currency?: string;
  category: 'transportation' | 'accommodation' | 'food' | 'attraction' | 'shopping' | 'entertainment' | 'other';
  description: string;
  expense_date: string;
  location?: string;
  created_at?: string;
  updated_at?: string;
}

// 地图相关类型
export interface POI {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  type: 'attraction' | 'restaurant' | 'hotel' | 'transport';
  rating?: number;
  price_level?: number;
  photos?: string[];
  description?: string;
}

export interface Route {
  id: string;
  origin: string;
  destination: string;
  distance: number;
  duration: number;
  mode: 'driving' | 'transit' | 'walking' | 'cycling';
  steps: RouteStep[];
}

export interface RouteStep {
  instruction: string;
  distance: number;
  duration: number;
  start_location: { lat: number; lng: number };
  end_location: { lat: number; lng: number };
}

// 语音相关类型
export interface VoiceConfig {
  language: 'zh-cn' | 'en-us';
  voice: string;
  speed: number;
  volume: number;
}

export interface VoiceResult {
  text: string;
  confidence: number;
  duration: number;
}

// 行程列表响应类型
export interface TripListResponse {
  trips: Trip[];
  total: number;
  page: number;
  size: number;
  has_next: boolean;
}

// 费用列表响应类型
export interface ExpenseListResponse {
  expenses: Expense[];
  total: number;
  page: number;
  size: number;
  has_next: boolean;
  total_amount: number;
}

// AI 查询响应类型
export interface AIQueryResponse {
  response: string;
  action_performed: boolean;
  pending_action?: {
    id?: string;
    function_name: string;
    arguments: string; // JSON字符串
  };
}
