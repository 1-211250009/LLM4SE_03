"""
预算管理API端点（重构版本）

注意：预算信息现在直接在Trip模型中管理，不再有独立的Budget表
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.trip import Trip as TripModel, Expense as ExpenseModel
from app.schemas.trip import Trip, TripUpdate, Expense, ExpenseCreate, ExpenseUpdate, ExpenseListResponse, ExpenseStats

router = APIRouter()

# 响应模型
class BudgetSummaryResponse(BaseModel):
    """预算摘要响应"""
    trip_id: str
    trip_title: str
    total_budget: Optional[float] = None
    spent_amount: float
    remaining_budget: Optional[float] = None
    budget_usage_percent: Optional[float] = None
    category_breakdown: Dict[str, float]
    expense_count: int
    
class BudgetUpdateRequest(BaseModel):
    """预算更新请求"""
    total_budget: float = Field(..., gt=0, description="总预算")
    currency: Optional[str] = Field("CNY", description="货币单位")

# 预算管理
@router.get("/trips/{trip_id}/budget", response_model=BudgetSummaryResponse)
async def get_trip_budget(
    trip_id: str = Path(..., description="行程ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取行程预算摘要"""
    try:
        # 检查行程是否存在且属于当前用户
        trip = db.query(TripModel).filter(
            TripModel.id == trip_id,
            TripModel.user_id == current_user.id
        ).first()
        
        if not trip:
            raise HTTPException(status_code=404, detail="行程不存在")
        
        # 计算总花费
        expenses = db.query(ExpenseModel).filter(
            ExpenseModel.trip_id == trip_id
        ).all()
        
        spent_amount = sum(e.amount for e in expenses)
        
        # 按类别统计
        category_breakdown = {}
        for expense in expenses:
            category = expense.category
            if category not in category_breakdown:
                category_breakdown[category] = 0
            category_breakdown[category] += expense.amount
        
        # 计算剩余预算和使用率
        remaining_budget = None
        budget_usage_percent = None
        if trip.budget_total:
            remaining_budget = trip.budget_total - spent_amount
            budget_usage_percent = (spent_amount / trip.budget_total * 100) if trip.budget_total > 0 else 0
        
        return BudgetSummaryResponse(
            trip_id=trip_id,
            trip_title=trip.title,
            total_budget=trip.budget_total,
            spent_amount=spent_amount,
            remaining_budget=remaining_budget,
            budget_usage_percent=budget_usage_percent,
            category_breakdown=category_breakdown,
            expense_count=len(expenses)
        )
        
    except Exception as e:
        print(f"Get budget error: {e}")
        raise HTTPException(status_code=500, detail=f"获取预算失败: {str(e)}")

