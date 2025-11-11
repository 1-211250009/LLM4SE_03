/**
 * 地图容器组件
 * 百度地图的主要容器组件
 */

import React, { useEffect, useRef} from 'react';
import { useMap } from '../hooks/useMap';
import { MapConfig, MapMarker, RouteInfo } from '../types/map.types';
import { Spin, Alert } from 'antd';
import './MapContainer.css';

interface MapContainerProps {
  containerId: string;
  config: MapConfig;
  markers?: MapMarker[];
  routes?: RouteInfo[];
  onMapClick?: (point: { lat: number; lng: number }) => void;
  onMarkerClick?: (marker: MapMarker) => void;
  onMapReady?: (focusToPoint: (point: { lat: number; lng: number }, zoom?: number) => void) => void;
  className?: string;
  style?: React.CSSProperties;
}

const MapContainer: React.FC<MapContainerProps> = ({
  containerId,
  config,
  markers = [],
  routes = [],
  onMapClick,
  onMapReady,
  // onMarkerClick, // 暂时未使用
  className = '',
  style = {}
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const onMapReadyRef = useRef(onMapReady);
  
  // 更新 ref 当 onMapReady 改变时
  useEffect(() => {
    onMapReadyRef.current = onMapReady;
  }, [onMapReady]);
  
  const {
    mapState,
    addMarker,
    clearMarkers,
    getMapInstance,
    setCenter
  } = useMap(containerId, config);
  
  // 暴露聚焦函数给外部 - 使用 ref 避免无限循环
  useEffect(() => {
    if (!mapState.isLoading && onMapReadyRef.current) {
      const focusToPoint = (point: { lat: number; lng: number }, zoom: number = 16) => {
        setCenter(point, zoom);
      };
      onMapReadyRef.current(focusToPoint);
    }
  }, [mapState.isLoading, setCenter]);

  // 处理标记变化
  useEffect(() => {
    if (mapState.isLoading) return;

    // 清除现有标记
    clearMarkers();

    // 添加新标记
    markers.forEach(marker => {
      addMarker(marker);
    });
  }, [markers, mapState.isLoading, addMarker, clearMarkers]);

  // 处理路线变化
  useEffect(() => {
    // 确保地图已完全加载
    if (mapState.isLoading || !routes.length) {
      console.log('路线绘制等待中:', { isLoading: mapState.isLoading, routesCount: routes.length });
      return;
    }

    const mapInstance = getMapInstance();
    if (!mapInstance) {
      console.warn('地图实例未准备好，延迟绘制路线');
      // 延迟重试 - 使用 forceUpdate 或直接重新执行 useEffect
      const timer = setTimeout(() => {
        const retryInstance = getMapInstance();
        if (retryInstance && routes.length > 0) {
          console.log('重试绘制路线');
          // 通过重新检查来触发绘制
          // 由于 routes 依赖项会触发重新渲染，这里不需要手动触发
        }
      }, 500);
      return () => clearTimeout(timer);
    }

    // 清除现有路线（但保留标记）
    try {
      // 只清除折线，保留标记
      const overlays = mapInstance.getOverlays();
      overlays.forEach((overlay: any) => {
        if (overlay instanceof window.BMap.Polyline) {
          mapInstance.removeOverlay(overlay);
        }
      });
    } catch (error) {
      console.warn('清除路线时出错，使用clearOverlays:', error);
      mapInstance.clearOverlays();
    }

    // 重新添加标记（如果还没有添加）
    markers.forEach(marker => {
      try {
        addMarker(marker);
      } catch (error) {
        console.error('添加标记失败:', error, marker);
      }
    });

    // 添加路线 - 使用蓝色线条显示所有路线
    console.log('开始绘制路线，路线数量:', routes.length);
    routes.forEach((route, index) => {
      console.log(`路线 ${index + 1}:`, {
        hasPolyline: !!route.overview_polyline,
        polylineLength: route.overview_polyline?.length,
        hasSteps: !!(route as any).steps,
        dayNumber: (route as any).day_number
      });
      
      let pointStrings: string[] = [];
      
      // 优先使用 overview_polyline
      if (route.overview_polyline && route.overview_polyline.trim().length > 0) {
        pointStrings = route.overview_polyline.split(';').filter(str => str.trim().length > 0);
        console.log(`路线 ${index + 1} 使用 overview_polyline，包含 ${pointStrings.length} 个点`);
      } 
      // 如果 overview_polyline 为空，尝试从 steps 中提取
      else if ((route as any).steps && Array.isArray((route as any).steps)) {
        console.log(`路线 ${index + 1} 从 steps 中提取路径点`);
        const steps = (route as any).steps;
        steps.forEach((step: any) => {
          if (step.path) {
            // step.path 格式：lng,lat;lng,lat;...（百度地图API返回的格式）
            const stepPoints = step.path.split(';').filter((str: string) => str.trim().length > 0);
            stepPoints.forEach((pointStr: string) => {
              const coords = pointStr.split(',');
              if (coords.length === 2) {
                const lng = parseFloat(coords[0].trim());  // 第一个是经度
                const lat = parseFloat(coords[1].trim());  // 第二个是纬度
                if (!isNaN(lat) && !isNaN(lng)) {
                  pointStrings.push(`${lng},${lat}`); // 保持 lng,lat 格式
                }
              }
            });
          }
        });
        console.log(`路线 ${index + 1} 从 steps 提取出 ${pointStrings.length} 个点`);
      }
      // 如果都没有，尝试使用起点和终点作为特征点（简化方案）
      else if ((route as any).origin && (route as any).destination) {
        console.log(`路线 ${index + 1} 使用起点和终点作为特征点`);
        const origin = (route as any).origin;
        const dest = (route as any).destination;
        if (origin.lng && origin.lat && dest.lng && dest.lat) {
          pointStrings.push(`${origin.lng},${origin.lat}`);
          pointStrings.push(`${dest.lng},${dest.lat}`);
        }
      }
      
      if (pointStrings.length === 0) {
        console.warn(`路线 ${index + 1} 没有有效的点数据`, route);
        return;
      }
      
      console.log(`路线 ${index + 1} 解析出 ${pointStrings.length} 个点`);
      
      try {
        const points = pointStrings.map(pointStr => {
          const parts = pointStr.split(',');
          if (parts.length !== 2) {
            throw new Error(`无效的点格式: ${pointStr}`);
          }
          const lng = parseFloat(parts[0].trim());
          const lat = parseFloat(parts[1].trim());
          
          if (isNaN(lng) || isNaN(lat)) {
            throw new Error(`无效的坐标值: ${pointStr}`);
          }
          
          return new window.BMap.Point(lng, lat);
        });

        if (points.length === 0) {
          console.warn(`路线 ${index + 1} 解析后没有有效点`);
          return;
        }

        // 使用蓝色显示所有路线
        const routeColor = '#1890ff'; // 蓝色

        // 创建折线
        const polyline = new window.BMap.Polyline(points, {
          strokeColor: routeColor,
          strokeWeight: 4,
          strokeOpacity: 0.8
        });

        mapInstance.addOverlay(polyline);
        console.log(`路线 ${index + 1} 绘制成功，包含 ${points.length} 个点`);

      } catch (error) {
        console.error(`路线 ${index + 1} 绘制失败:`, error, route);
      }
    });
    
    // 调整地图视野以包含所有标记和路线
    if (markers.length > 0) {
      try {
        const points = markers
          .filter(m => m.poi?.location)
          .map(m => new window.BMap.Point(m.poi!.location!.lng, m.poi!.location!.lat));
        
        if (points.length > 0) {
          // 使用百度地图的getViewport方法计算最佳视野
          const viewport = mapInstance.getViewport(points, {
            margins: [50, 50, 50, 50]
          });
          
          if (viewport) {
            mapInstance.centerAndZoom(viewport.center, viewport.zoom);
          }
        }
      } catch (error) {
        console.error('Error adjusting map viewport:', error);
        // 如果getViewport失败，使用简单的bounds计算
        try {
          if (markers.length > 0) {
            const points = markers
              .filter(m => m.poi?.location)
              .map(m => new window.BMap.Point(m.poi!.location!.lng, m.poi!.location!.lat));
            
            if (points.length > 0) {
              const bounds = new window.BMap.Bounds(points[0], points[0]);
              points.forEach(point => bounds.extend(point));
              mapInstance.setViewport([bounds]);
            }
          }
        } catch (fallbackError) {
          console.error('Error in fallback viewport adjustment:', fallbackError);
        }
      }
    }
  }, [routes, mapState.isLoading, markers, getMapInstance, addMarker]);

  // 处理地图点击事件
  useEffect(() => {
    const mapInstance = getMapInstance();
    if (!mapInstance || !onMapClick) return;

    const handleMapClick = (e: any) => {
      const point = {
        lat: e.latlng.lat,
        lng: e.latlng.lng
      };
      onMapClick(point);
    };

    mapInstance.addEventListener('click', handleMapClick);

    return () => {
      mapInstance.removeEventListener('click', handleMapClick);
    };
  }, [getMapInstance, onMapClick]);

  // 处理标记点击事件
  // const handleMarkerClick = (marker: MapMarker) => {
  //   if (onMarkerClick) {
  //     onMarkerClick(marker);
  //   }
  // };

  if (mapState.error) {
    return (
      <div className={`map-container ${className}`} style={style}>
        <Alert
          message="地图加载失败"
          description={mapState.error}
          type="error"
          showIcon
          style={{ margin: '20px' }}
        />
      </div>
    );
  }

  return (
    <div className={`map-container ${className}`} style={style}>
      {mapState.isLoading && (
        <div className="map-loading">
          <Spin size="large" />
          <p>正在加载地图...</p>
        </div>
      )}
      
      <div
        ref={containerRef}
        id={containerId}
        className="map-content"
        style={{
          width: '100%',
          height: '100%',
          minHeight: '400px',
          opacity: mapState.isLoading ? 0 : 1,
          transition: 'opacity 0.3s ease'
        }}
      />
      
      {/* 地图控制面板 */}
      <div className="map-controls">
        <div className="map-info">
          <span>中心: {mapState.center.lat.toFixed(4)}, {mapState.center.lng.toFixed(4)}</span>
          <span>缩放: {mapState.zoom}</span>
          <span>标记: {mapState.markers.length}</span>
        </div>
      </div>
    </div>
  );
};

export default MapContainer;
