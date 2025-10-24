# 地图模块

基于百度地图API的地图功能模块，提供地图展示、POI搜索、路线规划等功能。

## 功能特性

- 🗺️ 地图展示和交互
- 🔍 POI搜索（景点、餐厅、酒店等）
- 🛣️ 路线规划（驾车、公交、步行、骑行）
- 📍 标记管理
- 🎨 自定义样式

## 快速开始

### 1. 配置API Key

在项目根目录创建 `.env.local` 文件：

```bash
VITE_BAIDU_MAPS_API_KEY=your_baidu_maps_api_key_here
```

### 2. 基础使用

```tsx
import { MapContainer, POISearch } from '@/modules/map';
import { MapConfig, MapMarker } from '@/modules/map/types/map.types';

const mapConfig: MapConfig = {
  center: { lat: 39.9042, lng: 116.4074 },
  zoom: 12
};

const MyComponent = () => {
  const [markers, setMarkers] = useState<MapMarker[]>([]);

  return (
    <div style={{ height: '500px' }}>
      <MapContainer
        containerId="my-map"
        config={mapConfig}
        markers={markers}
        onMapClick={(point) => console.log('点击了地图:', point)}
      />
    </div>
  );
};
```

### 3. POI搜索

```tsx
import { POISearch } from '@/modules/map';

const MyComponent = () => {
  const handlePOISelect = (poi) => {
    console.log('选择了POI:', poi);
  };

  return (
    <POISearch
      onPOISelect={handlePOISelect}
      onSearchComplete={(results) => console.log('搜索结果:', results)}
    />
  );
};
```

## API 参考

### MapContainer

地图容器组件

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| containerId | string | - | 地图容器的DOM ID |
| config | MapConfig | - | 地图配置 |
| markers | MapMarker[] | [] | 地图标记 |
| onMapClick | (point: Point) => void | - | 地图点击回调 |
| onMarkerClick | (marker: MapMarker) => void | - | 标记点击回调 |

### POISearch

POI搜索组件

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| onPOISelect | (poi: POIInfo) => void | - | POI选择回调 |
| onSearchComplete | (results: POIInfo[]) => void | - | 搜索完成回调 |

### Hooks

#### useMap

地图管理Hook

```tsx
const {
  mapState,
  addMarker,
  removeMarker,
  clearMarkers,
  setCenter,
  setZoom
} = useMap(containerId, config);
```

#### usePOISearch

POI搜索Hook

```tsx
const {
  searchState,
  searchPOI,
  searchByCategory,
  searchNearby,
  clearResults
} = usePOISearch();
```

#### useRouteCalc

路线计算Hook

```tsx
const {
  routeState,
  calculateRoute,
  calculateDrivingRoute,
  calculateTransitRoute,
  calculateWalkingRoute,
  calculateBicyclingRoute,
  clearRoutes
} = useRouteCalc();
```

## 类型定义

### MapConfig

地图配置

```tsx
interface MapConfig {
  center: Point;
  zoom: number;
  style?: string;
  enableScrollWheelZoom?: boolean;
  enableDragging?: boolean;
  enableDoubleClickZoom?: boolean;
  enableKeyboard?: boolean;
  enableInertialDragging?: boolean;
  enableContinuousZoom?: boolean;
  enablePinchToZoom?: boolean;
}
```

### POIInfo

POI信息

```tsx
interface POIInfo {
  id: string;
  name: string;
  address: string;
  location: Point;
  category: POICategory;
  rating?: number;
  price?: string;
  description?: string;
  photos?: string[];
  phone?: string;
  website?: string;
  openingHours?: string;
  distance?: number;
}
```

### MapMarker

地图标记

```tsx
interface MapMarker {
  id: string;
  position: Point;
  title: string;
  content?: string;
  icon?: string;
  poi?: POIInfo;
  draggable?: boolean;
}
```

## 注意事项

1. 需要申请百度地图API Key
2. 确保网络连接正常
3. 地图容器需要有明确的高度
4. POI搜索需要网络连接

## 故障排除

### 地图不显示

1. 检查API Key是否正确配置
2. 检查网络连接
3. 检查浏览器控制台错误信息

### POI搜索失败

1. 检查网络连接
2. 检查搜索关键词是否有效
3. 检查城市名称是否正确

### 标记不显示

1. 检查标记数据格式
2. 检查地图是否已加载完成
3. 检查标记位置是否在地图范围内
