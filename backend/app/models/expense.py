"""
费用模型
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class Expense(Base):
    """费用模型"""
    __tablename__ = "expenses"

    id = Column(String(36), primary_key=True, index=True)
    trip_id = Column(String(36), ForeignKey("trips.id"), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)  # 费用分类
    amount = Column(Float, nullable=False)  # 金额
    description = Column(Text, nullable=False)  # 描述
    date = Column(DateTime, nullable=False, index=True)  # 日期
    location = Column(String(255), nullable=True)  # 地点
    currency = Column(String(10), default="CNY")  # 货币
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    trip = relationship("Trip", back_populates="expenses")

    def to_dict(self):
        return {
            "id": self.id,
            "trip_id": self.trip_id,
            "category": self.category,
            "amount": self.amount,
            "description": self.description,
            "date": self.date.isoformat() if self.date else None,
            "location": self.location,
            "currency": self.currency,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
