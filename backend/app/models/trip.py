"""
行程管理相关数据模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import uuid

class Trip(Base):
    """行程模型 - 整个旅行计划"""
    __tablename__ = "trips"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    destination = Column(String(100))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    duration_days = Column(Integer, default=1)
    budget_total = Column(Float)  # 总预算
    currency = Column(String(10), default="CNY")  # 货币单位
    status = Column(String(20), default="draft")  # draft, planned, active, completed, cancelled
    is_public = Column(Boolean, default=False)
    tags = Column(JSON)  # 标签列表
    preferences = Column(JSON)  # 用户偏好（美食、动漫、亲子等）
    traveler_count = Column(Integer, default=1)  # 同行人数
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    user = relationship("User", back_populates="trips")
    itineraries = relationship("Itinerary", back_populates="trip", cascade="all, delete-orphan", order_by="Itinerary.day_number")
    expenses = relationship("Expense", back_populates="trip", cascade="all, delete-orphan")

class Itinerary(Base):
    """行程安排模型 - 某一天的行程"""
    __tablename__ = "itineraries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id = Column(String(36), ForeignKey("trips.id"), nullable=False, index=True)
    day_number = Column(Integer, nullable=False)  # 第几天
    date = Column(DateTime)  # 具体日期
    title = Column(String(200))  # 当天标题，例如：第一天 - 探索市中心
    description = Column(Text)  # 当天描述
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    trip = relationship("Trip", back_populates="itineraries")
    items = relationship("ItineraryItem", back_populates="itinerary", cascade="all, delete-orphan", order_by="ItineraryItem.order_index")
    expenses = relationship("Expense", back_populates="itinerary", cascade="all, delete-orphan")

class ItineraryItem(Base):
    """行程节点模型 - 行程中的具体活动点"""
    __tablename__ = "itinerary_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    itinerary_id = Column(String(36), ForeignKey("itineraries.id"), nullable=False, index=True)
    
    # 基本信息
    poi_id = Column(String(100))  # POI ID（来自百度地图）
    name = Column(String(200), nullable=False)  # 地点名称
    description = Column(Text)  # 描述
    address = Column(String(500))  # 地址
    coordinates = Column(JSON)  # 坐标 {"lat": 39.9042, "lng": 116.4074}
    category = Column(String(50))  # 类别：attraction, restaurant, hotel, transport, shopping, other
    
    # 时间安排
    start_time = Column(String(10))  # 开始时间 HH:MM格式
    end_time = Column(String(10))    # 结束时间 HH:MM格式
    estimated_duration = Column(Integer)  # 预计停留时长（分钟）
    
    # 附加信息
    rating = Column(Float)  # 评分
    price_level = Column(String(20))  # 价格等级：$, $$, $$$, $$$$
    phone = Column(String(50))  # 电话
    website = Column(String(500))  # 网站
    opening_hours = Column(Text)  # 营业时间
    images = Column(JSON)  # 图片URL列表
    
    # 节点管理
    order_index = Column(Integer, default=0)  # 排序索引
    is_completed = Column(Boolean, default=False)  # 是否已完成
    notes = Column(Text)  # 备注
    
    # 费用信息
    estimated_cost = Column(Float)  # 预计费用
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    itinerary = relationship("Itinerary", back_populates="items")
    expenses = relationship("Expense", back_populates="itinerary_item", cascade="all, delete-orphan")

class Expense(Base):
    """费用记录模型 - 可以挂钩在行程、某天行程或具体节点上"""
    __tablename__ = "expenses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 关联关系 - 费用可以属于整个行程、某天行程或具体节点
    trip_id = Column(String(36), ForeignKey("trips.id"), nullable=False, index=True)
    itinerary_id = Column(String(36), ForeignKey("itineraries.id"), nullable=True, index=True)  # 可选：某一天的行程
    itinerary_item_id = Column(String(36), ForeignKey("itinerary_items.id"), nullable=True, index=True)  # 可选：具体节点
    
    # 费用信息
    amount = Column(Float, nullable=False)  # 金额
    currency = Column(String(10), default="CNY")  # 货币
    category = Column(String(50), nullable=False)  # 类别：transportation, accommodation, food, attraction, shopping, other
    description = Column(String(500))  # 描述
    
    # 位置信息
    location = Column(String(200))  # 地点名称
    coordinates = Column(JSON)  # 坐标 {"lat": 39.9042, "lng": 116.4074}
    
    # 支付信息
    payment_method = Column(String(50))  # 支付方式：cash, card, mobile, other
    receipt_image = Column(String(500))  # 收据图片URL
    
    # 分摊信息
    is_shared = Column(Boolean, default=False)  # 是否分摊
    shared_with = Column(JSON)  # 分摊人员列表
    my_share = Column(Float)  # 我的份额
    
    # 其他信息
    notes = Column(Text)  # 备注
    expense_date = Column(DateTime)  # 费用日期
    tags = Column(JSON)  # 标签
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    trip = relationship("Trip", back_populates="expenses")
    itinerary = relationship("Itinerary", back_populates="expenses")
    itinerary_item = relationship("ItineraryItem", back_populates="expenses")

# 更新User模型以包含关系
from .user import User
User.trips = relationship("Trip", back_populates="user")
