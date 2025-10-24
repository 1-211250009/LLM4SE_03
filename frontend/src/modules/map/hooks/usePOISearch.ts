/**
 * POI搜索Hook
 * 管理POI搜索功能
 */

import { useState, useCallback } from 'react';
import { mapService } from '../services/baidu-map.service';
import { POISearchParams, POISearchResult, POIInfo } from '../types/map.types';

export function usePOISearch() {
  const [searchState, setSearchState] = useState<{
    isLoading: boolean;
    results: POIInfo[];
    error?: string;
    hasMore: boolean;
    total: number;
  }>({
    isLoading: false,
    results: [],
    error: undefined,
    hasMore: false,
    total: 0
  });

  /**
   * 搜索POI
   */
  const searchPOI = useCallback(async (params: POISearchParams) => {
    setSearchState(prev => ({
      ...prev,
      isLoading: true,
      error: undefined
    }));

    try {
      const result = await mapService.searchPOI(params);
      
      setSearchState(prev => ({
        ...prev,
        isLoading: false,
        results: result.pois,
        hasMore: result.hasMore,
        total: result.total,
        error: undefined
      }));

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'POI search failed';
      
      setSearchState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
        results: [],
        hasMore: false,
        total: 0
      }));

      throw error;
    }
  }, []);

  /**
   * 按分类搜索POI
   */
  const searchByCategory = useCallback(async (
    category: string,
    city: string,
    limit: number = 10
  ) => {
    return searchPOI({
      keyword: '',
      city,
      category: category as any,
      limit
    });
  }, [searchPOI]);

  /**
   * 搜索附近的POI
   */
  const searchNearby = useCallback(async (
    center: { lat: number; lng: number },
    keyword: string,
    radius: number = 1000,
    limit: number = 10
  ) => {
    return searchPOI({
      keyword,
      city: '',
      location: center,
      radius,
      limit
    });
  }, [searchPOI]);

  /**
   * 清除搜索结果
   */
  const clearResults = useCallback(() => {
    setSearchState({
      isLoading: false,
      results: [],
      error: undefined,
      hasMore: false,
      total: 0
    });
  }, []);

  /**
   * 重新搜索
   */
  const retry = useCallback(() => {
    if (searchState.error) {
      setSearchState(prev => ({
        ...prev,
        error: undefined,
        isLoading: true
      }));
    }
  }, [searchState.error]);

  return {
    searchState,
    searchPOI,
    searchByCategory,
    searchNearby,
    clearResults,
    retry
  };
}
