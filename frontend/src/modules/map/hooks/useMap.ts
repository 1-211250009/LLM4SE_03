/**
 * 地图Hook
 * 管理地图实例和状态
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { mapService } from '../services/baidu-map.service';
import { MapConfig, MapState, Point, MapMarker, TripInfo, TripStep, MarkerSelection } from '../types/map.types';

export function useMap(containerId: string, config: MapConfig) {
  const [mapState, setMapState] = useState<MapState>({
    center: config.center,
    zoom: config.zoom,
    markers: [],
    routes: [],
    currentTrip: undefined,
    tripSteps: [],
    selectedMarkers: [],
    isLoading: true,
    error: undefined
  });

  const mapInstanceRef = useRef<any>(null);
  const markersRef = useRef<MapMarker[]>([]);

  /**
   * 初始化地图
   */
  const initializeMap = useCallback(async () => {
    try {
      setMapState(prev => ({ ...prev, isLoading: true, error: undefined }));

      // 初始化百度地图API
      await mapService.initialize();

      // 获取容器元素
      const container = document.getElementById(containerId);
      if (!container) {
        throw new Error(`Map container with id "${containerId}" not found`);
      }

      // 创建地图实例
      const map = mapService.createMap(container, config.center, config.zoom);
      mapInstanceRef.current = map;

      // 监听地图事件
      map.addEventListener('click', (e: any) => {
        const point: Point = {
          lat: e.latlng.lat,
          lng: e.latlng.lng
        };
        console.log('Map clicked:', point);
      });

      map.addEventListener('zoomend', () => {
        const center = map.getCenter();
        const zoom = map.getZoom();
        setMapState(prev => ({
          ...prev,
          center: { lat: center.lat, lng: center.lng },
          zoom
        }));
      });

      map.addEventListener('moveend', () => {
        const center = map.getCenter();
        setMapState(prev => ({
          ...prev,
          center: { lat: center.lat, lng: center.lng }
        }));
      });

      setMapState(prev => ({
        ...prev,
        isLoading: false,
        error: undefined
      }));

    } catch (error) {
      console.error('Failed to initialize map:', error);
      setMapState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to initialize map'
      }));
    }
  }, [containerId, config]);

  /**
   * 添加标记
   */
  const addMarker = useCallback((marker: MapMarker) => {
    if (!mapInstanceRef.current) return;

    const bdPoint = new window.BMap.Point(marker.position.lng, marker.position.lat);
    const bdMarker = new window.BMap.Marker(bdPoint);
    
    if (marker.title) {
      bdMarker.setTitle(marker.title);
    }

    if (marker.content) {
      const infoWindow = new window.BMap.InfoWindow(marker.content);
      bdMarker.addEventListener('click', () => {
        mapInstanceRef.current.openInfoWindow(infoWindow, bdPoint);
      });
    }

    mapInstanceRef.current.addOverlay(bdMarker);
    markersRef.current.push(marker);

    // 自动聚焦到新添加的标记
    mapInstanceRef.current.setCenter(bdPoint);
    mapInstanceRef.current.setZoom(15); // 设置合适的缩放级别

    setMapState(prev => ({
      ...prev,
      markers: [...prev.markers, marker]
    }));
  }, []);

  /**
   * 移除标记
   */
  const removeMarker = useCallback((markerId: string) => {
    if (!mapInstanceRef.current) return;

    const markerIndex = markersRef.current.findIndex(m => m.id === markerId);
    if (markerIndex === -1) return;

    // 从地图上移除标记
    const overlays = mapInstanceRef.current.getOverlays();
    overlays.forEach((overlay: any) => {
      if (overlay.getPosition && 
          overlay.getPosition().lat === markersRef.current[markerIndex].position.lat &&
          overlay.getPosition().lng === markersRef.current[markerIndex].position.lng) {
        mapInstanceRef.current.removeOverlay(overlay);
      }
    });

    // 从状态中移除
    markersRef.current.splice(markerIndex, 1);
    setMapState(prev => ({
      ...prev,
      markers: prev.markers.filter(m => m.id !== markerId)
    }));
  }, []);

  /**
   * 清除所有标记
   */
  const clearMarkers = useCallback(() => {
    if (!mapInstanceRef.current) return;

    mapInstanceRef.current.clearOverlays();
    markersRef.current = [];
    setMapState(prev => ({
      ...prev,
      markers: []
    }));
  }, []);

  /**
   * 设置地图中心
   */
  const setCenter = useCallback((center: Point, zoom?: number) => {
    if (!mapInstanceRef.current) return;

    const bdPoint = new window.BMap.Point(center.lng, center.lat);
    if (zoom) {
      mapInstanceRef.current.centerAndZoom(bdPoint, zoom);
    } else {
      mapInstanceRef.current.setCenter(bdPoint);
    }

    setMapState(prev => ({
      ...prev,
      center,
      zoom: zoom || prev.zoom
    }));
  }, []);

  /**
   * 设置缩放级别
   */
  const setZoom = useCallback((zoom: number) => {
    if (!mapInstanceRef.current) return;

    mapInstanceRef.current.setZoom(zoom);
    setMapState(prev => ({
      ...prev,
      zoom
    }));
  }, []);

  /**
   * 获取地图实例
   */
  const getMapInstance = useCallback(() => {
    return mapInstanceRef.current;
  }, []);

  /**
   * 销毁地图
   */
  const destroyMap = useCallback(() => {
    if (mapInstanceRef.current) {
      mapInstanceRef.current.clearOverlays();
      mapInstanceRef.current = null;
    }
    markersRef.current = [];
    setMapState({
      center: config.center,
      zoom: config.zoom,
      markers: [],
      routes: [],
      currentTrip: undefined,
      tripSteps: [],
      selectedMarkers: [],
      isLoading: false,
      error: undefined
    });
  }, [config]);

  // 初始化地图
  useEffect(() => {
    initializeMap();

    return () => {
      destroyMap();
    };
  }, [initializeMap, destroyMap]);

  /**
   * 创建行程
   */
  const createTrip = useCallback((tripInfo: Omit<TripInfo, 'id'>) => {
    const trip: TripInfo = {
      ...tripInfo,
      id: `trip_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    };
    
    setMapState(prev => ({
      ...prev,
      currentTrip: trip,
      tripSteps: []
    }));
    
    return trip;
  }, []);

  /**
   * 添加行程步骤
   */
  const addTripStep = useCallback((step: Omit<TripStep, 'id'>) => {
    const newStep: TripStep = {
      ...step,
      id: `step_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    };
    
    setMapState(prev => ({
      ...prev,
      tripSteps: [...prev.tripSteps, newStep]
    }));
    
    // 添加POI标记
    addMarker({
      id: newStep.poi.id,
      position: newStep.poi.location,
      title: newStep.poi.name,
      content: `
        <div style="padding: 8px;">
          <h4>${newStep.poi.name}</h4>
          <p>${newStep.poi.address}</p>
          <p>步骤 ${newStep.order}</p>
          ${newStep.notes ? `<p>备注: ${newStep.notes}</p>` : ''}
        </div>
      `,
      poi: newStep.poi
    });
    
    return newStep;
  }, [addMarker]);

  /**
   * 显示完整行程
   */
  const displayTrip = useCallback((trip: TripInfo) => {
    setMapState(prev => ({
      ...prev,
      currentTrip: trip,
      tripSteps: []
    }));
    
    // 清除现有标记
    clearMarkers();
    
    // 添加所有POI标记
    trip.waypoints.forEach((poi, index) => {
      addMarker({
        id: poi.id,
        position: poi.location,
        title: poi.name,
        content: `
          <div style="padding: 8px;">
            <h4>${poi.name}</h4>
            <p>${poi.address}</p>
            <p>第 ${index + 1} 站</p>
          </div>
        `,
        poi: poi
      });
    });
    
    // 添加路线
    trip.routes.forEach(route => {
      if (route.overview_polyline) {
        // 这里需要实现路线绘制逻辑
        console.log('绘制路线:', route);
      }
    });
    
    // 调整地图视野以包含所有标记
    if (trip.waypoints.length > 0) {
      const bounds = calculateBounds(trip.waypoints.map(poi => poi.location));
      if (mapInstanceRef.current && bounds) {
        mapInstanceRef.current.setViewport(bounds);
      }
    }
  }, [addMarker, clearMarkers]);

  /**
   * 计算边界
   */
  const calculateBounds = useCallback((points: Point[]) => {
    if (points.length === 0) return null;
    
    const lats = points.map(p => p.lat);
    const lngs = points.map(p => p.lng);
    
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLng = Math.min(...lngs);
    const maxLng = Math.max(...lngs);
    
    return {
      northeast: { lat: maxLat, lng: maxLng },
      southwest: { lat: minLat, lng: minLng }
    };
  }, []);

  /**
   * 清除行程
   */
  const clearTrip = useCallback(() => {
    setMapState(prev => ({
      ...prev,
      currentTrip: undefined,
      tripSteps: []
    }));
    clearMarkers();
  }, [clearMarkers]);

  /**
   * 添加标记到选择列表
   */
  const addMarkerToSelection = useCallback((marker: Omit<MarkerSelection, 'selected'>) => {
    setMapState(prev => {
      // 检查是否已存在
      const exists = prev.selectedMarkers.some(m => m.id === marker.id);
      if (exists) return prev;
      
      return {
        ...prev,
        selectedMarkers: [...prev.selectedMarkers, { ...marker, selected: false }]
      };
    });
  }, []);

  /**
   * 切换标记选择状态
   */
  const toggleMarkerSelection = useCallback((markerId: string) => {
    setMapState(prev => ({
      ...prev,
      selectedMarkers: prev.selectedMarkers.map(marker =>
        marker.id === markerId
          ? { ...marker, selected: !marker.selected }
          : marker
      )
    }));
  }, []);

  /**
   * 清除所有标记选择
   */
  const clearMarkerSelection = useCallback(() => {
    setMapState(prev => ({
      ...prev,
      selectedMarkers: prev.selectedMarkers.map(marker => ({
        ...marker,
        selected: false
      }))
    }));
  }, []);

  /**
   * 获取选中的标记
   */
  const getSelectedMarkers = useCallback(() => {
    return mapState.selectedMarkers.filter(marker => marker.selected);
  }, [mapState.selectedMarkers]);

  return {
    mapState,
    addMarker,
    removeMarker,
    clearMarkers,
    setCenter,
    setZoom,
    getMapInstance,
    destroyMap,
    // 行程相关方法
    createTrip,
    addTripStep,
    displayTrip,
    clearTrip,
    // 标记选择相关方法
    addMarkerToSelection,
    toggleMarkerSelection,
    clearMarkerSelection,
    getSelectedMarkers
  };
}
