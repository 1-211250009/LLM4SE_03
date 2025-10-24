/**
 * 百度地图服务
 * 封装百度地图API调用
 */

import { 
  POIInfo, 
  POISearchParams, 
  POISearchResult, 
  RouteParams, 
  RouteInfo, 
  GeocodeResult, 
  ReverseGeocodeResult,
  Point,
  MapServiceConfig
} from '../types/map.types';

declare global {
  interface Window {
    BMap: any;
    BMapGL: any;
  }
}

class BaiduMapService {
  private config: MapServiceConfig;
  private isLoaded: boolean = false;

  constructor(config: MapServiceConfig) {
    this.config = config;
  }

  /**
   * 初始化百度地图API
   */
  async initialize(): Promise<void> {
    if (this.isLoaded) return;

    return new Promise((resolve, reject) => {
      // 检查是否已经加载
      if (window.BMap) {
        this.isLoaded = true;
        resolve();
        return;
      }

      // 创建script标签加载百度地图API
      const script = document.createElement('script');
      script.src = `https://api.map.baidu.com/api?v=3.0&ak=${this.config.apiKey}&callback=initBaiduMap`;
      script.async = true;
      script.defer = true;

      // 设置全局回调函数
      (window as any).initBaiduMap = () => {
        this.isLoaded = true;
        resolve();
      };

      script.onerror = () => {
        reject(new Error('Failed to load Baidu Map API'));
      };

      document.head.appendChild(script);
    });
  }

  /**
   * 创建地图实例
   */
  createMap(container: HTMLElement, center: Point, zoom: number = 15): any {
    if (!this.isLoaded) {
      throw new Error('Baidu Map API not loaded');
    }

    const map = new window.BMap.Map(container);
    const point = new window.BMap.Point(center.lng, center.lat);
    
    map.centerAndZoom(point, zoom);
    
    // 启用地图控件
    map.addControl(new window.BMap.NavigationControl());
    map.addControl(new window.BMap.ScaleControl());
    map.addControl(new window.BMap.OverviewMapControl());
    map.addControl(new window.BMap.MapTypeControl());
    
    // 启用地图功能
    map.enableScrollWheelZoom(true);
    map.enableDragging(true);
    map.enableDoubleClickZoom(true);
    map.enableKeyboard(true);
    map.enableInertialDragging(true);
    map.enableContinuousZoom(true);
    map.enablePinchToZoom(true);

    return map;
  }

  /**
   * POI搜索
   */
  async searchPOI(params: POISearchParams): Promise<POISearchResult> {
    if (!this.isLoaded) {
      throw new Error('Baidu Map API not loaded');
    }

    return new Promise((resolve, reject) => {
      const local = new window.BMap.LocalSearch(null, {
        onSearchComplete: (results: any) => {
          if (local.getStatus() === window.BMap.StatusCode.OK) {
            const pois: POIInfo[] = results.getPoi().map((poi: any) => ({
              id: poi.uid || `poi_${Date.now()}_${Math.random()}`,
              name: poi.title,
              address: poi.address,
              location: {
                lat: poi.point.lat,
                lng: poi.point.lng
              },
              category: this.mapCategory(poi.type),
              rating: poi.rating || 0,
              price: poi.price || '',
              description: poi.content || '',
              phone: poi.phone || '',
              website: poi.url || '',
              openingHours: poi.openTime || ''
            }));

            resolve({
              pois: pois.slice(0, params.limit || 10),
              total: pois.length,
              page: 1,
              hasMore: pois.length > (params.limit || 10)
            });
          } else {
            reject(new Error('POI search failed'));
          }
        }
      });

      // 构建搜索关键词
      let keyword = params.keyword;
      if (params.category) {
        keyword += ` ${this.getCategoryKeyword(params.category)}`;
      }
      if (params.city) {
        keyword += ` ${params.city}`;
      }

      local.search(keyword);
    });
  }

  /**
   * 路线规划
   */
  async calculateRoute(params: RouteParams): Promise<RouteInfo> {
    if (!this.isLoaded) {
      throw new Error('Baidu Map API not loaded');
    }

    return new Promise((resolve, reject) => {
      const driving = new window.BMap.DrivingRoute(null, {
        onSearchComplete: (results: any) => {
          if (driving.getStatus() === window.BMap.StatusCode.OK) {
            const plan = results.getPlan(0);
            const route = plan.getRoute(0);
            
            const steps: any[] = [];
            for (let i = 0; i < route.getNumSteps(); i++) {
              const step = route.getStep(i);
              steps.push({
                instruction: step.getDescription(),
                distance: step.getDistance(),
                duration: step.getDuration(),
                start_location: {
                  lat: step.getPosition().lat,
                  lng: step.getPosition().lng
                },
                end_location: {
                  lat: step.getPosition().lat,
                  lng: step.getPosition().lng
                },
                travel_mode: params.mode
              });
            }

            resolve({
              distance: plan.getDistance(),
              duration: plan.getDuration(),
              steps,
              bounds: {
                northeast: {
                  lat: route.getBounds().getNorthEast().lat,
                  lng: route.getBounds().getNorthEast().lng
                },
                southwest: {
                  lat: route.getBounds().getSouthWest().lat,
                  lng: route.getBounds().getSouthWest().lng
                }
              },
              overview_polyline: route.getPolyline().toString()
            });
          } else {
            reject(new Error('Route calculation failed'));
          }
        }
      });

      // 转换起点和终点
      const start = typeof params.origin === 'string' 
        ? params.origin 
        : new window.BMap.Point(params.origin.lng, params.origin.lat);
      const end = typeof params.destination === 'string'
        ? params.destination
        : new window.BMap.Point(params.destination.lng, params.destination.lat);

      driving.search(start, end);
    });
  }

