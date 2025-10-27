"""
费用管理API端点
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import uuid
from pydantic import BaseModel, Field

from ....core.database import get_db
from ...deps import get_current_user
from ....models.user import User
from ....models.trip import Expense, Budget, Trip
from ....schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseResponse, BudgetResponse
from ....schemas.trip import ExpenseListResponse
from ....services.expense_service import ExpenseService
from ....services.expense_ai_service import ExpenseAIService

router = APIRouter()

@router.get("/", response_model=ExpenseListResponse)
async def get_expenses(
    trip_id: Optional[str] = Query(None, description="行程ID"),
    category: Optional[str] = Query(None, description="费用分类"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(100, ge=1, le=1000, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取费用列表"""
    service = ExpenseService(db)
    skip = (page - 1) * size
    expenses = await service.get_expenses(
        user_id=current_user.id,
        trip_id=trip_id,
        category=category,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=size
    )
    
    # 计算总金额
    total_amount = sum(expense.amount for expense in expenses)
    
    # 计算总数（这里简化处理，实际应该查询总数）
    total = len(expenses)
    
    return ExpenseListResponse(
        expenses=expenses,
        total=total,
        page=page,
        size=size,
        has_next=(page * size) < total,
        total_amount=total_amount
    )

@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个费用详情"""
    service = ExpenseService(db)
    expense = await service.get_expense(expense_id, current_user.id)
    if not expense:
        raise HTTPException(status_code=404, detail="费用不存在")
    return expense

@router.post("/", response_model=ExpenseResponse)
async def create_expense(
    expense_data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建费用记录"""
    service = ExpenseService(db)
    
    # 验证行程是否属于当前用户
    trip = db.query(Trip).filter(
        Trip.id == expense_data.trip_id,
        Trip.user_id == current_user.id
    ).first()
    if not trip:
        raise HTTPException(status_code=404, detail="行程不存在")
    
    expense = await service.create_expense(expense_data, current_user.id)
    return expense

@router.put("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: str,
    expense_data: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新费用记录"""
    service = ExpenseService(db)
    expense = await service.update_expense(expense_id, expense_data, current_user.id)
    if not expense:
        raise HTTPException(status_code=404, detail="费用不存在")
    return expense

@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除费用记录"""
    service = ExpenseService(db)
    success = await service.delete_expense(expense_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="费用不存在")
    return {"message": "费用删除成功"}

@router.get("/stats/summary")
async def get_expense_summary(
    trip_id: Optional[str] = Query(None, description="行程ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取费用统计摘要"""
    service = ExpenseService(db)
    summary = await service.get_expense_summary(
        user_id=current_user.id,
        trip_id=trip_id,
        start_date=start_date,
        end_date=end_date
    )
    return summary

@router.get("/categories/stats")
async def get_category_stats(
    trip_id: Optional[str] = Query(None, description="行程ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取费用分类统计"""
    service = ExpenseService(db)
    stats = await service.get_category_stats(
        user_id=current_user.id,
        trip_id=trip_id,
        start_date=start_date,
        end_date=end_date
    )
    return stats


# AI查询相关模型
class AIQueryRequest(BaseModel):
    """AI查询请求模型"""
    query: str = Field(..., description="用户查询")
    trip_id: Optional[str] = Field(None, description="行程ID")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")


class AIQueryResponse(BaseModel):
    """AI查询响应模型"""
    response: str = Field(..., description="AI响应")
    action_performed: bool = Field(False, description="是否执行了操作")


@router.post("/ai/query", response_model=AIQueryResponse)
async def ai_query(
    request: AIQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI费用管理查询"""
    service = ExpenseAIService(db)
    
    try:
        response = await service.process_natural_language_query(
            query=request.query,
            user_id=current_user.id,
            trip_id=request.trip_id,
            context=request.context
        )
        
        # 检查是否执行了操作（简单判断）
        action_performed = any(keyword in response.lower() for keyword in [
            '已添加', '已更新', '已删除', '已创建', '已修改'
        ])
        
        return AIQueryResponse(
            response=response,
            action_performed=action_performed
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI查询失败: {str(e)}")
