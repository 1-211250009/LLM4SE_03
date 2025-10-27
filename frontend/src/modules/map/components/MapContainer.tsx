/**
 * 地图容器组件
 * 百度地图的主要容器组件
 */

import React, { useEffect, useRef } from 'react';
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
  className?: string;
  style?: React.CSSProperties;
}

const MapContainer: React.FC<MapContainerProps> = ({
  containerId,
  config,
  markers = [],
  routes = [],
  onMapClick,
  // onMarkerClick, // 暂时未使用
  className = '',
  style = {}
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  
  const {
    mapState,
    addMarker,
    clearMarkers,
    getMapInstance
  } = useMap(containerId, config);

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
    if (mapState.isLoading || !routes.length) return;

    const mapInstance = getMapInstance();
    if (!mapInstance) return;

    // 清除现有路线
    mapInstance.clearOverlays();

    // 重新添加标记
    markers.forEach(marker => {
      addMarker(marker);
    });

    // 添加路线
    routes.forEach((route, index) => {
      if (route.overview_polyline) {
        try {
          // 解析路线折线
          const points = route.overview_polyline.split(';').map(pointStr => {
            const [lng, lat] = pointStr.split(',').map(Number);
            return new window.BMap.Point(lng, lat);
          });

          // 创建折线
          const polyline = new window.BMap.Polyline(points, {
            strokeColor: index === 0 ? '#1890ff' : '#52c41a',
            strokeWeight: 4,
            strokeOpacity: 0.8
          });

          mapInstance.addOverlay(polyline);

          // 调整地图视野以包含路线
          if (route.bounds) {
            const bounds = new window.BMap.Bounds(
              new window.BMap.Point(route.bounds.southwest.lng, route.bounds.southwest.lat),
              new window.BMap.Point(route.bounds.northeast.lng, route.bounds.northeast.lat)
            );
            mapInstance.setViewport(bounds);
          }
        } catch (error) {
          console.error('Error drawing route:', error);
        }
      }
    });
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
