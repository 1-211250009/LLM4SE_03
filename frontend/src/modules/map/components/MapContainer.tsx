/**
 * 地图容器组件
 * 百度地图的主要容器组件
 */

import React, { useEffect, useRef } from 'react';
import { useMap } from '../hooks/useMap';
import { MapConfig, MapMarker } from '../types/map.types';
import { Spin, Alert } from 'antd';
import './MapContainer.css';

interface MapContainerProps {
  containerId: string;
  config: MapConfig;
  markers?: MapMarker[];
  onMapClick?: (point: { lat: number; lng: number }) => void;
  onMarkerClick?: (marker: MapMarker) => void;
  className?: string;
  style?: React.CSSProperties;
}

const MapContainer: React.FC<MapContainerProps> = ({
  containerId,
  config,
  markers = [],
  onMapClick,
  onMarkerClick,
  className = '',
  style = {}
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  
  const {
    mapState,
    addMarker,
    removeMarker,
    clearMarkers,
    setCenter,
    setZoom,
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
  const handleMarkerClick = (marker: MapMarker) => {
    if (onMarkerClick) {
      onMarkerClick(marker);
    }
  };

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
