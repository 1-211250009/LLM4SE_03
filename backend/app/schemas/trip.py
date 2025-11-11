"""
行程管理相关Pydantic schemas
"""

from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class TripStatus(str, Enum):
    DRAFT = "draft"
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ExpenseCategory(str, Enum):
    TRANSPORT = "transportation"
    ACCOMMODATION = "accommodation"
    FOOD = "food"
    ATTRACTION = "attraction"
    SHOPPING = "shopping"
    OTHER = "other"

class POICategory(str, Enum):
    ATTRACTION = "attraction"
    RESTAURANT = "restaurant"
    HOTEL = "hotel"
    TRANSPORT = "transport"
    SHOPPING = "shopping"
    OTHER = "other"

# 基础模型
class Coordinates(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="纬度")
    lng: float = Field(..., ge=-180, le=180, description="经度")

class ItineraryItemBase(BaseModel):
    # 基本信息
    poi_id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    address: Optional[str] = None
    coordinates: Optional[Coordinates] = None
    category: POICategory = POICategory.OTHER
    
    # 时间安排
    start_time: Optional[str] = Field(None, pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    end_time: Optional[str] = Field(None, pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    estimated_duration: Optional[int] = Field(None, ge=0, description="预计停留时长（分钟）")
    
    # 附加信息
    rating: Optional[float] = Field(None, ge=0, le=5)
    price_level: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    opening_hours: Optional[str] = None
    images: Optional[List[str]] = None
    
    # 节点管理
    order_index: int = 0
    is_completed: bool = False
    notes: Optional[str] = None
    
    # 费用信息
    estimated_cost: Optional[float] = Field(None, ge=0, description="预计费用")

class ItineraryItemCreate(ItineraryItemBase):
    pass

class ItineraryItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    address: Optional[str] = None
    coordinates: Optional[Coordinates] = None
    category: Optional[POICategory] = None
    start_time: Optional[str] = Field(None, pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    end_time: Optional[str] = Field(None, pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    estimated_duration: Optional[int] = Field(None, ge=0)
    rating: Optional[float] = Field(None, ge=0, le=5)
    price_level: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    opening_hours: Optional[str] = None
    images: Optional[List[str]] = None
    order_index: Optional[int] = None
    is_completed: Optional[bool] = None
    notes: Optional[str] = None
    estimated_cost: Optional[float] = Field(None, ge=0)

class ItineraryItem(ItineraryItemBase):
    id: str
    itinerary_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ItineraryBase(BaseModel):
    """某一天的行程"""
    day_number: int = Field(..., ge=1, description="第几天")
    date: Optional[datetime] = None
    title: Optional[str] = Field(None, max_length=200, description="当天标题")
    description: Optional[str] = Field(None, description="当天描述")

class ItineraryCreate(ItineraryBase):
    items: Optional[List[ItineraryItemCreate]] = []

class ItineraryUpdate(BaseModel):
    day_number: Optional[int] = Field(None, ge=1)
    date: Optional[datetime] = None
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None

class Itinerary(ItineraryBase):
    id: str
    trip_id: str
    items: List[ItineraryItem] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class TripBase(BaseModel):
    """整个旅行计划"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    destination: Optional[str] = Field(None, max_length=100)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    duration_days: int = Field(1, ge=1, le=365)
    budget_total: Optional[float] = Field(None, ge=0, description="总预算")
    currency: str = Field("CNY", max_length=10, description="货币单位")
    status: TripStatus = TripStatus.DRAFT
    is_public: bool = False
    tags: Optional[List[str]] = []
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict, description="用户偏好")
    traveler_count: int = Field(1, ge=1, le=100, description="同行人数")

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            # 允许同一天（end_date >= start_date），例如：2025-11-11到2025-11-11是1天
            if v < values['start_date']:
                raise ValueError('结束日期不能早于开始日期')
        return v

class TripCreate(TripBase):
    itineraries: Optional[List[ItineraryCreate]] = []

class TripUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    destination: Optional[str] = Field(None, max_length=100)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    duration_days: Optional[int] = Field(None, ge=1, le=365)
    budget_total: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=10)
    status: Optional[TripStatus] = None
    is_public: Optional[bool] = None
    tags: Optional[List[str]] = None
    preferences: Optional[Dict[str, Any]] = None
    traveler_count: Optional[int] = Field(None, ge=1, le=100)

class Trip(TripBase):
    id: str
    user_id: str
    itineraries: List[Itinerary] = []
    expenses: List['Expense'] = []  # 添加expenses字段
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ExpenseBase(BaseModel):
    """费用记录 - 可以挂钩在行程、某天行程或具体节点上"""
    amount: float = Field(..., gt=0, description="金额")
    currency: str = Field("CNY", max_length=10)
    category: ExpenseCategory
    description: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=200)
    coordinates: Optional[Coordinates] = None
    payment_method: Optional[str] = Field(None, max_length=50)
    receipt_image: Optional[str] = None
    is_shared: bool = False
    shared_with: Optional[List[str]] = Field(default_factory=list, description="分摊人员列表")
    my_share: Optional[float] = Field(None, ge=0, description="我的份额")
    notes: Optional[str] = None
    expense_date: Optional[datetime] = None
    tags: Optional[List[str]] = Field(default_factory=list)

class ExpenseCreate(ExpenseBase):
    trip_id: Optional[str] = None  # 可选，通常从路径参数中获取
    itinerary_id: Optional[str] = None
    itinerary_item_id: Optional[str] = None

class ExpenseUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=10)
    category: Optional[ExpenseCategory] = None
    description: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=200)
    coordinates: Optional[Coordinates] = None
    payment_method: Optional[str] = Field(None, max_length=50)
    receipt_image: Optional[str] = None
    is_shared: Optional[bool] = None
    shared_with: Optional[List[str]] = None
    my_share: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None
    expense_date: Optional[datetime] = None
    tags: Optional[List[str]] = None
    itinerary_item_id: Optional[str] = None

class Expense(ExpenseBase):
    id: str
    trip_id: str
    itinerary_id: Optional[str] = None
    itinerary_item_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# 预算信息已整合到Trip模型中，不再需要独立的Budget模型

# 统计模型
class TripStats(BaseModel):
    total_trips: int
    active_trips: int
    completed_trips: int
    total_expenses: float
    average_trip_duration: float
    most_visited_destinations: List[Dict[str, Any]]

class ExpenseStats(BaseModel):
    total_amount: float
    category_breakdown: Dict[str, float]
    daily_average: float
    monthly_trend: List[Dict[str, Any]]
    budget_vs_actual: Dict[str, Any]

# 响应模型
class TripListResponse(BaseModel):
    trips: List[Trip]
    total: int
    page: int
    size: int
    has_next: bool

class ExpenseListResponse(BaseModel):
    expenses: List[Expense]
    total: int
    page: int
    size: int
    has_next: bool
    total_amount: float
