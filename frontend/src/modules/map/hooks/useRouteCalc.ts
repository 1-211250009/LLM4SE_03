/**
 * 路线计算Hook
 * 管理路线规划功能
 */

import { useState, useCallback } from 'react';
import { mapService } from '../services/baidu-map.service';
import { RouteParams, RouteInfo } from '../types/map.types';

export function useRouteCalc() {
  const [routeState, setRouteState] = useState<{
    isLoading: boolean;
    routes: RouteInfo[];
    error?: string;
  }>({
    isLoading: false,
    routes: [],
    error: undefined
  });

  /**
   * 计算路线
   */
  const calculateRoute = useCallback(async (params: RouteParams) => {
    setRouteState(prev => ({
      ...prev,
      isLoading: true,
      error: undefined
    }));

    try {
      const route = await mapService.calculateRoute(params);
      
      setRouteState(prev => ({
        ...prev,
        isLoading: false,
        routes: [...prev.routes, route],
        error: undefined
      }));

      return route;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Route calculation failed';
      
      setRouteState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage
      }));

      throw error;
    }
  }, []);

  /**
   * 计算驾车路线
   */
  const calculateDrivingRoute = useCallback(async (
    origin: string | { lat: number; lng: number },
    destination: string | { lat: number; lng: number }
  ) => {
    return calculateRoute({
      origin,
      destination,
      mode: 'driving'
    });
  }, [calculateRoute]);

  /**
   * 计算公交路线
   */
  const calculateTransitRoute = useCallback(async (
    origin: string | { lat: number; lng: number },
    destination: string | { lat: number; lng: number }
  ) => {
    return calculateRoute({
      origin,
      destination,
      mode: 'transit'
    });
  }, [calculateRoute]);

  /**
   * 计算步行路线
   */
  const calculateWalkingRoute = useCallback(async (
    origin: string | { lat: number; lng: number },
    destination: string | { lat: number; lng: number }
  ) => {
    return calculateRoute({
      origin,
      destination,
      mode: 'walking'
    });
  }, [calculateRoute]);

  /**
   * 计算骑行路线
   */
  const calculateBicyclingRoute = useCallback(async (
    origin: string | { lat: number; lng: number },
    destination: string | { lat: number; lng: number }
  ) => {
    return calculateRoute({
      origin,
      destination,
      mode: 'bicycling'
    });
  }, [calculateRoute]);

  /**
   * 清除所有路线
   */
  const clearRoutes = useCallback(() => {
    setRouteState({
      isLoading: false,
      routes: [],
      error: undefined
    });
  }, []);

  /**
   * 移除指定路线
   */
  const removeRoute = useCallback((index: number) => {
    setRouteState(prev => ({
      ...prev,
      routes: prev.routes.filter((_, i) => i !== index)
    }));
  }, []);

  /**
   * 重新计算路线
   */
  const retry = useCallback(() => {
    if (routeState.error) {
      setRouteState(prev => ({
        ...prev,
        error: undefined,
        isLoading: true
      }));
    }
  }, [routeState.error]);

  return {
    routeState,
    calculateRoute,
    calculateDrivingRoute,
    calculateTransitRoute,
    calculateWalkingRoute,
    calculateBicyclingRoute,
    clearRoutes,
    removeRoute,
    retry
  };
}
