"""
预算模型
"""

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class Budget(Base):
    """预算模型"""
    __tablename__ = "budgets"

    id = Column(String(36), primary_key=True, index=True)
    trip_id = Column(String(36), ForeignKey("trips.id"), nullable=False, index=True)
    total_budget = Column(Float, nullable=False)  # 总预算
    spent_amount = Column(Float, default=0)  # 已花费金额
    remaining_amount = Column(Float, default=0)  # 剩余金额
    categories = Column(JSON, nullable=True)  # 分类预算
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    trip = relationship("Trip", back_populates="budgets")

    def to_dict(self):
        return {
            "id": self.id,
            "trip_id": self.trip_id,
            "total_budget": self.total_budget,
            "spent_amount": self.spent_amount,
            "remaining_amount": self.remaining_amount,
            "categories": self.categories,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
