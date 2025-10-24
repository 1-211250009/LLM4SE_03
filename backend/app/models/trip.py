"""
行程管理相关数据模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import uuid

class Trip(Base):
    """行程模型"""
    __tablename__ = "trips"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    destination = Column(String(100))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    duration_days = Column(Integer, default=1)
    budget = Column(Float)
    status = Column(String(20), default="draft")  # draft, planned, active, completed, cancelled
    is_public = Column(Boolean, default=False)
    tags = Column(JSON)  # 标签列表
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    user = relationship("User", back_populates="trips")
    itineraries = relationship("Itinerary", back_populates="trip", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="trip", cascade="all, delete-orphan")

class Itinerary(Base):
    """行程安排模型"""
    __tablename__ = "itineraries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id = Column(String(36), ForeignKey("trips.id"), nullable=False, index=True)
    day_number = Column(Integer, nullable=False)  # 第几天
    date = Column(DateTime)
    title = Column(String(200))
    description = Column(Text)
    start_time = Column(String(10))  # HH:MM格式
    end_time = Column(String(10))    # HH:MM格式
    location = Column(String(200))
    coordinates = Column(JSON)  # {"lat": 39.9042, "lng": 116.4074}
    category = Column(String(50))  # attraction, restaurant, hotel, transport, other
    priority = Column(Integer, default=1)  # 优先级 1-5
    estimated_duration = Column(Integer)  # 预计时长（分钟）
    estimated_cost = Column(Float)  # 预计费用
    notes = Column(Text)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    trip = relationship("Trip", back_populates="itineraries")
    items = relationship("ItineraryItem", back_populates="itinerary", cascade="all, delete-orphan")

class ItineraryItem(Base):
    """行程项目模型"""
    __tablename__ = "itinerary_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    itinerary_id = Column(String(36), ForeignKey("itineraries.id"), nullable=False, index=True)
    poi_id = Column(String(100))  # POI ID
    name = Column(String(200), nullable=False)
    description = Column(Text)
    address = Column(String(500))
    coordinates = Column(JSON)  # {"lat": 39.9042, "lng": 116.4074}
    category = Column(String(50))  # attraction, restaurant, hotel, transport, other
    rating = Column(Float)
    price_level = Column(String(20))  # $, $$, $$$, $$$$
    phone = Column(String(50))
    website = Column(String(500))
    opening_hours = Column(Text)
    images = Column(JSON)  # 图片URL列表
    order_index = Column(Integer, default=0)  # 排序索引
    is_visited = Column(Boolean, default=False)
    visit_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    itinerary = relationship("Itinerary", back_populates="items")

class Expense(Base):
    """费用记录模型"""
    __tablename__ = "expenses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id = Column(String(36), ForeignKey("trips.id"), nullable=False, index=True)
    itinerary_id = Column(String(36), ForeignKey("itineraries.id"), nullable=True, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="CNY")
    category = Column(String(50), nullable=False)  # transport, accommodation, food, attraction, shopping, other
    description = Column(String(500))
    location = Column(String(200))
    coordinates = Column(JSON)  # {"lat": 39.9042, "lng": 116.4074}
    payment_method = Column(String(50))  # cash, card, mobile, other
    receipt_image = Column(String(500))  # 收据图片URL
    is_shared = Column(Boolean, default=False)  # 是否分摊
    shared_amount = Column(Float)  # 分摊金额
    notes = Column(Text)
    expense_date = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    trip = relationship("Trip", back_populates="expenses")

class Budget(Base):
    """预算模型"""
    __tablename__ = "budgets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id = Column(String(36), ForeignKey("trips.id"), nullable=False, index=True)
    total_budget = Column(Float, nullable=False)
    currency = Column(String(10), default="CNY")
    categories = Column(JSON)  # {"transport": 1000, "accommodation": 2000, "food": 800, ...}
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    trip = relationship("Trip", foreign_keys=[trip_id])

# 更新User模型以包含关系
from .user import User
User.trips = relationship("Trip", back_populates="user")
