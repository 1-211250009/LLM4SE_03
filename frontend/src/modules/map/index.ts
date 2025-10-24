/**
 * 地图模块入口文件
 * 导出所有地图相关的组件、Hooks和类型
 */

// 组件
export { default as MapContainer } from './components/MapContainer';
export { default as POIMarker } from './components/POIMarker';
export { default as POISearch } from './components/POISearch';

// Hooks
export { useMap } from './hooks/useMap';
export { usePOISearch } from './hooks/usePOISearch';
export { useRouteCalc } from './hooks/useRouteCalc';

// 服务
export { mapService, BaiduMapService } from './services/baidu-map.service';

// 类型
export type {
  Point,
  MapConfig,
  MapState,
  MapMarker,
  POIInfo,
  POICategory,
  POISearchParams,
  POISearchResult,
  RouteParams,
  RouteInfo,
  RouteStep,
  TransportMode,
  GeocodeResult,
  ReverseGeocodeResult,
  MapServiceConfig,
  TripInfo,
  TripStep
} from './types/map.types';
