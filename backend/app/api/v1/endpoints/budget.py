"""
费用管理API端点
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func
from typing import List, Optional
from datetime import datetime, timedelta

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.trip import Trip as TripModel, Budget as BudgetModel, Expense as ExpenseModel
from app.schemas.trip import (
    BudgetCreate, BudgetUpdate, Budget,
    ExpenseCreate, ExpenseUpdate, Expense, ExpenseListResponse,
    ExpenseStats
)

router = APIRouter()

# 预算管理
@router.post("/trips/{trip_id}/budgets", response_model=Budget)
async def create_budget(
    trip_id: str = Path(..., description="行程ID"),
    budget_data: BudgetCreate = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建预算"""
    try:
        # 检查行程是否存在且属于当前用户
        trip = db.query(TripModel).filter(
            TripModel.id == trip_id,
            TripModel.user_id == current_user.id
        ).first()
        
        if not trip:
            raise HTTPException(status_code=404, detail="行程不存在")
        
        # 创建预算
        budget = BudgetModel(
            trip_id=trip_id,
            total_budget=budget_data.total_budget,
            currency=budget_data.currency,
            categories=budget_data.categories or {},
            is_active=budget_data.is_active
        )
        
        db.add(budget)
        db.commit()
        db.refresh(budget)
        return budget
        
    except Exception as e:
        db.rollback()
        print(f"Create budget error: {e}")
        raise HTTPException(status_code=500, detail=f"创建预算失败: {str(e)}")

@router.get("/trips/{trip_id}/budgets", response_model=List[Budget])
async def get_budgets(
    trip_id: str = Path(..., description="行程ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取预算列表"""
    try:
        # 检查行程是否存在且属于当前用户
        trip = db.query(TripModel).filter(
            TripModel.id == trip_id,
            TripModel.user_id == current_user.id
        ).first()
        
        if not trip:
            raise HTTPException(status_code=404, detail="行程不存在")
        
        budgets = db.query(BudgetModel).filter(
            BudgetModel.trip_id == trip_id
        ).order_by(desc(BudgetModel.created_at)).all()
        
        return budgets
        
    except Exception as e:
        print(f"Get budgets error: {e}")
        raise HTTPException(status_code=500, detail=f"获取预算列表失败: {str(e)}")

@router.put("/budgets/{budget_id}", response_model=Budget)
async def update_budget(
    budget_id: str = Path(..., description="预算ID"),
    budget_data: BudgetUpdate = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新预算"""
    try:
        # 检查预算是否存在且属于当前用户
        budget = db.query(BudgetModel).join(TripModel).filter(
            BudgetModel.id == budget_id,
            TripModel.user_id == current_user.id
        ).first()
        
        if not budget:
            raise HTTPException(status_code=404, detail="预算不存在")
        
        # 更新预算
        if budget_data.total_budget is not None:
            budget.total_budget = budget_data.total_budget
        if budget_data.currency is not None:
            budget.currency = budget_data.currency
        if budget_data.categories is not None:
            budget.categories = budget_data.categories
        if budget_data.is_active is not None:
            budget.is_active = budget_data.is_active
        
        budget.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(budget)
        return budget
        
    except Exception as e:
        db.rollback()
        print(f"Update budget error: {e}")
        raise HTTPException(status_code=500, detail=f"更新预算失败: {str(e)}")

@router.delete("/budgets/{budget_id}")
async def delete_budget(
    budget_id: str = Path(..., description="预算ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除预算"""
    try:
        # 检查预算是否存在且属于当前用户
        budget = db.query(BudgetModel).join(TripModel).filter(
            BudgetModel.id == budget_id,
            TripModel.user_id == current_user.id
        ).first()
        
        if not budget:
            raise HTTPException(status_code=404, detail="预算不存在")
        
        db.delete(budget)
        db.commit()
        
        return {"message": "预算删除成功"}
        
    except Exception as e:
        db.rollback()
        print(f"Delete budget error: {e}")
        raise HTTPException(status_code=500, detail=f"删除预算失败: {str(e)}")

# 费用管理
@router.post("/trips/{trip_id}/expenses", response_model=Expense)
async def create_expense(
    trip_id: str = Path(..., description="行程ID"),
    expense_data: ExpenseCreate = None,
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
        
        # 创建费用记录
        expense = ExpenseModel(
            trip_id=trip_id,
            amount=expense_data.amount,
            currency=expense_data.currency,
            category=expense_data.category,
            description=expense_data.description,
            location=expense_data.location,
            coordinates=expense_data.coordinates,
            payment_method=expense_data.payment_method,
            receipt_image=expense_data.receipt_image,
            is_shared=expense_data.is_shared,
            shared_amount=expense_data.shared_amount,
            notes=expense_data.notes,
            expense_date=expense_data.expense_date or datetime.utcnow()
        )
        
        db.add(expense)
        db.commit()
        db.refresh(expense)
        return expense
        
    except Exception as e:
        db.rollback()
        print(f"Create expense error: {e}")
        raise HTTPException(status_code=500, detail=f"创建费用记录失败: {str(e)}")

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
            expense.coordinates = expense_data.coordinates
        if expense_data.payment_method is not None:
            expense.payment_method = expense_data.payment_method
        if expense_data.receipt_image is not None:
            expense.receipt_image = expense_data.receipt_image
        if expense_data.is_shared is not None:
            expense.is_shared = expense_data.is_shared
        if expense_data.shared_amount is not None:
            expense.shared_amount = expense_data.shared_amount
        if expense_data.notes is not None:
            expense.notes = expense_data.notes
        if expense_data.expense_date is not None:
            expense.expense_date = expense_data.expense_date
        
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
        
        # 费用天数
        expense_days = db.query(func.count(func.distinct(func.date(ExpenseModel.expense_date)))).filter(
            ExpenseModel.trip_id == trip_id
        ).scalar() or 0
        
        return ExpenseStats(
            total_amount=total_amount,
            category_stats=[{"category": cat, "amount": amount} for cat, amount in category_stats],
            expense_days=expense_days
        )
        
    except Exception as e:
        print(f"Get expense stats error: {e}")
        raise HTTPException(status_code=500, detail=f"获取费用统计失败: {str(e)}")
