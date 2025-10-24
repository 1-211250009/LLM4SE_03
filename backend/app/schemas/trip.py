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
    TRANSPORT = "transport"
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
    poi_id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    address: Optional[str] = None
    coordinates: Optional[Coordinates] = None
    category: POICategory = POICategory.OTHER
    rating: Optional[float] = Field(None, ge=0, le=5)
    price_level: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    opening_hours: Optional[str] = None
    images: Optional[List[str]] = None
    order_index: int = 0
    is_visited: bool = False
    visit_notes: Optional[str] = None

class ItineraryItemCreate(ItineraryItemBase):
    pass

class ItineraryItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    address: Optional[str] = None
    coordinates: Optional[Coordinates] = None
    category: Optional[POICategory] = None
    rating: Optional[float] = Field(None, ge=0, le=5)
    price_level: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    opening_hours: Optional[str] = None
    images: Optional[List[str]] = None
    order_index: Optional[int] = None
    is_visited: Optional[bool] = None
    visit_notes: Optional[str] = None

class ItineraryItem(ItineraryItemBase):
    id: str
    itinerary_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ItineraryBase(BaseModel):
    day_number: int = Field(..., ge=1, description="第几天")
    date: Optional[datetime] = None
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    start_time: Optional[str] = Field(None, pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    end_time: Optional[str] = Field(None, pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    location: Optional[str] = Field(None, max_length=200)
    coordinates: Optional[Coordinates] = None
    category: str = "other"
    priority: int = Field(1, ge=1, le=5)
    estimated_duration: Optional[int] = Field(None, ge=0, description="预计时长（分钟）")
    estimated_cost: Optional[float] = Field(None, ge=0, description="预计费用")
    notes: Optional[str] = None
    is_completed: bool = False

class ItineraryCreate(ItineraryBase):
    items: Optional[List[ItineraryItemCreate]] = []

class ItineraryUpdate(BaseModel):
    day_number: Optional[int] = Field(None, ge=1)
    date: Optional[datetime] = None
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    start_time: Optional[str] = Field(None, pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    end_time: Optional[str] = Field(None, pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    location: Optional[str] = Field(None, max_length=200)
    coordinates: Optional[Coordinates] = None
    category: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    estimated_duration: Optional[int] = Field(None, ge=0)
    estimated_cost: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None
    is_completed: Optional[bool] = None

class Itinerary(ItineraryBase):
    id: str
    trip_id: str
    items: List[ItineraryItem] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class TripBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    destination: Optional[str] = Field(None, max_length=100)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    duration_days: int = Field(1, ge=1, le=365)
    budget: Optional[float] = Field(None, ge=0)
    status: TripStatus = TripStatus.DRAFT
    is_public: bool = False
    tags: Optional[List[str]] = []

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v <= values['start_date']:
                raise ValueError('结束日期必须晚于开始日期')
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
    budget: Optional[float] = Field(None, ge=0)
    status: Optional[TripStatus] = None
    is_public: Optional[bool] = None
    tags: Optional[List[str]] = None

class Trip(TripBase):
    id: str
    user_id: str
    itineraries: List[Itinerary] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ExpenseBase(BaseModel):
    amount: float = Field(..., gt=0, description="金额")
    currency: str = Field("CNY", max_length=10)
    category: ExpenseCategory
    description: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=200)
    coordinates: Optional[Coordinates] = None
    payment_method: Optional[str] = Field(None, max_length=50)
    receipt_image: Optional[str] = None
    is_shared: bool = False
    shared_amount: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None
    expense_date: Optional[datetime] = None

class ExpenseCreate(ExpenseBase):
    trip_id: str
    itinerary_id: Optional[str] = None

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
    shared_amount: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None
    expense_date: Optional[datetime] = None

class Expense(ExpenseBase):
    id: str
    trip_id: str
    itinerary_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class BudgetBase(BaseModel):
    total_budget: float = Field(..., gt=0, description="总预算")
    currency: str = Field("CNY", max_length=10)
    categories: Optional[Dict[str, float]] = Field(default_factory=dict, description="分类预算")

class BudgetCreate(BudgetBase):
    trip_id: str

class BudgetUpdate(BaseModel):
    total_budget: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=10)
    categories: Optional[Dict[str, float]] = None

class Budget(BudgetBase):
    id: str
    trip_id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

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
