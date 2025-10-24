/**
 * 地图测试页面
 * 用于测试地图模块功能
 */

import React, { useState } from 'react';
import { Card, Button, Space, message } from 'antd';
import { MapContainer, POISearch } from '../../modules/map';
import { MapConfig, MapMarker, POIInfo } from '../../modules/map/types/map.types';

const MapTest: React.FC = () => {
  const [mapMarkers, setMapMarkers] = useState<MapMarker[]>([]);

  // 地图配置
  const mapConfig: MapConfig = {
    center: { lat: 39.9042, lng: 116.4074 }, // 北京天安门
    zoom: 12,
    enableScrollWheelZoom: true,
    enableDragging: true,
    enableDoubleClickZoom: true,
    enableKeyboard: true,
    enableInertialDragging: true,
    enableContinuousZoom: true,
    enablePinchToZoom: true
  };

  // 处理POI选择
  const handlePOISelect = (poi: POIInfo) => {
    message.success(`选择了POI: ${poi.name}`);
    
    // 添加POI标记到地图
    const marker: MapMarker = {
      id: poi.id,
      position: poi.location,
      title: poi.name,
      content: `
        <div style="padding: 8px;">
          <h4 style="margin: 0 0 4px 0; font-size: 14px;">${poi.name}</h4>
          <p style="margin: 0; font-size: 12px; color: #666;">${poi.address}</p>
          ${poi.rating ? `<p style="margin: 4px 0 0 0; font-size: 12px; color: #ffa500;">⭐ ${poi.rating}</p>` : ''}
        </div>
      `,
      poi
    };
    
    setMapMarkers(prev => {
      // 移除相同ID的标记
      const filtered = prev.filter(m => m.id !== poi.id);
      return [...filtered, marker];
    });
  };

  // 清除所有标记
  const clearMarkers = () => {
    setMapMarkers([]);
    message.info('已清除所有标记');
  };

  return (
    <div style={{ padding: '20px', height: 'calc(100vh - 64px)' }}>
      <Card title="地图模块测试" style={{ height: '100%' }}>
        <div style={{ display: 'flex', height: 'calc(100% - 60px)', gap: '16px' }}>
          {/* 地图区域 */}
          <div style={{ flex: 1 }}>
            <MapContainer
              containerId="map-test-container"
              config={mapConfig}
              markers={mapMarkers}
              style={{ height: '100%' }}
            />
          </div>
          
          {/* POI搜索区域 */}
          <div style={{ width: '300px' }}>
            <Card title="POI搜索" size="small" style={{ height: '100%' }}>
              <POISearch
                onPOISelect={handlePOISelect}
                style={{ height: 'calc(100% - 40px)' }}
              />
            </Card>
          </div>
        </div>
        
        {/* 控制按钮 */}
        <div style={{ marginTop: '16px' }}>
          <Space>
            <Button onClick={clearMarkers}>
              清除标记
            </Button>
            <Button type="primary" onClick={() => message.info('地图功能正常')}>
              测试地图
            </Button>
          </Space>
        </div>
      </Card>
    </div>
  );
};

export default MapTest;
