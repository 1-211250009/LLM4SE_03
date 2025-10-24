/**
 * 地图模块类型定义
 */

// 坐标点
export interface Point {
  lat: number;
  lng: number;
}

// 地图配置
export interface MapConfig {
  center: Point;
  zoom: number;
  style?: string;
  enableScrollWheelZoom?: boolean;
  enableDragging?: boolean;
  enableDoubleClickZoom?: boolean;
  enableKeyboard?: boolean;
  enableInertialDragging?: boolean;
  enableContinuousZoom?: boolean;
  enablePinchToZoom?: boolean;
}

// POI信息
export interface POIInfo {
  id: string;
  name: string;
  address: string;
  location: Point;
  category: POICategory;
  rating?: number;
  price?: string;
  description?: string;
  photos?: string[];
  phone?: string;
  website?: string;
  openingHours?: string;
  distance?: number; // 距离用户位置的距离（米）
}

// POI分类
export type POICategory = 'attraction' | 'restaurant' | 'hotel' | 'shopping' | 'transport' | 'entertainment';

// POI搜索参数
export interface POISearchParams {
  keyword: string;
  city: string;
  category?: POICategory;
  location?: Point;
  radius?: number; // 搜索半径（米）
  limit?: number; // 返回数量限制
}

// POI搜索结果
export interface POISearchResult {
  pois: POIInfo[];
  total: number;
  page: number;
  hasMore: boolean;
}

// 路线规划参数
export interface RouteParams {
  origin: string | Point;
  destination: string | Point;
  mode: TransportMode;
  waypoints?: Point[]; // 途径点
  avoidHighways?: boolean;
  avoidTolls?: boolean;
}

// 交通方式
export type TransportMode = 'driving' | 'transit' | 'walking' | 'bicycling';

// 路线信息
export interface RouteInfo {
  distance: number; // 距离（米）
  duration: number; // 时间（秒）
  steps: RouteStep[];
  bounds: {
    northeast: Point;
    southwest: Point;
  };
  overview_polyline?: string; // 路线折线
}

// 路线步骤
export interface RouteStep {
  instruction: string;
  distance: number;
  duration: number;
  start_location: Point;
  end_location: Point;
  polyline?: string;
  travel_mode: TransportMode;
}

// 地图标记
export interface MapMarker {
  id: string;
  position: Point;
  title: string;
  content?: string;
  icon?: string;
  poi?: POIInfo;
  draggable?: boolean;
}

// 地图事件
export interface MapEvent {
  type: 'click' | 'dblclick' | 'rightclick' | 'mouseover' | 'mouseout';
  point: Point;
  pixel: { x: number; y: number };
  target?: any;
}

// 地图控件
export interface MapControl {
  type: 'navigation' | 'scale' | 'overview' | 'copyright' | 'geolocation';
  position: 'top_left' | 'top_right' | 'bottom_left' | 'bottom_right';
  visible?: boolean;
}

// 地理编码结果
export interface GeocodeResult {
  address: string;
  location: Point;
  formatted_address: string;
  address_components: {
    country: string;
    province: string;
    city: string;
    district: string;
    street: string;
    street_number: string;
  };
}

// 逆地理编码结果
export interface ReverseGeocodeResult {
  address: string;
  location: Point;
  formatted_address: string;
  business: string;
  address_components: {
    country: string;
    province: string;
    city: string;
    district: string;
    street: string;
    street_number: string;
  };
}

// 地图服务配置
export interface MapServiceConfig {
  apiKey: string;
  baseUrl: string;
  version: string;
  timeout: number;
}

// 行程信息
export interface TripInfo {
  id: string;
  name: string;
  description?: string;
  startDate?: string;
  endDate?: string;
  waypoints: POIInfo[];
  routes: RouteInfo[];
  totalDistance: number;
  totalDuration: number;
  status: 'draft' | 'planned' | 'active' | 'completed';
}

// 行程步骤
export interface TripStep {
  id: string;
  order: number;
  poi: POIInfo;
  arrivalTime?: string;
  departureTime?: string;
  duration?: number; // 停留时间（分钟）
  notes?: string;
  routeToNext?: RouteInfo;
}

// 地图标记选择状态
export interface MarkerSelection {
  id: string;
  name: string;
  coordinates: Point;
  category: POICategory;
  selected: boolean;
}

// 地图状态
export interface MapState {
  center: Point;
  zoom: number;
  markers: MapMarker[];
  routes: RouteInfo[];
  selectedPOI?: POIInfo;
  currentTrip?: TripInfo;
  tripSteps: TripStep[];
  selectedMarkers: MarkerSelection[];
  isLoading: boolean;
  error?: string;
}
