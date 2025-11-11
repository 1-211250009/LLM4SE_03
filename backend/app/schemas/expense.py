"""
费用相关Schema
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime, date


class ExpenseBase(BaseModel):
    """费用基础模型"""
    trip_id: str = Field(..., description="行程ID")
    category: str = Field(..., description="费用分类")
    amount: float = Field(..., gt=0, description="金额")
    description: str = Field(..., description="描述")
    expense_date: str = Field(..., description="日期")
    location: Optional[str] = Field(None, description="地点")
    currency: str = Field("CNY", description="货币")
    
    @field_validator('expense_date')
    @classmethod
    def validate_expense_date(cls, v):
        if isinstance(v, str):
            try:
                return datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError('日期格式必须为 YYYY-MM-DD')
        return v


class ExpenseCreate(ExpenseBase):
    """创建费用模型"""
    pass


class ExpenseUpdate(BaseModel):
    """更新费用模型"""
    category: Optional[str] = Field(None, description="费用分类")
    amount: Optional[float] = Field(None, gt=0, description="金额")
    description: Optional[str] = Field(None, description="描述")
    expense_date: Optional[str] = Field(None, description="日期")
    location: Optional[str] = Field(None, description="地点")
    currency: Optional[str] = Field(None, description="货币")
    
    @field_validator('expense_date')
    @classmethod
    def validate_expense_date(cls, v):
        if v is not None and isinstance(v, str):
            try:
                return datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError('日期格式必须为 YYYY-MM-DD')
        return v


class ExpenseResponse(ExpenseBase):
    """费用响应模型"""
    id: str
    expense_date: datetime  # 覆盖父类的 str 类型，使用 datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Budget模型已删除 - 预算信息现在直接在Trip模型中管理


class ExpenseSummary(BaseModel):
    """费用统计摘要"""
    total_amount: float = Field(..., description="总金额")
    total_count: int = Field(..., description="总笔数")
    average_amount: float = Field(..., description="平均金额")
    category_breakdown: Dict[str, Dict[str, Any]] = Field(..., description="分类明细")
    daily_breakdown: Dict[str, float] = Field(..., description="每日明细")


class CategoryStats(BaseModel):
    """分类统计"""
    category: str = Field(..., description="分类名称")
    amount: float = Field(..., description="金额")
    count: int = Field(..., description="笔数")
    percentage: float = Field(..., description="占比")
