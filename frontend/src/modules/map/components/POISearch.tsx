/**
 * POI搜索组件
 * 提供POI搜索功能
 */

import React, { useState, useEffect } from 'react';
import { Input, Button, Select, Card, List, Spin, Alert, Empty, Tag } from 'antd';
import { SearchOutlined, ClearOutlined } from '@ant-design/icons';
import { usePOISearch } from '../hooks/usePOISearch';
import { POISearchParams, POIInfo, POICategory } from '../types/map.types';
import POIMarker from './POIMarker';
import './POISearch.css';

const { Search } = Input;
const { Option } = Select;

interface POISearchProps {
  onPOISelect?: (poi: POIInfo) => void;
  onSearchComplete?: (results: POIInfo[]) => void;
  className?: string;
  style?: React.CSSProperties;
}

const POISearch: React.FC<POISearchProps> = ({
  onPOISelect,
  onSearchComplete,
  className = '',
  style = {}
}) => {
  const [searchParams, setSearchParams] = useState<POISearchParams>({
    keyword: '',
    city: '北京',
    category: undefined,
    limit: 10
  });

  const {
    searchState,
    searchPOI,
    searchByCategory,
    clearResults
  } = usePOISearch();

  // 处理搜索结果变化
  useEffect(() => {
    if (searchState.results.length > 0 && onSearchComplete) {
      onSearchComplete(searchState.results);
    }
  }, [searchState.results, onSearchComplete]);

  // 执行搜索
  const handleSearch = async (value?: string) => {
    const keyword = value || searchParams.keyword;
    if (!keyword.trim()) return;

    try {
      await searchPOI({
        ...searchParams,
        keyword: keyword.trim()
      });
    } catch (error) {
      console.error('POI search failed:', error);
    }
  };

  // 按分类搜索
  const handleCategorySearch = async (category: POICategory) => {
    try {
      await searchByCategory(category, searchParams.city, searchParams.limit);
    } catch (error) {
      console.error('Category search failed:', error);
    }
  };

  // 清除搜索
  const handleClear = () => {
    setSearchParams(prev => ({ ...prev, keyword: '' }));
    clearResults();
  };

  // 处理POI选择
  const handlePOISelect = (poi: POIInfo) => {
    if (onPOISelect) {
      onPOISelect(poi);
    }
  };

  // 分类选项
  const categoryOptions = [
    { value: 'attraction', label: '景点', icon: '🏛️' },
    { value: 'restaurant', label: '餐厅', icon: '🍽️' },
    { value: 'hotel', label: '酒店', icon: '🏨' },
    { value: 'shopping', label: '购物', icon: '🛍️' },
    { value: 'transport', label: '交通', icon: '🚇' },
    { value: 'entertainment', label: '娱乐', icon: '🎭' }
  ];

  return (
    <div className={`poi-search ${className}`} style={style}>
      {/* 搜索表单 */}
      <Card className="search-form" size="small">
        <div className="search-inputs">
          <Search
            placeholder="搜索地点、餐厅、酒店..."
            value={searchParams.keyword}
            onChange={(e) => setSearchParams(prev => ({ ...prev, keyword: e.target.value }))}
            onSearch={handleSearch}
            enterButton={<SearchOutlined />}
            loading={searchState.isLoading}
            allowClear
          />
          
          <div className="search-filters">
            <Select
              placeholder="选择城市"
              value={searchParams.city}
              onChange={(city) => setSearchParams(prev => ({ ...prev, city }))}
              style={{ width: 120 }}
            >
              <Option value="北京">北京</Option>
              <Option value="上海">上海</Option>
              <Option value="广州">广州</Option>
              <Option value="深圳">深圳</Option>
              <Option value="杭州">杭州</Option>
              <Option value="成都">成都</Option>
            </Select>
            
            <Select
              placeholder="选择分类"
              value={searchParams.category}
              onChange={(category) => setSearchParams(prev => ({ ...prev, category }))}
              allowClear
              style={{ width: 120 }}
            >
              {categoryOptions.map(option => (
                <Option key={option.value} value={option.value}>
                  {option.icon} {option.label}
                </Option>
              ))}
            </Select>
            
            <Button
              icon={<ClearOutlined />}
              onClick={handleClear}
              disabled={!searchParams.keyword && !searchParams.category}
            >
              清除
            </Button>
          </div>
        </div>
      </Card>

      {/* 分类快速搜索 */}
      <Card className="category-search" size="small">
        <div className="category-tags">
          <span className="category-label">快速搜索:</span>
          {categoryOptions.map(option => (
            <Tag
              key={option.value}
              className="category-tag"
              onClick={() => handleCategorySearch(option.value as POICategory)}
            >
              {option.icon} {option.label}
            </Tag>
          ))}
        </div>
      </Card>

      {/* 搜索结果 */}
      <Card className="search-results" size="small">
        {searchState.isLoading && (
          <div className="search-loading">
            <Spin size="large" />
            <p>正在搜索...</p>
          </div>
        )}

        {searchState.error && (
          <Alert
            message="搜索失败"
            description={searchState.error}
            type="error"
            showIcon
            style={{ margin: '16px 0' }}
          />
        )}

        {!searchState.isLoading && !searchState.error && searchState.results.length === 0 && (
          <Empty
            description="暂无搜索结果"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        )}

        {!searchState.isLoading && !searchState.error && searchState.results.length > 0 && (
          <div className="results-header">
            <span className="results-count">
              找到 {searchState.total} 个结果
            </span>
            {searchState.hasMore && (
              <span className="results-more">还有更多结果...</span>
            )}
          </div>
        )}

        {searchState.results.length > 0 && (
          <List
            dataSource={searchState.results}
            renderItem={(poi) => (
              <List.Item key={poi.id} className="poi-list-item">
                <POIMarker
                  poi={poi}
                  onClick={handlePOISelect}
                  className="poi-list-marker"
                />
              </List.Item>
            )}
          />
        )}
      </Card>
    </div>
  );
};

export default POISearch;