  /**
   * 地理编码（地址转坐标）
   */
  async geocode(address: string): Promise<GeocodeResult> {
    if (!this.isLoaded) {
      throw new Error('Baidu Map API not loaded');
    }

    return new Promise((resolve, reject) => {
      const geocoder = new window.BMap.Geocoder();
      
      geocoder.getPoint(address, (point: any) => {
        if (point) {
          resolve({
            address,
            location: {
              lat: point.lat,
              lng: point.lng
            },
            formatted_address: address,
            address_components: {
              country: '',
              province: '',
              city: '',
              district: '',
              street: '',
              street_number: ''
            }
          });
        } else {
          reject(new Error('Geocoding failed'));
        }
      });
    });
  }

  /**
   * 逆地理编码（坐标转地址）
   */
  async reverseGeocode(point: Point): Promise<ReverseGeocodeResult> {
    if (!this.isLoaded) {
      throw new Error('Baidu Map API not loaded');
    }

    return new Promise((resolve, reject) => {
      const geocoder = new window.BMap.Geocoder();
      const bdPoint = new window.BMap.Point(point.lng, point.lat);
      
      geocoder.getLocation(bdPoint, (result: any) => {
        if (result) {
          resolve({
            address: result.address,
            location: point,
            formatted_address: result.address,
            business: result.business || '',
            address_components: {
              country: result.addressComponents?.country || '',
              province: result.addressComponents?.province || '',
              city: result.addressComponents?.city || '',
              district: result.addressComponents?.district || '',
              street: result.addressComponents?.street || '',
              street_number: result.addressComponents?.streetNumber || ''
            }
          });
        } else {
          reject(new Error('Reverse geocoding failed'));
        }
      });
    });
  }

  /**
   * 创建标记
   */
  createMarker(point: Point, title: string, content?: string): any {
    if (!this.isLoaded) {
      throw new Error('Baidu Map API not loaded');
    }

    const bdPoint = new window.BMap.Point(point.lng, point.lat);
    const marker = new window.BMap.Marker(bdPoint);
    
    if (title) {
      marker.setTitle(title);
    }
    
    if (content) {
      // 注意：这里需要传入map实例，但当前方法签名中没有map参数
      // 暂时注释掉，需要在调用时传入map实例
      // const infoWindow = new window.BMap.InfoWindow(content);
      // marker.addEventListener('click', () => {
      //   map.openInfoWindow(infoWindow, bdPoint);
      // });
    }

    return marker;
  }

  /**
   * 添加路线覆盖层
   */
  addRouteOverlay(map: any, route: RouteInfo): void {
    if (!this.isLoaded || !route.overview_polyline) {
      return;
    }

    const polyline = new window.BMap.Polyline(
      route.overview_polyline.split(';').map((point: string) => {
        const [lng, lat] = point.split(',').map(Number);
        return new window.BMap.Point(lng, lat);
      }),
      {
        strokeColor: '#3388ff',
        strokeWeight: 4,
        strokeOpacity: 0.8
      }
    );

    map.addOverlay(polyline);
  }

  /**
   * 地图分类映射
   */
  private mapCategory(type: string): string {
    const categoryMap: { [key: string]: string } = {
      '景点': 'attraction',
      '餐厅': 'restaurant',
      '酒店': 'hotel',
      '购物': 'shopping',
      '交通': 'transport',
      '娱乐': 'entertainment'
    };

    return categoryMap[type] || 'attraction';
  }

  /**
   * 获取分类关键词
   */
  private getCategoryKeyword(category: string): string {
    const keywordMap: { [key: string]: string } = {
      'attraction': '景点',
      'restaurant': '餐厅',
      'hotel': '酒店',
      'shopping': '购物',
      'transport': '交通',
      'entertainment': '娱乐'
    };

    return keywordMap[category] || '';
  }

  /**
   * 检查API是否已加载
   */
  isApiLoaded(): boolean {
    return this.isLoaded;
  }
}

// 创建默认实例
const mapService = new BaiduMapService({
  apiKey: import.meta.env.VITE_BAIDU_MAPS_API_KEY || 'your_baidu_maps_api_key_here',
  baseUrl: 'https://api.map.baidu.com',
  version: '3.0',
  timeout: 10000
});

export { BaiduMapService, mapService };