@router.put("/trips/{trip_id}/budget")
async def update_trip_budget(
    trip_id: str = Path(..., description="行程ID"),
    budget_data: BudgetUpdateRequest = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新行程预算"""
    try:
        # 检查行程是否存在且属于当前用户
        trip = db.query(TripModel).filter(
            TripModel.id == trip_id,
            TripModel.user_id == current_user.id
        ).first()
        
        if not trip:
            raise HTTPException(status_code=404, detail="行程不存在")
        
        # 更新预算
        trip.budget_total = budget_data.total_budget
        if budget_data.currency:
            trip.currency = budget_data.currency
        trip.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(trip)
        
        return {
            "message": "预算更新成功",
            "trip_id": trip_id,
            "total_budget": trip.budget_total,
            "currency": trip.currency
        }
        
    except Exception as e:
        db.rollback()
        print(f"Update budget error: {e}")
        raise HTTPException(status_code=500, detail=f"更新预算失败: {str(e)}")

# 费用管理
@router.post("/trips/{trip_id}/expenses", response_model=Expense)
async def create_expense(
    trip_id: str = Path(..., description="行程ID"),
    expense_data: ExpenseCreate = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建费用记录"""
    try:
        # 检查行程是否存在且属于当前用户
        trip = db.query(TripModel).filter(
            TripModel.id == trip_id,
            TripModel.user_id == current_user.id
        ).first()
        
        if not trip:
            raise HTTPException(status_code=404, detail="行程不存在")
        
        # 确保trip_id使用路径参数中的值，而不是请求体中的（如果请求体中有的话）
        # 创建费用记录
        expense = ExpenseModel(
            id=str(__import__('uuid').uuid4()),
            trip_id=trip_id,  # 使用路径参数中的trip_id
            amount=expense_data.amount,
            currency=expense_data.currency or "CNY",
            category=expense_data.category,
            description=expense_data.description or "",
            location=expense_data.location,
            coordinates=expense_data.coordinates.model_dump() if expense_data.coordinates else None,
            payment_method=expense_data.payment_method,
            receipt_image=expense_data.receipt_image,
            is_shared=expense_data.is_shared if expense_data.is_shared is not None else False,
            shared_with=expense_data.shared_with if expense_data.shared_with else [],
            my_share=expense_data.my_share,
            notes=expense_data.notes,
            tags=expense_data.tags if expense_data.tags else [],
            expense_date=expense_data.expense_date if expense_data.expense_date else datetime.utcnow(),
            itinerary_item_id=expense_data.itinerary_item_id if expense_data.itinerary_item_id else None
        )
        
        db.add(expense)
        db.commit()
        db.refresh(expense)
        return expense
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        error_msg = str(e)
        print(f"Create expense error: {error_msg}")
        print(f"Traceback: {traceback.format_exc()}")
        # 如果是Pydantic验证错误，FastAPI会自动处理并返回422
        # 这里只处理其他类型的错误
        raise HTTPException(status_code=500, detail=f"创建费用记录失败: {error_msg}")

@router.get("/trips/{trip_id}/expenses", response_model=ExpenseListResponse)
async def get_expenses(
    trip_id: str = Path(..., description="行程ID"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    category: Optional[str] = Query(None, description="费用类别"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取费用列表"""
    try:
        # 检查行程是否存在且属于当前用户
        trip = db.query(TripModel).filter(
            TripModel.id == trip_id,
            TripModel.user_id == current_user.id
        ).first()
        
        if not trip:
            raise HTTPException(status_code=404, detail="行程不存在")
        
        query = db.query(ExpenseModel).filter(ExpenseModel.trip_id == trip_id)
        
        # 筛选条件
        if category:
            query = query.filter(ExpenseModel.category == category)
        if start_date:
            query = query.filter(ExpenseModel.expense_date >= start_date)
        if end_date:
            query = query.filter(ExpenseModel.expense_date <= end_date)
        
        # 计算总金额
        total_amount = query.with_entities(func.sum(ExpenseModel.amount)).scalar() or 0
        
        # 分页
        total = query.count()
        expenses = query.order_by(desc(ExpenseModel.expense_date)).offset((page - 1) * size).limit(size).all()
        
        return ExpenseListResponse(
            expenses=expenses,
            total=total,
            page=page,
            size=size,
            has_next=(page * size) < total,
            total_amount=total_amount
        )
        
    except Exception as e:
        print(f"Get expenses error: {e}")
        raise HTTPException(status_code=500, detail=f"获取费用列表失败: {str(e)}")

@router.put("/expenses/{expense_id}", response_model=Expense)
async def update_expense(
    expense_id: str = Path(..., description="费用ID"),
    expense_data: ExpenseUpdate = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新费用记录"""
    try:
        # 检查费用是否存在且属于当前用户
        expense = db.query(ExpenseModel).join(TripModel).filter(
            ExpenseModel.id == expense_id,
            TripModel.user_id == current_user.id
        ).first()
        
        if not expense:
            raise HTTPException(status_code=404, detail="费用记录不存在")
        
        # 更新费用记录
        if expense_data.amount is not None:
            expense.amount = expense_data.amount
        if expense_data.currency is not None:
            expense.currency = expense_data.currency
        if expense_data.category is not None:
            expense.category = expense_data.category
        if expense_data.description is not None:
            expense.description = expense_data.description
        if expense_data.location is not None:
            expense.location = expense_data.location
        if expense_data.coordinates is not None:
            expense.coordinates = expense_data.coordinates.model_dump() if hasattr(expense_data.coordinates, 'model_dump') else expense_data.coordinates
        if expense_data.payment_method is not None:
            expense.payment_method = expense_data.payment_method
        if expense_data.receipt_image is not None:
            expense.receipt_image = expense_data.receipt_image
        if expense_data.is_shared is not None:
            expense.is_shared = expense_data.is_shared
        if hasattr(expense_data, 'shared_with') and expense_data.shared_with is not None:
            expense.shared_with = expense_data.shared_with
        if hasattr(expense_data, 'my_share') and expense_data.my_share is not None:
            expense.my_share = expense_data.my_share
        if expense_data.notes is not None:
            expense.notes = expense_data.notes
        if hasattr(expense_data, 'tags') and expense_data.tags is not None:
            expense.tags = expense_data.tags
        if expense_data.expense_date is not None:
            expense.expense_date = expense_data.expense_date
        # 更新关联节点ID（如果提供了该字段）
        # 使用model_dump(exclude_unset=True)获取实际更新的字段
        expense_update_dict = expense_data.model_dump(exclude_unset=True)
        if 'itinerary_item_id' in expense_update_dict:
            expense.itinerary_item_id = expense_data.itinerary_item_id
        
        expense.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(expense)
        return expense
        
    except Exception as e:
        db.rollback()
        print(f"Update expense error: {e}")
        raise HTTPException(status_code=500, detail=f"更新费用记录失败: {str(e)}")

@router.delete("/expenses/{expense_id}")
async def delete_expense(
    expense_id: str = Path(..., description="费用ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除费用记录"""
    try:
        # 检查费用是否存在且属于当前用户
        expense = db.query(ExpenseModel).join(TripModel).filter(
            ExpenseModel.id == expense_id,
            TripModel.user_id == current_user.id
        ).first()
        
        if not expense:
            raise HTTPException(status_code=404, detail="费用记录不存在")
        
        db.delete(expense)
        db.commit()
        
        return {"message": "费用记录删除成功"}
        
    except Exception as e:
        db.rollback()
        print(f"Delete expense error: {e}")
        raise HTTPException(status_code=500, detail=f"删除费用记录失败: {str(e)}")

# 费用统计
@router.get("/trips/{trip_id}/expenses/stats", response_model=ExpenseStats)
async def get_expense_stats(
    trip_id: str = Path(..., description="行程ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取费用统计"""
    try:
        # 检查行程是否存在且属于当前用户
        trip = db.query(TripModel).filter(
            TripModel.id == trip_id,
            TripModel.user_id == current_user.id
        ).first()
        
        if not trip:
            raise HTTPException(status_code=404, detail="行程不存在")
        
        # 总费用
        total_amount = db.query(func.sum(ExpenseModel.amount)).filter(
            ExpenseModel.trip_id == trip_id
        ).scalar() or 0
        
        # 按类别统计
        category_stats = db.query(
            ExpenseModel.category,
            func.sum(ExpenseModel.amount).label('amount')
        ).filter(ExpenseModel.trip_id == trip_id).group_by(ExpenseModel.category).all()
        
        # 费用天数 - 使用日期字符串提取，避免数据库兼容性问题
        expense_dates = db.query(ExpenseModel.expense_date).filter(
            ExpenseModel.trip_id == trip_id,
            ExpenseModel.expense_date.isnot(None)
        ).all()
        unique_dates = set()
        for date_obj in expense_dates:
            if date_obj:
                if isinstance(date_obj, datetime):
                    unique_dates.add(date_obj.date())
                else:
                    unique_dates.add(date_obj)
        expense_days = len(unique_dates)
        
        # 构建分类统计字典
        category_breakdown = {cat: float(amount) for cat, amount in category_stats}
        
        # 计算日均支出
        daily_average = total_amount / expense_days if expense_days > 0 else 0
        
        # 计算预算对比
        budget_vs_actual = {
            "budget": float(trip.budget_total) if trip.budget_total else 0,
            "actual": float(total_amount),
            "remaining": float(trip.budget_total - total_amount) if trip.budget_total else 0,
            "usage_percent": float((total_amount / trip.budget_total * 100)) if trip.budget_total and trip.budget_total > 0 else 0
        }
        
        # 月度趋势（简化版，返回空列表）
        monthly_trend = []
        
        return ExpenseStats(
            total_amount=float(total_amount),
            category_breakdown=category_breakdown,
            daily_average=float(daily_average),
            monthly_trend=monthly_trend,
            budget_vs_actual=budget_vs_actual
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Get expense stats error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取费用统计失败: {str(e)}")
