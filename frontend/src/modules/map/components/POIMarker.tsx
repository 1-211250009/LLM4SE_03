/**
 * POI标记组件
 * 显示POI信息的标记
 */

import React from 'react';
import { POIInfo } from '../types/map.types';
import { StarOutlined, PhoneOutlined, GlobalOutlined } from '@ant-design/icons';
import './POIMarker.css';

interface POIMarkerProps {
  poi: POIInfo;
  onClick?: (poi: POIInfo) => void;
  className?: string;
}

const POIMarker: React.FC<POIMarkerProps> = ({
  poi,
  onClick,
  className = ''
}) => {
  const handleClick = () => {
    if (onClick) {
      onClick(poi);
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'attraction':
        return '🏛️';
      case 'restaurant':
        return '🍽️';
      case 'hotel':
        return '🏨';
      case 'shopping':
        return '🛍️';
      case 'transport':
        return '🚇';
      case 'entertainment':
        return '🎭';
      default:
        return '📍';
    }
  };

  const getCategoryName = (category: string) => {
    const categoryMap: { [key: string]: string } = {
      'attraction': '景点',
      'restaurant': '餐厅',
      'hotel': '酒店',
      'shopping': '购物',
      'transport': '交通',
      'entertainment': '娱乐'
    };
    return categoryMap[category] || '其他';
  };

  return (
    <div 
      className={`poi-marker ${className}`}
      onClick={handleClick}
    >
      <div className="poi-marker-content">
        <div className="poi-marker-header">
          <span className="poi-category-icon">
            {getCategoryIcon(poi.category)}
          </span>
          <div className="poi-info">
            <h4 className="poi-name">{poi.name}</h4>
            <span className="poi-category">
              {getCategoryName(poi.category)}
            </span>
          </div>
          {poi.rating && (
            <div className="poi-rating">
              <StarOutlined />
              <span>{poi.rating.toFixed(1)}</span>
            </div>
          )}
        </div>
        
        <div className="poi-marker-body">
          <p className="poi-address">{poi.address}</p>
          
          {poi.price && (
            <div className="poi-price">
              <span className="price-label">价格:</span>
              <span className="price-value">{poi.price}</span>
            </div>
          )}
          
          {poi.description && (
            <p className="poi-description">{poi.description}</p>
          )}
          
          <div className="poi-actions">
            {poi.phone && (
              <button className="poi-action-btn">
                <PhoneOutlined />
                <span>电话</span>
              </button>
            )}
            
            {poi.website && (
              <button className="poi-action-btn">
                <GlobalOutlined />
                <span>网站</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default POIMarker;
